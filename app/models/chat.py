"""
Chat Models
Request/Response models for chat endpoints
"""
from pydantic import BaseModel
from typing import Optional, List


class ChatMessage(BaseModel):
    """
    Individual message in a conversation
    """
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """
    Chat request from frontend
    
    userId is required for new conversations (conversationId=null)
    userId is optional for existing conversations (we look it up from DB)
    """
    message: str
    conversationId: Optional[str] = None
    userId: Optional[str] = None  # Required for new conv, optional for existing


class ChatResponse(BaseModel):
    """
    Chat response to frontend
    """
    response: str  # Last assistant message (for backward compatibility)
    messages: List[ChatMessage]  # Full conversation history
    conversationId: Optional[str] = None
    userId: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    tokens_used: Optional[int] = None

