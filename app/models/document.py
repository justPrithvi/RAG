"""
Document models
Similar to DTOs in NestJS (using class-validator and class-transformer)
Pydantic models provide validation and serialization
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    message: str
    document_id: str
    chunks_created: int


class QueryRequest(BaseModel):
    """Request model for querying documents"""
    question: str = Field(..., min_length=1, description="The question to ask")
    max_results: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of results")


class QueryResponse(BaseModel):
    """Response model for query results"""
    query: str
    answer: str
    sources: List[dict]


class DocumentChunk(BaseModel):
    """Model for a document chunk"""
    chunk_id: str
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Optional[dict] = None

