# Embedding & Chunking Theory for RAG 🧠

A comprehensive guide to chunking documents and semantic search for RAG systems.

---

## 📚 Part 1: Document Chunking

### 1️⃣ Why Chunking Matters

- **Each chunk becomes one vector** in your database
- **Chunks too big** → mixed topics → vague vectors → noisy similarity search
- **Chunks too small** → lost context → LLM can't reason → hallucinations

### 2️⃣ Chunk Size

**Recommended: 200–400 tokens per chunk**

- ✅ Small enough to maintain semantic coherence
- ✅ Large enough to include full context (steps, definitions, paragraphs)

**Optional Overlap: 10–20%**

- Helps cover context that splits across chunk boundaries
- Prevents information loss at boundaries

### 3️⃣ Chunk Boundaries

**Prefer semantic boundaries over arbitrary splits:**

- ✅ Paragraphs
- ✅ Headings / sections
- ✅ Sentence endings (if needed)
- ❌ Avoid cutting mid-sentence or mid-step

**Examples:**

❌ **Bad Example:**
```
"To rotate your API key, go to Setting… 
generate new key, revoke old…"
(cut in the middle of instructions)
```

✅ **Good Example:**
```
"To rotate your API key, go to Settings > API Keys. 
Click 'Generate New Key', then revoke the old one."
(complete paragraph with full instructions)
```

### 4️⃣ Metadata for Each Chunk

Store useful information along with text:

- **Source document** - Which file it came from
- **Section / heading** - Where in the document
- **Page number** - For reference
- **Created date** - When it was added

**Benefits:**
- Enables filtering during retrieval
- Prevents irrelevant chunks from being returned
- Provides context for the LLM

### 5️⃣ Chunk Quality Checks

**Before embedding, clean your chunks:**

- ❌ Remove boilerplate (headers, footers, nav links)
- ✅ Merge very short paragraphs if semantically linked
- ❌ Skip empty / irrelevant sections
- ✅ Preserve code blocks and structured content

### 6️⃣ Token vs Character-Based Chunking

**Use tokens, not characters!**

- LLMs have **token limits**, not character limits
- 1 token ≈ 4 characters (English)
- Use libraries like `tiktoken` (OpenAI) to count tokens

```python
import tiktoken

encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
tokens = encoder.encode("Your text here")
token_count = len(tokens)
```

### 7️⃣ Optional: Hybrid Chunking

**Hierarchical chunking strategy:**

1. **Large chunk** → Provides top-level context
2. **Sub-chunks** → Contains specific details

**Benefits:**
- Model can retrieve both overview and specifics
- Better context understanding
- Improved answer quality

### 8️⃣ General Rules of Thumb

| Problem | Cause | Fix |
|---------|-------|-----|
| **Hallucinations** | Chunk too short / incomplete | Merge into coherent paragraph |
| **Irrelevant search results** | Chunk mixes multiple topics | Split along semantic boundaries |
| **Low recall** | Chunk too big | Reduce size, add 10–20% overlap |
| **Redundant chunks** | Small overlapping chunks | Merge duplicates, use metadata |

---

## 🔍 Part 2: Semantic Search & Filtering

### 1. Core Concept

**Semantic Search** = Finding text based on **meaning**, not exact keywords

**RAG Pipeline:**
1. Chunk documents → Generate embeddings
2. Store embeddings in vector database
3. Embed user query → Similarity search → Retrieve top N chunks
4. Filter + rerank → Feed best chunks to LLM

### 2. Complete Pipeline Overview

```
┌─────────────────────┐
│ 1. Chunk Documents  │  200-400 tokens, semantic boundaries
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 2. Embed Chunks     │  Use same model as queries!
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 3. Store in Vector  │  Postgres+pgvector, ChromaDB, Pinecone
│    Database         │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 4. Query Embedding  │  Convert user question to vector
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 5. Retrieve Top N   │  Get 30-50 most similar chunks
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 6. Filter Chunks    │  Apply similarity threshold
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 7. Rerank           │  Score by relevance
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 8. Feed to LLM      │  Send top 3-7 chunks + question
└─────────────────────┘
```

### 3. Why Fetch Extra Chunks?

**Over-fetch then filter** is better than under-fetching!

- ✅ Vector DB only knows **semantic similarity**, not **usefulness**
- ✅ Cosine similarity finds topic-related chunks
- ❌ Some chunks may be irrelevant even if similar
- ✅ Better to over-fetch (N=30-50) and filter down to best (K=3-7)

### 4. Similarity Score Explained

**Cosine Similarity:**

- Computed on **embeddings** (vectors), not by the LLM
- Measures the **angle** between two vectors
- **Score → 1**: Very similar (same direction)
- **Score → 0**: Unrelated (perpendicular)
- **Score → -1**: Opposite meaning

**Formula:**

```
cosine_similarity = (query · chunk) / (||query|| * ||chunk||)
```

**Libraries handle this automatically:**
- pgvector (Postgres)
- FAISS
- ChromaDB
- scikit-learn

### 5. Postgres with pgvector

**Distance Operators:**

| Operator | Type | Description |
|----------|------|-------------|
| `<=>` | Cosine distance | Most common for semantic search |
| `<->` | Euclidean distance | Geometric distance |
| `<#>` | Inner product | Dot product |

**SQL Example:**

```sql
SELECT
  id,
  content,
  1 - (embedding <=> :query_embedding) AS cosine_similarity
FROM documents
ORDER BY embedding <=> :query_embedding
LIMIT 30;
```

Returns vectors with similarity scores for filtering.

### 6. Chunk Filtering Steps

#### 6.1 Similarity Threshold (Always Apply)

```python
# Keep only chunks above similarity threshold
kept = [c for c in chunks if c.cosine_similarity > 0.75]
```

**Typical thresholds:**
- `> 0.8` - Very strict (high precision, low recall)
- `> 0.75` - Balanced (recommended)
- `> 0.7` - More lenient (high recall, lower precision)

#### 6.2 Structural Filters (Optional but Recommended)

Remove noise and low-quality chunks:

```python
# Remove very short chunks
kept = [c for c in kept if len(c.text.split()) > 50]

# Remove boilerplate
kept = [c for c in kept if not is_boilerplate(c.text)]
```

**Filter out:**
- Very short chunks (< 50 tokens)
- Headings only
- Navigation elements
- Footers and headers

#### 6.3 Relevance Gate (Most Important!)

**Decides if chunk actually answers the question**

**Implementation options:**

**A) Cross-encoder (Best accuracy)**
```python
from sentence_transformers import CrossEncoder

model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
scores = model.predict([(query, c.text) for c in kept])
kept = [c for c, score in zip(kept, scores) if score > 0.6]
```

**B) LLM YES/NO prompt (Good but slower)**
```python
prompt = f"""
Does this text answer the question?
Question: {query}
Text: {chunk.text}
Answer YES or NO.
"""
# Keep only chunks with YES response
```

**C) Heuristics (Fast but less accurate)**
```python
# Keyword overlap, entity matching, etc.
```

### 7. Reranking & Final Selection

**Goal:** Select the absolute best 3-7 chunks for the LLM

```python
# Combine similarity + relevance scores
for chunk in kept:
    chunk.final_score = (
        0.4 * chunk.cosine_similarity + 
        0.6 * chunk.relevance_score
    )

# Sort by final score
kept.sort(key=lambda c: c.final_score, reverse=True)

# Take top K
top_chunks = kept[:5]  # Adjust K based on your needs
```

**Why limit to 3-7 chunks?**
- Saves tokens (cheaper API calls)
- Improves LLM focus
- Reduces noise
- Better answer quality

### 8. Key Principles

| Layer | Role | Goal |
|-------|------|------|
| **Vector DB** | Recall | Find related chunks (cast wide net) |
| **Application Layer** | Precision | Filter + relevance gate (narrow down) |
| **LLM** | Reasoning | Generate answer from top chunks |

**Remember:** Similarity ≠ Usefulness → Always filter and rerank!

### 9. Quick Pipeline Diagram

```
Query 
  → Embed 
    → DB Search (top N=30-50) 
      → Similarity Threshold (>0.75)
        → Structural Filters 
          → Relevance Gate 
            → Rerank 
              → Top K (3-7) 
                → LLM
```

### 10. Best Practices & Notes

✅ **Do:**
- Over-fetch from DB (N=30-50), filter down to 3-7
- Use **same embedding model** for query + chunks
- Apply **metadata filters** (document type, section, date)
- Monitor and tune thresholds based on results
- Log relevance scores for debugging

❌ **Don't:**
- Never modify embeddings in DB based on one bad query
- Don't send all N retrieved chunks to LLM
- Don't use different embedding models for indexing vs search
- Don't skip the relevance gate step

---

## 🎯 Quick Reference

### Chunking Checklist
- [ ] 200-400 tokens per chunk
- [ ] 10-20% overlap
- [ ] Semantic boundaries (paragraphs, sections)
- [ ] Metadata attached (source, section, page)
- [ ] Quality checks applied (no boilerplate)
- [ ] Token-based (not character-based)

### Search & Filter Checklist
- [ ] Retrieve N=30-50 chunks from DB
- [ ] Apply similarity threshold (>0.75)
- [ ] Filter by structure (remove short/boilerplate)
- [ ] Apply relevance gate (cross-encoder or LLM)
- [ ] Rerank by combined score
- [ ] Select top K=3-7 for LLM
- [ ] Monitor and adjust thresholds

---

**This guide provides the theoretical foundation for building effective RAG systems. Use it as a reference when implementing your chunking and search pipelines!** 🚀
