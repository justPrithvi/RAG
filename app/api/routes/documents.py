"""
Documents Routes
Handles document upload and processing for RAG
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, get_current_user
from app.services.document_access import parse_document_id, require_document_access
from sqlalchemy import text
from sqlalchemy.orm import Session
from pypdf import PdfReader
import io
import json

from app.services.embedding_service import embedding_service
from app.services.filemaster_client import filemaster_client
from app.services.ingestion_service import ingest_document
from app.models.db_models import DocumentChunk, DocumentChatMessage
from app.database import get_db
from app.utils.text_cleaner import TextCleaner
from app.utils.chunking import TextChunker

router = APIRouter()
text_chunker = TextChunker(chunk_size=1000, chunk_overlap=200)


class IngestRequest(BaseModel):
    """Body for POST /api/documents/ingest. Only the document id; any userId sent is ignored."""
    documentId: int = Field(..., gt=0)


@router.post("/ingest", status_code=202)
async def ingest(
    body: IngestRequest,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(get_current_user),
):
    """
    Index a document already stored by the Java document service (FileMaster).

    Called by the UI right after a successful upload, with only the document id.
    1. AuthMiddleware has already validated the Bearer token with Nest.
    2. The user id comes from Nest, never from the request body.
    3. A background job fetches the file from FileMaster
       (GET /internal/documents/{id}/file with X-Service-Key + X-User-Id).
       FileMaster returns 404 unless this user owns the document.
    4. The file is parsed, chunked, embedded and stored; re-ingesting replaces old chunks.
    """
    user_id = user.id

    if not filemaster_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Document ingestion is not configured (INTERNAL_SERVICE_KEY missing)",
        )

    background_tasks.add_task(ingest_document, body.documentId, user_id)

    return {"documentId": body.documentId, "status": "queued"}


async def process_document_chunks(document_id: str, cleaned_text: str, db: Session):
    """Background task to chunk, embed, and store document"""
    try:
        chunks = await text_chunker.chunk_text_token_based(cleaned_text)
        embeddings = await embedding_service.generate_embeddings(chunks)
        
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=chunk_text,
                embedding=embedding,
                chunk_metadata=json.dumps({
                    "chunk_size": len(chunk_text),
                    "position": i,
                    "total_chunks": len(chunks)
                })
            )
            db.add(db_chunk)
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    documentId: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    LEGACY: the UI no longer calls this; it uses POST /ingest (file fetched from FileMaster).

    Upload and process a document

    Form fields:
    - file: The file to upload
    - documentId: Original document ID from main database

    Supports: PDF, TXT, MD, CSV, JSON, XML
    Processing happens in background: chunking, embedding, storage
    """
    require_document_access(db, documentId, user)
    document_id = documentId
    filename = file.filename or ""
    file_extension = filename.split(".")[-1].lower() if "." in filename else ""
    
    image_extensions = {"jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "ico"}
    video_extensions = {"mp4", "avi", "mov", "wmv", "flv", "mkv", "webm"}
    
    if file_extension in image_extensions:
        raise HTTPException(
            status_code=400,
            detail="Image files are not supported yet. Coming soon!"
        )
    
    if file_extension in video_extensions:
        raise HTTPException(
            status_code=400,
            detail="Video files are not supported yet. Coming soon!"
        )
    
    try:
        content = await file.read()
        file_size = len(content)
        raw_text = ""
        
        if file_extension == "pdf":
            try:
                pdf_file = io.BytesIO(content)
                pdf_reader = PdfReader(pdf_file)
                
                for page in pdf_reader.pages:
                    raw_text += page.extract_text() + "\n"
                
                if not raw_text.strip():
                    raise HTTPException(
                        status_code=400,
                        detail="PDF appears to be empty or text could not be extracted"
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error parsing PDF: {str(e)}"
                )
        
        elif file_extension in ["txt", "md", "csv", "json", "xml"]:
            try:
                raw_text = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    raw_text = content.decode('latin-1')
                except Exception:
                    raise HTTPException(
                        status_code=400,
                        detail="Unable to decode text file"
                    )
        else:
            try:
                raw_text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: .{file_extension}"
                )
        
        cleaned_text = TextCleaner.clean_for_chunking(raw_text)
        
        if not cleaned_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text content found in the file"
            )
        
        background_tasks.add_task(
            process_document_chunks,
            document_id,
            cleaned_text,
            db
        )
        
        return {
            "message": "File uploaded successfully, processing in background",
            "document_id": document_id,
            "filename": filename,
            "file_size": file_size,
            "file_extension": file_extension,
            "content_type": file.content_type,
            "raw_content_length": len(raw_text),
            "cleaned_content_length": len(cleaned_text),
            "content_preview": cleaned_text[:500] + "..." if len(cleaned_text) > 500 else cleaned_text,
            "status": "processing",
            "estimated_chunks": text_chunker.get_chunk_count(cleaned_text)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove everything RAG holds for a document: its chunks and its document-chat messages.

    Called by the UI right after FileMaster's DELETE /api/documents/{id} succeeds.
    - If the documents row still exists, the caller must own it (or be an admin), else 404.
    - If the row is already gone (the normal case, since FileMaster deleted it), the leftover
      RAG rows are orphans that nobody can reach (chat requires the row), so any
      authenticated user may clear them. Idempotent: safe to call again.
    """
    doc_id = parse_document_id(document_id)
    try:
        owner_id = db.execute(
            text("SELECT user_id FROM documents WHERE id = :id"), {"id": doc_id}
        ).scalar()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=503, detail="Could not verify document access")
    if owner_id is not None and owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        key = str(doc_id)
        chunks_deleted = db.query(DocumentChunk)\
            .filter(DocumentChunk.document_id == key)\
            .delete(synchronize_session=False)
        chats_deleted = db.query(DocumentChatMessage)\
            .filter(DocumentChatMessage.document_id == key)\
            .delete(synchronize_session=False)
        db.commit()

        return {
            "message": "Document data deleted",
            "document_id": key,
            "chunks_deleted": chunks_deleted,
            "chat_messages_deleted": chats_deleted,
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )


@router.get("/health")
async def rag_health():
    """Check RAG service health"""
    return {
        "status": "healthy",
        "components": {
            "chunker": "ready",
            "embedder": "ready",
            "vector_store": "ready"
        }
    }
