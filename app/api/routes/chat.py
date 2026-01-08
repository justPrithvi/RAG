"""
Chat Routes
Handles chat/prompt endpoints for LLM interaction
Uses local Ollama model with PostgreSQL persistence
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from app.models.chat import ChatRequest, ChatResponse
from app.models.db_models import Conversation, Message
from app.database import get_db
from app.config import settings
import httpx
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a prompt to the LLM and get a response
    Uses local Ollama model (llama3)
    
    Request body:
    {
        "message": "User's question",
        "conversationId": "optional-conversation-id",
        "userId": "optional-user-id"
    }
    
    Response:
    {
        "response": "LLM's answer",
        "conversationId": "conversation-id",
        "userId": "user-id",
        "model": "llama3",
        "tokens_used": null
    }
    """
    try:
        # Get authenticated user (from middleware)
        user = getattr(request.state, "user", None)
        
        # Generate conversationId if not provided
        conversation_id = chat_request.conversationId or str(uuid.uuid4())
        
        # Get or create conversation in database
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        
        if not conversation:
            # Create new conversation
            conversation = Conversation(
                id=conversation_id,
                user_id=chat_request.userId or (user.get("id") if user else None),
                title=chat_request.message[:50] + ("..." if len(chat_request.message) > 50 else "")
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        else:
            # Update timestamp for existing conversation
            conversation.updated_at = datetime.now()
            db.commit()
        
        # Save user message to database
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=chat_request.message
        )
        db.add(user_message)
        db.commit()
        
        # Get recent message history from database for context
        recent_messages = db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at.desc())\
            .limit(settings.MAX_CONTEXT_MESSAGES)\
            .all()
        
        # Reverse to get chronological order
        recent_messages = list(reversed(recent_messages))
        
        # Convert database messages to format for LLM
        context_for_llm = [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
        ]
        
        # Add system message to encourage concise, complete responses
        system_message = {
            "role": "system",
            "content": (
                "You are a helpful assistant. Provide clear, concise answers. "
                "Keep responses brief (2-3 sentences) but always complete your thoughts. "
                "Never end mid-sentence."
            )
        }
        
        # Prepare Ollama request with limited context
        ollama_request = {
            "model": settings.OLLAMA_MODEL,
            "messages": [system_message] + context_for_llm,  # System message + context
            "stream": False,
            "options": {
                "num_predict": settings.MAX_RESPONSE_TOKENS,  # Max tokens (with buffer for completion)
                "temperature": settings.RESPONSE_TEMPERATURE,  # Control randomness
                "stop": ["\n\n\n"],  # Stop at natural breaks (3 newlines = end of thought)
            }
        }
        # Call Ollama API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=ollama_request,
                timeout=60.0  # Ollama can take a while
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama API error: {response.text}"
                )
            
            ollama_response = response.json()
        # Extract the assistant's message
        assistant_message = ollama_response.get("message", {}).get("content", "")
        
        if not assistant_message:
            raise HTTPException(
                status_code=500,
                detail="No response from Ollama model"
            )
        
        # Save assistant's response to database
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_message
        )
        db.add(assistant_msg)
        db.commit()
        
        # Get FULL conversation history from database (for UI display)
        all_messages = db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at.asc())\
            .all()
        
        messages_response = [
            {"role": msg.role, "content": msg.content}
            for msg in all_messages
        ]
        
        return ChatResponse(
            response=assistant_message,  # Last assistant message
            messages=messages_response,  # Full conversation history
            conversationId=conversation_id,  # Return the conversationId (generated or provided)
            userId=chat_request.userId or (user.get("id") if user else None),
            model=settings.OLLAMA_MODEL,
            tokens_used=None  # Ollama doesn't return token count
        )
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Ollama model took too long to respond"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Ollama: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )


@router.get("/conversations")
async def get_all_conversations(userId: str = None, db: Session = Depends(get_db)):
    """
    Get all conversations with metadata from database
    
    Query params:
    - userId (optional): Filter conversations by user ID
    
    Returns list of conversations sorted by most recent
    """
    # Query conversations from database
    query = db.query(Conversation)
    
    if userId:
        query = query.filter(Conversation.user_id == userId)
    
    conversations_db = query.order_by(Conversation.updated_at.desc()).all()
    
    conversation_list = []
    
    for conv in conversations_db:
        # Get message count and last message
        messages = db.query(Message)\
            .filter(Message.conversation_id == conv.id)\
            .order_by(Message.created_at.asc())\
            .all()
        
        last_message = messages[-1] if messages else None
        
        conversation_list.append({
            "conversationId": conv.id,
            "userId": conv.user_id,
            "title": conv.title,
            "createdAt": conv.created_at.isoformat(),
            "updatedAt": conv.updated_at.isoformat(),
            "messageCount": len(messages),
            "lastMessage": {
                "role": last_message.role,
                "content": last_message.content[:100] + ("..." if len(last_message.content) > 100 else ""),
                "timestamp": last_message.created_at.isoformat()
            } if last_message else None
        })
    
    return {
        "conversations": conversation_list,
        "total": len(conversation_list)
    }


@router.delete("/chat/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """
    Delete a conversation and all its messages from database
    
    CASCADE delete handles removing all related messages
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    
    return {
        "message": "Conversation deleted successfully",
        "conversationId": conversation_id
    }


@router.get("/chat/{conversation_id}/history")
async def get_conversation_history(conversation_id: str, db: Session = Depends(get_db)):
    """
    Get conversation history from database
    
    Returns all messages in a conversation
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    
    messages = db.query(Message)\
        .filter(Message.conversation_id == conversation_id)\
        .order_by(Message.created_at.asc())\
        .all()
    
    return {
        "conversationId": conversation_id,
        "messages": [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ],
        "message_count": len(messages)
    }

