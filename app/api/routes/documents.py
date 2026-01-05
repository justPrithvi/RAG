"""
Documents Routes - SKELETON
Similar to a DocumentsController in NestJS
Handles API endpoints for RAG operations
"""
from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from app.models.document import DocumentUploadResponse, QueryRequest, QueryResponse
from app.services.document_service import DocumentService
from app.utils.text_cleaner import TextCleaner
from pypdf import PdfReader
import io

# Create router (like @Controller('documents') in NestJS)
router = APIRouter()

# Service instance
# In NestJS, this would be injected via constructor
# In FastAPI, you can use Depends() for dependency injection
document_service = DocumentService()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    documentId: str = Form(...)
):
    """
    Upload a file and read its content
    
    Form fields:
    - file: The file to upload
    - documentId: The original document ID from your main DB
    
    Supports: PDF, TXT, and other text-based files
    Image and video support will be added later
    
    The text is automatically cleaned and ready for chunking.
    
    Similar to @Post('upload') @UseInterceptors(FileInterceptor('file')) in NestJS
    """
    # Store in snake_case for Python convention
    document_id = documentId
    # Get file extension
    filename = file.filename or ""
    file_extension = filename.split(".")[-1].lower() if "." in filename else ""
    
    # Block image and video files for now
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
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Extract text based on file type
        raw_text = ""
        
        if file_extension == "pdf":
            # Parse PDF
            try:
                pdf_file = io.BytesIO(content)
                pdf_reader = PdfReader(pdf_file)
                
                # Extract text from all pages
                raw_text = ""
                for page in pdf_reader.pages:
                    raw_text += page.extract_text() + "\n"
                
                if not raw_text.strip():
                    raise HTTPException(
                        status_code=400,
                        detail="PDF appears to be empty or text could not be extracted (might be image-based PDF)"
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error parsing PDF: {str(e)}"
                )
        
        elif file_extension in ["txt", "md", "csv", "json", "xml"]:
            # Plain text files
            try:
                raw_text = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    raw_text = content.decode('latin-1')
                except Exception:
                    raise HTTPException(
                        status_code=400,
                        detail="Unable to decode text file. Please ensure it's in UTF-8 or Latin-1 encoding."
                    )
        
        else:
            # Try to decode as text
            try:
                raw_text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: .{file_extension}. Supported types: PDF, TXT, MD, CSV"
                )
        
        # Clean the text for chunking
        cleaned_text = TextCleaner.clean_for_chunking(raw_text)
        
        if not cleaned_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text content found in the file after processing"
            )
        
        return {
            "message": "File uploaded and processed successfully",
            "document_id": document_id,
            "filename": filename,
            "file_size": file_size,
            "file_extension": file_extension,
            "content_type": file.content_type,
            "raw_content_length": len(raw_text),
            "cleaned_content_length": len(cleaned_text),
            "content_preview": cleaned_text[:500] + "..." if len(cleaned_text) > 500 else cleaned_text,
            "cleaned_content": cleaned_text,
            "ready_for_chunking": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing file: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse)
async def query_documents(query: QueryRequest):
    """
    Query documents using RAG
    
    Flow:
    1. User asks a question
    2. Convert question to embedding
    3. Search vector DB for similar chunks
    4. Return relevant chunks (and optionally LLM-generated answer)
    
    Similar to @Post('query') in NestJS
    
    Example request body:
    {
        "question": "What is the company's revenue?",
        "max_results": 5
    }
    """
    try:
        result = await document_service.query_documents(
            question=query.question,
            max_results=query.max_results or 5
        )
        
        return {
            "query": query.question,
            "answer": result.get("answer", ""),
            "sources": result.get("results", [])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and all its chunks
    
    Similar to @Delete(':id') in NestJS
    """
    try:
        await document_service.delete_document(document_id)
        return {
            "message": "Document deleted successfully",
            "document_id": document_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def rag_health():
    """
    Check if RAG service components are healthy
    Useful for monitoring
    """
    return {
        "status": "healthy",
        "components": {
            "chunker": "ready",
            "embedder": "ready",
            "vector_store": "ready"
        }
    }

