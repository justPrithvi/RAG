# Document Processing Flow

## Overview
This document explains how files are uploaded, chunked, embedded, and stored for RAG (Retrieval Augmented Generation).

## Flow

### 1. File Upload (`POST /api/documents/upload`)
**Request:**
- `file`: The PDF/text file (multipart/form-data)
- `documentId`: The document ID from your main NestJS database

**Process:**
1. ✅ **Immediate Response** - File is read and text is extracted
2. 🔄 **Background Processing** - Chunking, embedding, and storage happens asynchronously

**Response:**
```json
{
  "message": "File uploaded successfully, processing in background",
  "document_id": "123",
  "filename": "document.pdf",
  "status": "processing",
  "estimated_chunks": 5,
  "content_preview": "First 500 chars..."
}
```

### 2. Background Processing

The background task performs these steps:

#### Step 1: Chunking
- Uses `TextChunker` with 1000 character chunks and 200 character overlap
- Smart chunking: Respects paragraph and sentence boundaries
- Example: A 5000 character document → ~5-6 chunks

#### Step 2: Embedding
- Uses Ollama's `nomic-embed-text` model (running locally)
- Generates 768-dimensional vectors for each chunk
- Batch processing for efficiency

#### Step 3: Database Storage
- Saves to `document_chunks` table in PostgreSQL
- Each chunk includes:
  - `document_id`: Links to your main app's document
  - `chunk_index`: Position in the document (0, 1, 2, ...)
  - `content`: The actual text chunk
  - `embedding`: 768-dimensional vector (pgvector)
  - `chunk_metadata`: JSON with chunk size, position, total chunks

## Database Schema

```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768) NOT NULL,  -- nomic-embed-text produces 768D vectors
    chunk_metadata TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

## Configuration

In `app/config.py`:
```python
OLLAMA_BASE_URL: str = "http://localhost:11434"
EMBEDDING_MODEL: str = "nomic-embed-text"
EMBEDDING_DIMENSIONS: int = 768
```

## Key Components

### 1. `TextCleaner` (`app/utils/text_cleaner.py`)
- Removes PDF artifacts
- Normalizes whitespace
- Cleans special characters

### 2. `TextChunker` (`app/utils/chunking.py`)
- Paragraph-aware chunking
- Sentence boundary detection
- Configurable overlap for context preservation

### 3. `EmbeddingService` (`app/services/embedding_service.py`)
- Communicates with Ollama API
- Batch embedding generation
- Dimension validation

### 4. `DocumentChunk` Model (`app/models/db_models.py`)
- SQLAlchemy ORM model
- pgvector integration for embeddings
- Automatic timestamp management

## Why Background Processing?

**Problem:** Chunking and embedding can take 10-30 seconds for large documents
**Solution:** FastAPI's `BackgroundTasks` runs the heavy work in a separate thread

**Benefits:**
- ✅ API responds immediately (~1-2 seconds)
- ✅ User doesn't wait for processing
- ✅ Main thread stays responsive for other requests
- ✅ Processing happens on background thread pool

## Testing

### Upload a document:
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@document.pdf" \
  -F "documentId=123"
```

### Check database:
```sql
-- See all chunks for a document
SELECT 
    chunk_index, 
    LEFT(content, 100) as preview,
    array_length(embedding::float[], 1) as embedding_dims
FROM document_chunks 
WHERE document_id = '123'
ORDER BY chunk_index;
```

## Next Steps (RAG)

Once chunks are stored, you can:
1. Convert user questions to embeddings
2. Search for similar chunks using vector similarity
3. Send relevant chunks + question to LLM
4. Return AI-generated answer based on document context

This is the foundation for document-based chat! 🚀
