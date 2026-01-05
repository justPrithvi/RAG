"""
Main application entry point
Think of this like your main.ts in NestJS
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import health, documents
from app.middleware.auth import AuthMiddleware

# Create FastAPI app instance (like creating NestJS app)
app = FastAPI(
    title="RAG Backend Service",
    description="Document chunking, embedding, and vector search service",
    version="0.1.0"
)

# CORS middleware (similar to enabling CORS in NestJS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication middleware (validates JWT with NestJS backend)
app.add_middleware(
    AuthMiddleware,
    auth_service_url=settings.AUTH_SERVICE_URL
)

# Register routes (like importing modules in NestJS)
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "RAG Backend Service",
        "version": "0.1.0",
        "status": "running"
    }

# Startup event (like onModuleInit in NestJS)
@app.on_event("startup")
async def startup_event():
    print("🚀 RAG Backend Service starting...")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    print(f"🌐 CORS enabled for: {settings.ALLOWED_ORIGINS}")

# Shutdown event (like onModuleDestroy in NestJS)
@app.on_event("shutdown")
async def shutdown_event():
    print("👋 RAG Backend Service shutting down...")

