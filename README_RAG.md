# Python RAG Backend & Chat Pipeline Guide

This guide details the internal architecture, database schema, codebase structure, and complete workflow pipelines of the **Python RAG Microservice** located in the `RAG/` directory.

---

## 🏗️ Codebase Structure

The Python microservice is built using **FastAPI** (running on port `8000`). It uses **SQLAlchemy** for database operations, **pgvector** for similarity searches, and **Ollama** for local embeddings and LLM execution.

```bash
RAG/
├── requirements.txt               # Python package dependencies
├── start.sh                       # Quick launch shell script
├── app/
│   ├── main.py                    # Application entrypoint & middleware registration
│   ├── config.py                  # Pydantic Settings (manages env vars & constants)
│   ├── database.py                # PostgreSQL DB setup and Session injection helper
│   │
│   ├── api/routes/                # Route Controllers (API endpoints)
│   │   ├── health.py              # Health check status
│   │   ├── documents.py           # Document uploads, processing & deletion
│   │   └── chat.py                # General chat & RAG-based document chat routes
│   │
│   ├── middleware/
│   │   └── auth.py                # Intercepts Bearer tokens & calls NestJS to authenticate
│   │
│   ├── models/
│   │   ├── chat.py                # Pydantic schemas (Request/Response validation)
│   │   └── db_models.py           # SQLAlchemy database tables
│   │
│   ├── services/
│   │   ├── embedding_service.py   # Ollama interface for vector generation
│   │   ├── llm_service.py         # Ollama interface for conversational LLM
│   │   └── vector_search_service.py # Core similarity matching queries using pgvector
│   │
│   └── utils/
│       ├── chunking.py            # Sentence & token-based text partitioner
│       └── text_cleaner.py        # PDF noise remover and whitespace normalizer
```

---

## 🗄️ Database Schema (PostgreSQL with pgvector)

The service shares the PostgreSQL server with NestJS but manages its own RAG tables. It requires the `vector` extension to be enabled in PostgreSQL.

### Core Tables (`RAG/app/models/db_models.py`):
1. **`document_chunks`**: Stores the chunked texts and their vectors.
2. **`conversations` & `messages`**: Stores threads and logs for general chat queries.
3. **`document_chat_messages`**: Stores question-and-answer pairs for document-specific RAG conversations.

```sql
-- Enables vector operations in Postgres
CREATE EXTENSION IF NOT EXISTS vector;

-- Document chunks and vector embeddings
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR NOT NULL,               -- Foreign ID mapping to NestJS document.id
    chunk_index INTEGER NOT NULL,               -- Sequential position (0, 1, 2...)
    content TEXT NOT NULL,                      -- Actual text block
    embedding vector(768) NOT NULL,             -- nomic-embed-text 768D vector
    chunk_metadata TEXT,                        -- JSON string of stats (size, total chunks)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indices for performance
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

---

## 📥 Document Upload & Processing Pipeline

### "Do we send the document immediately or wait until chat start?"
**Yes, we send the document immediately upon upload.** Text extraction, paragraph chunking, vector embedding, and database storage are performed asynchronously *at upload time*. This ensures that when a user starts a chat, the search indices are already prepared.

### Execution Flow:
```
[User Uploads File]
       │
       ▼
1. Next.js Client ──(POST /documents/upload)──► 2. NestJS Backend (port 5001)
                                                 • Saves file to disk (./uploads)
                                                 • Creates catalog entry in SQL
                                                 • Returns { id: documentId }
                                                           │
                                                           ▼
4. Python Service (POST /api/documents/upload) ◄─── 3. Next.js Client
   • Extracts raw text (PdfReader / text decoder)
   • Sanitizes noise via TextCleaner
   • Responds with 202 ("processing")
   • Hands workload off to FastAPI BackgroundTasks thread
       │
       ├─────────────────────────────────────────┐
       ▼ (Asynchronous Background Thread)         ▼
5. Chunk Text (TextChunker)             6. Generate Embeddings (EmbeddingService)
   • Splitting with 1000 char size        • Sends chunks to Ollama API
   • 200 char overlap window              • Uses nomic-embed-text (768 Dimensions)
       │                                         │
       └───────────────────┬─────────────────────┘
                           ▼
                 7. Save to PostgreSQL
                    • Appends records to document_chunks table
```

---

## 💬 Chat Pipeline Execution Flow

The service has two parallel chat pipelines: **General Chat** and **Document-Specific Chat (RAG)**. Both routes are secure and authenticate incoming headers against the NestJS backend.

### 1. General Chat Pipeline (`POST /api/chat`)
* Used for general queries.
* **Process:**
  1. Retrieves the last $N$ (configured by `MAX_CONTEXT_MESSAGES`) messages from the `messages` table for conversation history.
  2. Constructs a message stack prefixed with a system prompt.
  3. Queries Ollama `/api/chat` using the configured LLM model (e.g., `llama3`).
  4. Appends user and assistant messages to the DB and returns the response.

### 2. Document-Specific Chat / RAG Pipeline (`POST /api/chat/document`)
* Used to ask questions about a specific document.
* **Process:**

```
                  [User sends message + documentId]
                                 │
                                 ▼
                     1. Embed User's Message
                        • Calls Ollama nomic-embed-text
                        • Generates 768D vector query
                                 │
                                 ▼
                     2. Similarity Search (Postgres)
                        • Performs cosine distance search:
                          "ORDER BY embedding <=> :query_embedding"
                        • Constraints: document_id matches AND
                          similarity score >= 0.3 threshold
                                 │
                                 ▼
                     3. Context Aggregator
                        • Takes top relevant chunks (up to 10)
                        • Joins content strings with dividers
                                 │
                                 ▼
                     4. LLM Generation (Ollama)
                        • Prompt context + user question is dispatched
                          to the LLM (e.g. llama3)
                                 │
                                 ▼
                     5. Log Response & Return
                        • Saves QA log in document_chat_messages
                        • Returns answer text & matching excerpt metadata
```

---

## 🛠️ Setting Up and Running the Python Service

### Prerequisites
- Python 3.9+
- Local PostgreSQL instance running (with database `data_vault` matching NestJS config)
- **Ollama** installed locally (`ollama serve`)

### Step-by-Step Setup
1. **Pull embedding and LLM models locally:**
   ```bash
   ollama pull nomic-embed-text
   ollama pull llama3  # or whichever model is set in config
   ```
2. **Setup virtual environment:**
   ```bash
   cd RAG
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install packages:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configuration Check:** Make sure PostgreSQL settings in your `.env` or system variables match the PostgreSQL database config.
5. **Run the service:**
   ```bash
   # Development reload mode
   uvicorn app.main:app --reload --port 8000
   
   # Or via the start script
   chmod +x start.sh
   ./start.sh
   ```
6. Visit `http://localhost:8000/docs` in your browser to view the interactive API swagger documentation.
