"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    
    AUTH_SERVICE_URL: str = "http://localhost:5001"

    # Java document service (Datavault-FileMaster): source of uploaded files for ingestion
    FILEMASTER_API_URL: str = "http://localhost:8080"
    # Shared secret with FileMaster, sent as X-Service-Key. Set in .env, never commit it.
    INTERNAL_SERVICE_KEY: str = ""
    FILEMASTER_TIMEOUT: float = 60.0
    # Largest file Python will download for ingestion (bytes). Default 200 MB.
    MAX_INGEST_FILE_BYTES: int = 200 * 1024 * 1024
    # How many chunks to send to the embedding model per request
    EMBEDDING_BATCH_SIZE: int = 32
    DATABASE_URL: str = "postgresql://prithviraj:Prithvi%4012345@localhost:5432/data_vault"
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT: float = 60.0
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSIONS: int = 768
    MAX_CONTEXT_MESSAGES: int = 10
    
    MAX_RESPONSE_TOKENS: int = 200
    RESPONSE_TEMPERATURE: float = 0.7
    MIN_RESPONSE_TOKENS: int = 50
    
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
