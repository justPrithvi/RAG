"""
Vector Database Utilities - SKELETON
This is where you'll implement vector storage and retrieval

Think of this like a database service in NestJS
"""


class VectorStore:
    """
    Manages vector storage and similarity search
    
    What is a Vector Database?
    - Stores embeddings (vectors) efficiently
    - Performs fast similarity search
    - Returns most relevant chunks based on query
    
    Popular options:
    - ChromaDB (local, easy to start)
    - Pinecone (cloud, scalable)
    - Weaviate, Qdrant, etc.
    """
    
    def __init__(self):
        """
        Initialize vector database connection
        
        TODO: Set up your chosen vector database
        Example with ChromaDB:
            import chromadb
            self.client = chromadb.Client()
            self.collection = self.client.create_collection("documents")
        """
        pass
    
    async def store_embeddings(
        self,
        document_id: str,
        chunks: list[str],
        embeddings: list[list[float]],
        metadata: dict = None
    ):
        """
        Store document chunks and their embeddings
        
        TODO: Implement storage logic
        
        Args:
            document_id: Unique ID for the document
            chunks: List of text chunks
            embeddings: Corresponding embeddings for each chunk
            metadata: Additional info (filename, upload date, etc.)
        """
        pass
    
    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5
    ) -> list[dict]:
        """
        Find most similar chunks to a query
        
        TODO: Implement similarity search
        
        Args:
            query_embedding: Embedding of the user's question
            top_k: Number of results to return
            
        Returns:
            List of matching chunks with metadata
            Example:
            [
                {
                    "chunk_id": "doc1_chunk_0",
                    "content": "Python is a programming language...",
                    "score": 0.92,  # similarity score
                    "metadata": {"document_id": "doc1", "filename": "intro.pdf"}
                },
                ...
            ]
        """
        # Placeholder
        return []
    
    async def delete_document(self, document_id: str):
        """
        Delete all chunks for a document
        
        TODO: Implement deletion
        """
        pass

