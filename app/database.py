"""
Database configuration and connection
Similar to TypeORM setup in NestJS
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Database URL format: postgresql://user:password@host:port/database
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",  # Log SQL queries in dev
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True  # Verify connections before using
)

# Session factory (like EntityManager in TypeORM)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models (like Entity decorator in TypeORM)
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    Similar to injecting DataSource in NestJS
    
    Usage:
        @router.get("/")
        def route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create tables if they don't exist
    Similar to synchronize: true in TypeORM
    
    Call this on app startup
    """
    from app.models.db_models import Conversation, Message  # Import all models
    
    print("🔄 Initializing database...")
    
    # Create pgvector extension if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("✅ Vector extension enabled")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified")

