"""
Chat Routes
Handles general chat and document-specific chat with RAG
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, field_validator
from typing import Optional, List, Union
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.api.deps import CurrentUser, get_current_user
from app.services.document_access import require_document_access
from app.models.chat import ChatRequest, ChatResponse
from app.models.db_models import Conversation, Message, DocumentChatMessage
from app.database import get_db
from app.services.llm_service import llm_service
from app.services.vector_search_service import vector_search_service
from app.config import settings
import httpx

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    General chat endpoint with conversation persistence.
    The conversation owner is the Nest-validated user; any userId in the body is ignored.
    """
    try:
        if chat_request.conversationId:
            conversation = db.query(Conversation)\
                .filter(Conversation.id == chat_request.conversationId)\
                .first()
            # Someone else's conversation looks the same as a missing one
            if not conversation or conversation.user_id != user.id_str:
                raise HTTPException(status_code=404, detail="Conversation not found")

            conversation.updated_at = datetime.now()
            db.commit()
        else:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user.id_str,
                title=chat_request.message[:50] + ("..." if len(chat_request.message) > 50 else "")
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        conversation_id = conversation.id
        
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=chat_request.message
        )
        db.add(user_message)
        db.commit()
        
        recent_messages = db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at.desc())\
            .limit(settings.MAX_CONTEXT_MESSAGES)\
            .all()
        
        recent_messages = list(reversed(recent_messages))
        
        context_for_llm = [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
        ]
        
        system_message = {
            "role": "system",
            "content": (
                "You are a helpful assistant. Provide clear, concise answers. "
                "Keep responses brief (2-3 sentences) but always complete your thoughts. "
                "Never end mid-sentence."
            )
        }
        
        ollama_request = {
            "model": settings.OLLAMA_MODEL,
            "messages": [system_message] + context_for_llm,
            "stream": False,
            "options": {
                "num_predict": settings.MAX_RESPONSE_TOKENS,
                "temperature": settings.RESPONSE_TEMPERATURE,
                "stop": ["\n\n\n"]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json=ollama_request,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Ollama API error: {response.text}"
                )
            
            ollama_response = response.json()
        
        assistant_message = ollama_response.get("message", {}).get("content", "")
        
        if not assistant_message:
            raise HTTPException(
                status_code=500,
                detail="No response from Ollama model"
            )
        
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_message
        )
        db.add(assistant_msg)
        db.commit()
        
        all_messages = db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at.asc())\
            .all()
        
        messages_response = [
            {"role": msg.role, "content": msg.content}
            for msg in all_messages
        ]
        
        return ChatResponse(
            response=assistant_message,
            messages=messages_response,
            conversationId=conversation_id,
            userId=user.id_str,
            model=settings.OLLAMA_MODEL,
            tokens_used=None
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
async def get_all_conversations(
    userId: Optional[str] = None,  # still sent by the UI; ignored
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all conversations for the authenticated user
    """
    conversations_db = db.query(Conversation)\
        .filter(Conversation.user_id == user.id_str)\
        .order_by(Conversation.updated_at.desc())\
        .all()
    
    conversation_list = []
    
    for conv in conversations_db:
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
async def delete_conversation(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete one of the authenticated user's conversations and all its messages
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation or conversation.user_id != user.id_str:
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
async def get_conversation_history(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the history of one of the authenticated user's conversations
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conversation or conversation.user_id != user.id_str:
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


class DocumentChatRequest(BaseModel):
    """Request model for document chat"""
    message: str
    documentId: Union[str, int]
    userId: Optional[Union[str, int]] = None  # still sent by the UI; ignored
    conversationId: Optional[str] = None
    
    @field_validator('documentId')
    @classmethod
    def convert_document_id_to_str(cls, v):
        return str(v)


class DocumentChatResponse(BaseModel):
    """Response model for document chat"""
    response: str
    documentId: str
    userId: str
    conversationId: str
    relevantChunks: Optional[list] = None


@router.post("/chat/document", response_model=DocumentChatResponse)
async def chat_with_document(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with a specific document using RAG

    Flow:
    0. Check the authenticated user owns the document (or is an admin), else 404
    1. Embed user's question
    2. Vector search for relevant chunks
    3. Build context from chunks
    4. Send to LLM with context
    5. Return AI response
    """
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    
    try:
        chat_request = DocumentChatRequest(**body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")

    require_document_access(db, chat_request.documentId, user)

    user_message = DocumentChatMessage(
        document_id=chat_request.documentId,
        user_id=user.id_str,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    db.commit()
    
    try:
        relevant_chunks = await vector_search_service.search_similar_chunks(
            query_text=chat_request.message,
            document_id=chat_request.documentId,
            db=db,
            top_k=10,
            similarity_threshold=0.3
        )
        
        context = vector_search_service.build_context(relevant_chunks)
        
        agent_response = await llm_service.chat_with_context(
            question=chat_request.message,
            context=context,
            max_tokens=350
        )
        
    except Exception as e:
        agent_response = f"Error processing request: {str(e)}"
    
    agent_message = DocumentChatMessage(
        document_id=chat_request.documentId,
        user_id=user.id_str,
        role="agent",
        content=agent_response
    )
    db.add(agent_message)
    db.commit()

    return DocumentChatResponse(
        response=agent_response,
        documentId=chat_request.documentId,
        userId=user.id_str,
        conversationId=f"{chat_request.documentId}_{user.id_str}",
        relevantChunks=[
            {
                "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                "similarity_score": chunk["similarity_score"],
                "chunk_index": chunk["chunk_index"]
            }
            for chunk in relevant_chunks
        ]
    )


@router.get("/document-chat/history")
async def get_document_chat_history(
    documentId: str,
    userId: Optional[str] = None,  # still sent by the UI; ignored
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the authenticated user's chat history for a document they can access
    """
    require_document_access(db, documentId, user)

    messages = db.query(DocumentChatMessage)\
        .filter(
            DocumentChatMessage.document_id == documentId,
            DocumentChatMessage.user_id == user.id_str
        )\
        .order_by(DocumentChatMessage.created_at.asc())\
        .all()

    return {
        "documentId": documentId,
        "userId": user.id_str,
        "conversationId": f"{documentId}_{user.id_str}",
        "messageCount": len(messages),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "createdAt": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }
