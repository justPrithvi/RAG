"""
Main application entry point
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health, documents, chat
from app.middleware.auth import AuthMiddleware

# Show app logs (e.g. rag.ingestion) alongside uvicorn's
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

app = FastAPI(
    title="RAG Backend Service",
    description="Document chunking, embedding, and vector search service",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    AuthMiddleware,
    auth_service_url=settings.AUTH_SERVICE_URL
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.get("/")
async def root():
    return {
        "message": "RAG Backend Service",
        "version": "0.1.0",
        "status": "running"
    }


@app.on_event("startup")
async def startup_event():
    print("🚀 RAG Backend Service starting...")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    print(f"🌐 CORS enabled for: {settings.ALLOWED_ORIGINS}")
    
    from app.database import init_db
    try:
        init_db()
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("💡 Make sure PostgreSQL is running and DATABASE_URL is correct")


@app.on_event("shutdown")
async def shutdown_event():
    print("👋 RAG Backend Service shutting down...")
