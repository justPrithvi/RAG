"""
Vector Search Service
Handles vector similarity search operations
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_service import embedding_service


class VectorSearchService:
    """Service for vector similarity search in document chunks"""
    
    async def search_similar_chunks(
        self,
        query_text: str,
        document_id: str,
        db: Session,
        top_k: int = 20,
        similarity_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Search for similar document chunks using vector similarity
        
        Args:
            query_text: User's query text
            document_id: Document to search in
            db: Database session
            top_k: Number of results to return (before filtering)
            similarity_threshold: Minimum similarity score (0-1) to include chunk
            
        Returns:
            List of matching chunks with metadata (filtered by threshold)
        """
        query_embeddings = await embedding_service.generate_embeddings([query_text])
        query_embedding = query_embeddings[0]
        
        query = text("""
            SELECT 
                id,
                document_id,
                chunk_index,
                content,
                chunk_metadata,
                1 - (embedding <=> :query_embedding) AS similarity_score
            FROM document_chunks
            WHERE document_id = :document_id
            ORDER BY embedding <=> :query_embedding
            LIMIT :top_k
        """)
        
        result = db.execute(
            query,
            {
                "query_embedding": str(query_embedding),
                "document_id": document_id,
                "top_k": top_k
            }
        )
        
        chunks = []
        for row in result.fetchall():
            similarity_score = float(row[5]) if row[5] else 0.0
            
            if similarity_score >= similarity_threshold:
                chunks.append({
                    "id": row[0],
                    "document_id": row[1],
                    "chunk_index": row[2],
                    "content": row[3],
                    "chunk_metadata": row[4],
                    "similarity_score": similarity_score
                })
        
        return chunks
    
    @staticmethod
    def build_context(chunks: List[Dict], include_scores: bool = False) -> str:
        """
        Build context string from document chunks
        
        Args:
            chunks: List of chunk dicts with 'content'
            include_scores: Whether to include similarity scores (for debugging)
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant context found."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            score_text = f" (Relevance: {chunk.get('similarity_score', 0):.2f})" if include_scores else ""
            context_parts.append(f"--- Excerpt {i}{score_text} ---")
            context_parts.append(chunk['content'])
            context_parts.append("")
        
        return "\n".join(context_parts)


vector_search_service = VectorSearchService()
