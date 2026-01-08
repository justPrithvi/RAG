# Database Setup Guide

## Prerequisites

1. **Install PostgreSQL** (if not already installed)
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt-get install postgresql-15 postgresql-contrib-15

# Windows
# Download from: https://www.postgresql.org/download/windows/
```

2. **Install pgvector extension**
```bash
# macOS
brew install pgvector

# Ubuntu/Debian
sudo apt-get install postgresql-15-pgvector

# Or build from source
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install
```

---

## Quick Setup

### 1. Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE rag_db;

# Create user (optional)
CREATE USER rag_user WITH PASSWORD 'your_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE rag_db TO rag_user;

# Exit
\q
```

### 2. Enable pgvector Extension

```bash
# Connect to your database
psql rag_db

# Enable extension
CREATE EXTENSION vector;

# Verify
\dx

# Exit
\q
```

### 3. Configure Connection String

Create `.env` file in project root:

```bash
# Database connection
DATABASE_URL=postgresql://rag_user:your_password@localhost:5432/rag_db

# Or for default postgres user
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_db
```

**Format:** `postgresql://username:password@host:port/database_name`

---

## Auto-Sync (Recommended)

The application will automatically create tables on startup.

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app.main:app --reload --port 8000
```

**Output:**
```
🔄 Initializing database...
✅ Vector extension enabled
✅ Database tables created/verified
🚀 RAG Backend Service starting...
```

---

## Manual Setup (Alternative)

If auto-sync doesn't work, run the SQL manually:

```bash
# Run the schema file
psql rag_db < schema.sql

# Or copy-paste from schema.sql into psql
psql rag_db
\i schema.sql
```

---

## Verify Tables

```bash
psql rag_db

# List tables
\dt

# Should show:
#  conversations
#  messages
#  document_chunks

# Describe table structure
\d conversations
\d messages
\d document_chunks

# Check if vector extension is enabled
\dx
```

---

## Connection String Examples

### Local Development
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_db
```

### Docker
```
DATABASE_URL=postgresql://postgres:postgres@db:5432/rag_db
```

### Remote Server
```
DATABASE_URL=postgresql://user:pass@your-server.com:5432/rag_db
```

### Heroku/Cloud
```
DATABASE_URL=postgresql://user:pass@ec2-xxx.compute-1.amazonaws.com:5432/dbname?sslmode=require
```

---

## Table Designs

### 1. Conversations
```sql
- id (VARCHAR, PK) - UUID
- user_id (VARCHAR) - User identifier
- title (VARCHAR(255)) - First message preview
- created_at (TIMESTAMP) - Auto-generated
- updated_at (TIMESTAMP) - Auto-updated
```

### 2. Messages
```sql
- id (SERIAL, PK) - Auto-increment
- conversation_id (VARCHAR, FK) - References conversations
- role (VARCHAR(20)) - 'user' or 'assistant'
- content (TEXT) - Message content
- created_at (TIMESTAMP) - Auto-generated
```

### 3. Document Chunks (for RAG)
```sql
- id (SERIAL, PK) - Auto-increment
- document_id (VARCHAR) - Document identifier
- chunk_index (INTEGER) - Chunk number
- content (TEXT) - Chunk text
- embedding (VECTOR(384)) - Vector embedding
- metadata (TEXT) - JSON metadata
- created_at (TIMESTAMP) - Auto-generated
```

---

## Troubleshooting

### Issue: "CREATE EXTENSION vector" fails

**Solution:** Install pgvector extension first:
```bash
# macOS
brew install pgvector

# Ubuntu
sudo apt-get install postgresql-15-pgvector
```

### Issue: Connection refused

**Solution:** Check if PostgreSQL is running:
```bash
# macOS
brew services list

# Ubuntu
sudo systemctl status postgresql

# Start if not running
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Ubuntu
```

### Issue: Authentication failed

**Solution:** Update `pg_hba.conf` to trust local connections:
```bash
# Find pg_hba.conf
psql -c "SHOW hba_file"

# Edit and change to 'trust' for local development
# local   all   all   trust
```

### Issue: Database doesn't exist

**Solution:** Create it:
```bash
createdb rag_db

# Or via psql
psql postgres -c "CREATE DATABASE rag_db;"
```

---

## Migration Commands

### Reset Database (⚠️ Deletes all data)
```bash
psql rag_db < schema.sql
```

### Backup Database
```bash
pg_dump rag_db > backup.sql
```

### Restore Database
```bash
psql rag_db < backup.sql
```

---

## Next Steps

1. ✅ Configure `DATABASE_URL` in `.env`
2. ✅ Start server (tables auto-create)
3. ✅ Test with Postman
4. Later: Add embeddings to `document_chunks` table for RAG

---

## Vector Search Example (Future Use)

```sql
-- Find similar documents using cosine similarity
SELECT 
    content,
    1 - (embedding <=> '[0.1, 0.2, ...]') as similarity
FROM document_chunks
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 5;
```

Replace `[0.1, 0.2, ...]` with your query embedding vector.

---

Your database is now ready! 🚀

