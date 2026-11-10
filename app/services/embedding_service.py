"""
Embedding Service
Generates vector embeddings using Ollama's nomic-embed-text model
"""
import httpx
from typing import List
from app.config import settings


class EmbeddingService:
    """Service for generating embeddings using Ollama"""
    
    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.embedding_dimensions = settings.EMBEDDING_DIMENSIONS
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_base_url}/api/embed",
                json={
                    "model": self.embedding_model,
                    "input": texts
                }
            )
            response.raise_for_status()
            
            data = response.json()
            embeddings = data.get("embeddings", [])
            
            if not embeddings:
                raise ValueError("Ollama did not return embeddings")
            
            for i, emb in enumerate(embeddings):
                if len(emb) != self.embedding_dimensions:
                    raise ValueError(
                        f"Expected {self.embedding_dimensions} dimensions, "
                        f"but got {len(emb)} for text {i}"
                    )
            
            return embeddings
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []


embedding_service = EmbeddingService()
