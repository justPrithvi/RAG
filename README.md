# RAG Backend Service - LEARNING SKELETON 🎓

A Python backend service for RAG (Retrieval Augmented Generation). This is a **learning skeleton** to help you understand Python/FastAPI project structure coming from a JavaScript/NestJS background.

## 🎯 What This Service Does

Your main app (React + NestJS) handles file uploads. This Python service receives text and:
1. **Chunks** it (splits into smaller pieces)
2. **Embeds** it (converts to vectors)
3. **Stores** it (saves in vector database)
4. **Queries** it (semantic search + answer generation)

## 📊 Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Main App (React + NestJS)               │
│  - User uploads PDF/DOCX                                    │
│  - Extracts text from file                                  │
│  - Sends text to Python RAG service                         │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP POST
                     │ { document_id, text, metadata }
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Python RAG Service (This App)                  │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │ 1. CHUNKING (app/utils/chunking.py)             │     │
│  │    Split text into smaller pieces                │     │
│  │    "Long document..." → ["Chunk 1", "Chunk 2"]   │     │
│  └──────────────┬───────────────────────────────────┘     │
│                 │                                           │
│  ┌──────────────▼───────────────────────────────────┐     │
│  │ 2. EMBEDDINGS (app/utils/embeddings.py)         │     │
│  │    Convert text to vectors                       │     │
│  │    "Chunk 1" → [0.2, 0.8, 0.1, ...] (768 dims)  │     │
│  └──────────────┬───────────────────────────────────┘     │
│                 │                                           │
│  ┌──────────────▼───────────────────────────────────┐     │
│  │ 3. VECTOR STORE (app/utils/vector_store.py)     │     │
│  │    Store embeddings in database                  │     │
│  │    Enable fast similarity search                 │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  When user asks question:                                  │
│  ┌──────────────────────────────────────────────────┐     │
│  │ 4. QUERY (app/services/document_service.py)     │     │
│  │    - Convert question to embedding               │     │
│  │    - Find similar chunks                         │     │
│  │    - Return relevant context                     │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 🏗️ Project Structure (For JS Developers)

```
RAG/
├── app/
│   ├── main.py                    # Entry point (like main.ts in NestJS)
│   ├── config.py                  # Configuration (like ConfigModule)
│   │
│   ├── api/routes/                # 🎮 Controllers (like @Controller())
│   │   ├── health.py              #    Health checks
│   │   └── documents.py           #    RAG endpoints (process, query)
│   │
│   ├── services/                  # 🔧 Business Logic (like @Injectable())
│   │   └── document_service.py    #    Orchestrates RAG workflow
│   │
│   ├── models/                    # 📋 DTOs (like class-validator)
│   │   └── document.py            #    Request/response models
│   │
│   └── utils/                     # 🛠️ Utilities
│       ├── chunking.py            #    Text chunking logic
│       ├── embeddings.py          #    Embedding generation
│       └── vector_store.py        #    Vector database operations
│
├── requirements.txt               # Dependencies (like package.json)
├── start.sh                       # Run script
└── README.md                      # You are here!
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9+ (similar to Node.js)
- pip (similar to npm)

### Installation

1. **Create virtual environment** (like `node_modules`):
```bash
python -m venv venv
```

2. **Activate virtual environment**:
```bash
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the server**:
```bash
# Development mode with auto-reload (like nodemon)
uvicorn app.main:app --reload --port 8000

# Or use the script:
chmod +x start.sh
./start.sh
```

The server starts at `http://localhost:8000`
- API docs: `http://localhost:8000/docs` (Swagger UI - auto-generated!)
- Alternative docs: `http://localhost:8000/redoc`

## 📚 API Endpoints

### Health Check
- `GET /api/health` - Service health

### RAG Operations
- `POST /api/documents/process` - Receive text from main app, chunk, embed, store
- `POST /api/documents/query` - Query documents semantically
- `DELETE /api/documents/{id}` - Delete document and its chunks

## 🔧 Key Concepts for JS/NestJS Developers

### Side-by-Side Comparison

| Concept | NestJS/Express | Python/FastAPI | Location |
|---------|---------------|----------------|----------|
| **Entry Point** | `main.ts` | `main.py` | `app/main.py` |
| **Routes** | `@Controller()` `@Get()` | `APIRouter()` `@router.get()` | `app/api/routes/` |
| **Services** | `@Injectable()` | Regular class | `app/services/` |
| **DTOs** | `class-validator` | Pydantic models | `app/models/` |
| **Config** | `ConfigModule` | `pydantic-settings` | `app/config.py` |
| **Async** | `async/await` | `async/await` | Same! ✅ |
| **Dependencies** | `package.json` | `requirements.txt` | Root |
| **Install** | `npm install` | `pip install` | - |
| **Run Dev** | `npm run start:dev` | `uvicorn --reload` | - |

### Key Differences

**1. Type Hints (Python 3.9+)**
```python
# Python - types come AFTER the variable
def greet(name: str) -> str:
    return f"Hello {name}"

# TypeScript - types come AFTER colon
function greet(name: string): string {
    return `Hello ${name}`;
}
```

**2. Imports**
```python
# Python
from app.services.document_service import DocumentService

# JavaScript/TypeScript
import { DocumentService } from './services/document_service';
```

**3. Decorators**
```python
# Python/FastAPI
@router.post("/upload")
async def upload_document():
    pass

# NestJS
@Post('upload')
async uploadDocument() {
}
```

## 📖 Learning Path

### Phase 1: Understand Structure ✅ (You are here!)
- [x] Project layout
- [x] Routes (controllers)
- [x] Services
- [x] Models (DTOs)

### Phase 2: Implement Chunking
Learn about text splitting strategies:
- Character-based chunking
- Sentence-aware chunking
- Semantic chunking
- **File**: `app/utils/chunking.py`

### Phase 3: Learn Embeddings
Understand vector representations:
- What are embeddings?
- OpenAI vs local models
- Batch processing
- **File**: `app/utils/embeddings.py`

### Phase 4: Vector Database
Set up vector storage:
- Choose a DB (ChromaDB recommended for learning)
- Store vectors
- Similarity search
- **File**: `app/utils/vector_store.py`

### Phase 5: Complete Service
Wire everything together:
- Process pipeline
- Query pipeline
- Error handling
- **File**: `app/services/document_service.py`

## 🎓 Resources for Learning

1. **Python Basics** (if needed):
   - [Python for JavaScript Developers](https://www.codecademy.com/resources/blog/python-vs-javascript/)
   
2. **FastAPI**:
   - [Official Docs](https://fastapi.tiangolo.com/) (excellent tutorial!)
   
3. **RAG Concepts**:
   - [What is RAG?](https://www.pinecone.io/learn/retrieval-augmented-generation/)
   - [LangChain RAG Tutorial](https://python.langchain.com/docs/use_cases/question_answering/)

4. **Vector Databases**:
   - [ChromaDB Docs](https://docs.trychroma.com/) (easiest to start)
   - [Pinecone](https://www.pinecone.io/) (production-ready)

## 🔍 Testing the Skeleton

```bash
# 1. Start the server
uvicorn app.main:app --reload

# 2. Visit http://localhost:8000/docs
#    You'll see all endpoints with "Try it out" buttons

# 3. Test the health endpoint:
curl http://localhost:8000/api/health
```

## 💡 Next Steps

When you're ready to implement:

1. Uncomment dependencies in `requirements.txt`
2. Install them: `pip install -r requirements.txt`
3. Implement one utility at a time
4. Test each component individually
5. Wire everything together

Happy learning! 🚀

