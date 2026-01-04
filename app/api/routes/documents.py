"""
Documents Routes - SKELETON
Similar to a DocumentsController in NestJS
Handles API endpoints for RAG operations
"""
from fastapi import APIRouter, HTTPException, Body
from app.models.document import DocumentUploadResponse, QueryRequest, QueryResponse
from app.services.document_service import DocumentService

# Create router (like @Controller('documents') in NestJS)
router = APIRouter()

# Service instance
# In NestJS, this would be injected via constructor
# In FastAPI, you can use Depends() for dependency injection
document_service = DocumentService()


@router.post("/process", response_model=DocumentUploadResponse)
async def process_document(
    document_id: str = Body(..., description="Document ID from main app"),
    text: str = Body(..., description="Extracted text from document"),
    metadata: dict = Body(None, description="Optional metadata")
):
    """
    Process document text sent from main app
    
    Flow:
    1. Main app (React + NestJS) handles file upload
    2. Main app extracts text from file
    3. Main app sends text here for RAG processing
    4. This service chunks, embeds, and stores
    
    Similar to @Post('process') in NestJS
    
    Example request body:
    {
        "document_id": "doc_123",
        "text": "This is the extracted text from the PDF...",
        "metadata": {
            "filename": "report.pdf",
            "user_id": "user_456",
            "upload_date": "2024-01-04"
        }
    }
    """
    try:
        result = await document_service.process_document(
            text=text,
            document_id=document_id,
            metadata=metadata
        )
        
        return {
            "message": "Document processed successfully",
            "document_id": result["document_id"],
            "chunks_created": result["chunks_created"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

