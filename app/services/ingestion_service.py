"""
Ingestion Service
Pulls a stored document from FileMaster and indexes it for RAG:
fetch file -> extract text -> clean -> chunk -> embed -> replace chunks in document_chunks.

Runs as a background task after POST /api/documents/ingest returns 202.
"""
import json
import logging
from typing import List

from pypdf import PdfReader
from sqlalchemy import text

from app.config import settings
from app.database import SessionLocal
from app.models.db_models import DocumentChunk
from app.services.embedding_service import embedding_service
from app.services.filemaster_client import FetchedFile, FileMasterError, filemaster_client
from app.utils.chunking import TextChunker
from app.utils.text_cleaner import TextCleaner

logger = logging.getLogger("rag.ingestion")

text_chunker = TextChunker(chunk_size=1000, chunk_overlap=200)

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "ico", "heic"}
VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "wmv", "flv", "mkv", "webm"}
TEXT_EXTENSIONS = {"txt", "md", "csv", "json", "xml"}


class UnsupportedDocument(Exception):
    """File type can't be turned into text (images, video, binary)."""


def extract_text(fetched: FetchedFile) -> str:
    """Extract raw text from a downloaded file. Raises UnsupportedDocument if not possible."""
    ext = fetched.extension

    if ext in IMAGE_EXTENSIONS or fetched.content_type.startswith("image/"):
        raise UnsupportedDocument("Image files are not supported yet")
    if ext in VIDEO_EXTENSIONS or fetched.content_type.startswith("video/"):
        raise UnsupportedDocument("Video files are not supported yet")

    if ext == "pdf" or fetched.content_type == "application/pdf":
        reader = PdfReader(fetched.path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    with open(fetched.path, "rb") as f:
        content = f.read()

    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        if ext in TEXT_EXTENSIONS:
            return content.decode("latin-1")
        raise UnsupportedDocument(f"Unsupported file type: .{ext or 'unknown'}")


async def _embed_in_batches(chunks: List[str]) -> List[List[float]]:
    batch_size = max(1, settings.EMBEDDING_BATCH_SIZE)
    embeddings: List[List[float]] = []
    for start in range(0, len(chunks), batch_size):
        embeddings.extend(await embedding_service.generate_embeddings(chunks[start:start + batch_size]))
    return embeddings


async def ingest_document(document_id: int, user_id: int) -> None:
    """
    Background job. Never raises: every failure is logged with the document and user id.
    Idempotent: re-ingesting a document replaces its existing chunks.
    """
    log_ctx = f"document={document_id} user={user_id}"
    fetched = None
    try:
        logger.info("Ingestion started %s", log_ctx)

        fetched = await filemaster_client.fetch_document_file(document_id, user_id)
        logger.info(
            "Fetched %s name=%r type=%s size=%d",
            log_ctx, fetched.file_name, fetched.content_type, fetched.size,
        )

        raw_text = extract_text(fetched)
        cleaned_text = TextCleaner.clean_for_chunking(raw_text)
        if not cleaned_text.strip():
            logger.warning("No text content found, nothing indexed %s", log_ctx)
            return

        chunks = await text_chunker.chunk_text_token_based(cleaned_text)
        if not chunks:
            logger.warning("Chunker produced no chunks %s", log_ctx)
            return

        embeddings = await _embed_in_batches(chunks)
        if len(embeddings) != len(chunks):
            raise ValueError(f"Got {len(embeddings)} embeddings for {len(chunks)} chunks")

        if not _replace_chunks(document_id, user_id, fetched.file_name, chunks, embeddings):
            logger.warning("Document deleted during ingestion, chunks discarded %s", log_ctx)
            return
        logger.info("Ingestion finished %s chunks=%d", log_ctx, len(chunks))

    except UnsupportedDocument as e:
        logger.warning("Skipped %s: %s", log_ctx, e)
    except FileMasterError as e:
        logger.error("Ingestion failed fetching file %s: %s: %s", log_ctx, type(e).__name__, e)
    except Exception:
        logger.exception("Ingestion failed %s", log_ctx)
    finally:
        if fetched is not None:
            fetched.cleanup()


def _replace_chunks(
    document_id: int,
    user_id: int,
    file_name: str,
    chunks: List[str],
    embeddings: List[List[float]],
) -> bool:
    """
    Delete old chunks for the document and insert the new ones in one transaction.

    The documents row is locked FOR SHARE first, so a FileMaster delete can't happen
    mid-write. If the row is already gone (document deleted while we were embedding),
    nothing is written and False is returned, so no orphan chunks are left behind.
    """
    db = SessionLocal()
    try:
        exists = db.execute(
            text("SELECT 1 FROM documents WHERE id = :id FOR SHARE"), {"id": int(document_id)}
        ).scalar()
        if not exists:
            db.rollback()
            return False
        document_id = str(document_id)
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            db.add(DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=chunk_text,
                embedding=embedding,
                chunk_metadata=json.dumps({
                    "user_id": user_id,
                    "file_name": file_name,
                    "chunk_size": len(chunk_text),
                    "position": i,
                    "total_chunks": len(chunks),
                }),
            ))
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
