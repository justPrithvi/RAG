"""
Database models (SQLAlchemy ORM)
Similar to TypeORM entities in NestJS
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base
import uuid


def generate_uuid():
    """Generate UUID string"""
    return str(uuid.uuid4())


class Conversation(Base):
    """
    Conversation entity
    Similar to @Entity() class in TypeORM
    """
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Fields
    user_id = Column(String, nullable=True, index=True)
    title = Column(String(255), nullable=False)
    
    # Timestamps (similar to @CreateDateColumn, @UpdateDateColumn)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships (similar to @OneToMany in TypeORM)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title})>"


class Message(Base):
    """
    Message entity
    Stores individual messages in conversations
    """
    __tablename__ = "messages"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key (similar to @ManyToOne in TypeORM)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Fields
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship (similar to @ManyToOne in TypeORM)
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"


# Future: Document chunks with embeddings for RAG
class DocumentChunk(Base):
    """
    Document chunks with vector embeddings
    For RAG functionality (future use)
    """
    __tablename__ = "document_chunks"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Document metadata
    document_id = Column(String, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    
    # Vector embedding (pgvector)
    # Dimension depends on your embedding model (e.g., 384 for all-MiniLM-L6-v2)
    embedding = Column(Vector(384), nullable=True)  # Will add embeddings later
    
    # Metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    chunk_metadata = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk={self.chunk_index})>"

