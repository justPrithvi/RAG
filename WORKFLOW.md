# RAG Workflow Explained 📚

A detailed guide on how the RAG system works, for developers coming from JavaScript.

## 🔄 Complete Data Flow

### Part 1: Document Processing (Ingestion)

```
User uploads file
      │
      ▼
┌─────────────────────────────────────┐
│    Main App (React + NestJS)        │
│                                     │
│  1. Receive file upload             │
│  2. Extract text from PDF/DOCX      │
│     (using libraries like pdf-parse)│
└──────────┬──────────────────────────┘
           │
           │ HTTP POST /api/documents/process
           │ {
           │   "document_id": "doc_123",
           │   "text": "Long document text...",
           │   "metadata": {
           │     "filename": "report.pdf",
           │     "user_id": "user_456"
           │   }
           │ }
           ▼
┌─────────────────────────────────────┐
│   Python RAG Service                │
│   (app/api/routes/documents.py)     │
│                                     │
│   process_document() endpoint       │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│   DocumentService                   │
│   (app/services/document_service.py)│
│                                     │
│   Orchestrates the pipeline:        │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ STEP 1: Chunking                    │
│ (app/utils/chunking.py)             │
│                                     │
│ Input:                              │
│   "This is a very long document     │
│    about Python and machine         │
│    learning. Python is a great      │
│    language. Machine learning       │
│    is powerful..."                  │
│                                     │
│ Output (chunks):                    │
│   [                                 │
│     "This is a very long document   │
│      about Python and machine       │
│      learning.",                    │
│     "Python is a great language.    │
│      Machine learning is powerful." │
│   ]                                 │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ STEP 2: Generate Embeddings         │
│ (app/utils/embeddings.py)           │
│                                     │
│ For each chunk, convert to vector:  │
│                                     │
│ Chunk 1:                            │
│   "This is a very long document..." │
│   → [0.234, 0.876, 0.123, ...]      │
│      (768 numbers)                  │
│                                     │
│ Chunk 2:                            │
│   "Python is a great language..."   │
│   → [0.456, 0.234, 0.789, ...]      │
│      (768 numbers)                  │
│                                     │
│ Uses: OpenAI API, Sentence          │
│       Transformers, or other        │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ STEP 3: Store in Vector DB          │
│ (app/utils/vector_store.py)         │
│                                     │
│ Store each chunk with:              │
│   - Chunk ID                        │
│   - Chunk text                      │
│   - Embedding vector                │
│   - Metadata                        │
│                                     │
│ Vector DB (ChromaDB/Pinecone)       │
│ enables fast similarity search      │
└─────────────────────────────────────┘
```

### Part 2: Querying (Retrieval + Generation)

```
User asks question: "What is Python used for?"
      │
      ▼
┌─────────────────────────────────────┐
│    Frontend (React)                 │
│                                     │
│    Sends query to backend           │
└──────────┬──────────────────────────┘
           │
           │ HTTP POST /api/documents/query
           │ {
           │   "question": "What is Python used for?",
           │   "max_results": 5
           │ }
           ▼
┌─────────────────────────────────────┐
│   Python RAG Service                │
│   (app/api/routes/documents.py)     │
│                                     │
│   query_documents() endpoint        │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│   DocumentService                   │
│   query_documents()                 │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ STEP 1: Embed the Question          │
│ (app/utils/embeddings.py)           │
│                                     │
│ Question:                           │
│   "What is Python used for?"        │
│   → [0.445, 0.223, 0.789, ...]      │
│      (same 768 dimensions)          │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ STEP 2: Similarity Search           │
│ (app/utils/vector_store.py)         │
│                                     │
│ Compare question vector with all    │
│ stored chunk vectors.               │
│                                     │
│ Find most similar chunks:           │
│   Chunk 2: similarity = 0.92        │
│   Chunk 1: similarity = 0.78        │
│   Chunk 5: similarity = 0.65        │
│                                     │
│ Return top 5 chunks                 │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ STEP 3: Format Results              │
│                                     │
│ Return:                             │
│   {                                 │
│     "query": "What is Python...",   │
│     "results": [                    │
│       {                             │
│         "content": "Python is...",  │
│         "score": 0.92,              │
│         "metadata": {...}           │
│       }                             │
│     ]                               │
│   }                                 │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ OPTIONAL STEP 4: LLM Generation     │
│                                     │
│ Send retrieved chunks to LLM:       │
│                                     │
│ Prompt:                             │
│   "Based on these documents:        │
│    [chunk 1, chunk 2, chunk 3]      │
│    Answer: What is Python used for?"│
│                                     │
│ LLM generates natural answer:       │
│   "Python is used for web dev,      │
│    machine learning, data science..." │
└─────────────────────────────────────┘
```

## 🧠 Key Concepts Explained

### 1. Why Chunking?

**Problem**: Documents are long, but:
- Embedding models have token limits (usually 512-8192 tokens)
- LLMs have context limits
- Smaller chunks = more precise retrieval

**Solution**: Break into chunks
```python
# Instead of:
"Very long 50-page document..."  # Too big!

# We do:
[
  "Page 1 content...",    # Chunk 1
  "Page 2 content...",    # Chunk 2
  "Page 3 content...",    # Chunk 3
  ...
]
```

**Overlap**: Chunks overlap slightly to preserve context
```
Chunk 1: [____________________]
Chunk 2:           [____________________]
Chunk 3:                     [____________________]
                   ↑↑↑↑      ↑↑↑↑
                   Overlap    Overlap
```

### 2. What Are Embeddings?

**Think of embeddings as coordinates in space**

```
Text: "Python programming"
Embedding: [0.2, 0.8, 0.1, 0.5, ...] (768 numbers)
           Like coordinates: (x, y, z, ...)

Similar meanings = close in space!

"Python programming" → [0.2, 0.8, 0.1, ...]
"Python coding"      → [0.21, 0.79, 0.11, ...] ← Very close!
"Banana recipe"      → [0.9, 0.1, 0.8, ...]   ← Far away!
```

**JavaScript Analogy**:
```javascript
// Like how we might hash or fingerprint content
const text = "Python programming";
const hash = generateHash(text);  // "a7b4c9..."

// But embeddings are smarter!
const embedding = generateEmbedding(text);  // [0.2, 0.8, ...]
// Similar text → similar embeddings!
```

### 3. Vector Database

**Regular Database**:
```sql
SELECT * FROM documents WHERE text LIKE '%Python%'
-- Keyword matching only
```

**Vector Database**:
```python
# Find documents SIMILAR to query (semantically!)
query_embedding = embed("What is Python?")
results = vector_db.search(query_embedding, top_k=5)
# Returns documents about Python, even if they don't contain "Python"
# E.g., "This programming language..." might match!
```

**Popular Options**:
- **ChromaDB**: Local, easy to start, great for learning
- **Pinecone**: Cloud, scalable, production-ready
- **Weaviate, Qdrant**: Other production options

### 4. RAG vs Regular Search

**Regular Keyword Search**:
```
Query: "How do I learn Python?"
Database: Search for exact words "learn" and "Python"
Result: Documents containing these exact words
Problem: Misses synonyms, context, meaning
```

**RAG (Semantic Search + LLM)**:
```
Query: "How do I learn Python?"
Step 1: Convert to embedding (captures meaning)
Step 2: Find similar chunks (understands context)
        Matches: "Python tutorial", "Getting started with Python",
                "Python for beginners" ← No exact keywords!
Step 3: LLM generates answer using retrieved chunks
Result: Natural, contextual answer
```

## 🛠️ Implementation Strategy

### Phase 1: Simple Text Chunking
```python
def simple_chunk(text, chunk_size=1000):
    # Split every 1000 characters
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    return chunks
```

### Phase 2: Choose Embedding Provider

**Option A: OpenAI (Easiest)**
```python
import openai

response = openai.Embedding.create(
    model="text-embedding-ada-002",
    input="Your text here"
)
embedding = response['data'][0]['embedding']
# Returns: [0.234, 0.876, ...] (1536 dimensions)
```

**Option B: Sentence Transformers (Free, Local)**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode("Your text here")
# Returns: [0.234, 0.876, ...] (384 dimensions)
```

### Phase 3: Set Up ChromaDB (Simplest)
```python
import chromadb

# Initialize
client = chromadb.Client()
collection = client.create_collection("documents")

# Store
collection.add(
    embeddings=[[0.1, 0.2, ...]],  # Your embedding
    documents=["Chunk text"],
    ids=["chunk_1"]
)

# Search
results = collection.query(
    query_embeddings=[[0.15, 0.21, ...]],  # Query embedding
    n_results=5
)
```

## 📝 Testing Strategy

### Test Locally (Without Real Implementation)

1. **Test Chunking**:
```bash
curl -X POST http://localhost:8000/api/documents/process \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "test_1",
    "text": "Short test text",
    "metadata": {"filename": "test.txt"}
  }'
```

2. **Test Query**:
```bash
curl -X POST http://localhost:8000/api/documents/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this about?",
    "max_results": 5
  }'
```

3. **Use Swagger UI**: Visit `http://localhost:8000/docs`

## 🎯 Learning Checkpoints

- [ ] ✅ Understand project structure
- [ ] Run the skeleton server
- [ ] Test endpoints with Swagger UI
- [ ] Implement simple chunking
- [ ] Choose and test embedding provider
- [ ] Set up vector database
- [ ] Wire everything together
- [ ] Test end-to-end flow
- [ ] Add error handling
- [ ] Optimize performance

## 🚀 When You're Ready

1. Pick one component to implement
2. Uncomment dependencies in `requirements.txt`
3. Test that component in isolation
4. Move to next component
5. Integrate everything

Don't try to build it all at once! 🎯

