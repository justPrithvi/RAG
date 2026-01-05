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
    
    # Vector DB (will add later)
    # VECTOR_DB_URL: str = ""
    
    # API Keys (will add as needed)
    # OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance (like exporting from a config module)
settings = Settings()

