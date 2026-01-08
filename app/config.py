"""
Configuration settings
Think of this like your ConfigService in NestJS
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    Similar to @nestjs/config ConfigService
    """
    # Environment
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # NestJS backend
    ]
    
    # Authentication
    AUTH_SERVICE_URL: str = "http://localhost:5001"  # NestJS auth service
    
    # Database
    # @ symbol in password is URL-encoded as %40
    DATABASE_URL: str = "postgresql://prithviraj:Prithvi%4012345@localhost:5432/data_vault"
    
    # Ollama (Local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"  # Your installed model
    MAX_CONTEXT_MESSAGES: int = 10  # Number of recent messages to send to LLM (prevents token limits)
    
    # Response control
    MAX_RESPONSE_TOKENS: int = 200  # Buffer room to complete thoughts naturally
    RESPONSE_TEMPERATURE: float = 0.7  # Creativity (0.0-2.0, lower = more focused)
    MIN_RESPONSE_TOKENS: int = 50  # Minimum response length
    
    # Vector DB (will add later)
    # VECTOR_DB_URL: str = ""
    
    # API Keys (optional, for OpenAI if needed later)
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance (like exporting from a config module)
settings = Settings()

