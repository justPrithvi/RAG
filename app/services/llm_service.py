"""
LLM Service
Handles all interactions with Ollama LLM
"""
import httpx
from typing import List, Dict, Optional
from app.config import settings


class LLMService:
    """Service for interacting with Ollama LLM"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        system_message: Optional[str] = None
    ) -> str:
        """
        Send messages to LLM and get response
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Response randomness (0-1)
            max_tokens: Maximum tokens to generate
            system_message: Optional system instruction
            
        Returns:
            LLM response text
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or settings.RESPONSE_TEMPERATURE,
                "num_predict": max_tokens or settings.MAX_RESPONSE_TOKENS,
                "stop": ["\n\n\n"]
            }
        }
        
        if system_message:
            payload["messages"].insert(0, {"role": "system", "content": system_message})
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("message", {}).get("content", "")
    
    async def chat_with_context(
        self,
        question: str,
        context: str,
        max_tokens: int = 350
    ) -> str:
        """
        Chat with document context (RAG)
        
        Args:
            question: User's question
            context: Document context
            max_tokens: Maximum response tokens
            
        Returns:
            LLM response
        """
        system_message = """You are a document Q&A assistant. Your ONLY job is to answer questions using the provided context.

CRITICAL RULES (DO NOT BREAK):
1. ONLY use information from the Context section below
2. DO NOT use your own knowledge or training data
3. If the answer is not in the context, respond: "The provided document does not contain information about this."
4. Quote or paraphrase directly from the context
5. Keep answers under 200 words, complete sentences only

EXAMPLE OF WRONG ANSWER:
Context: "The Vaisesika theory discussed vega (motion)."
Question: "What is vega?"
WRONG: "Vega is a general concept of movement found in many Indian philosophies including Ayurveda..." (using external knowledge)

EXAMPLE OF CORRECT ANSWER:
Context: "The Vaisesika theory discussed vega (motion)."
Question: "What is vega?"
CORRECT: "According to the Vaisesika theory in the context, vega refers to motion."

Remember: Extract from context, never invent."""
        
        user_prompt = f"""===== CONTEXT START =====
{context}
===== CONTEXT END =====

QUESTION: {question}

INSTRUCTION: Answer the question using ONLY the context above. Do not add external knowledge."""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat(messages, max_tokens=max_tokens)


llm_service = LLMService()
