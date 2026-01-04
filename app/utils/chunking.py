"""
Text Chunking Utilities - SKELETON
This is where you'll implement text chunking logic

Think of this like a utility service in NestJS
"""


class TextChunker:
    """
    Chunks text into smaller pieces for embedding
    
    Why chunking?
    - LLMs and embeddings have token limits
    - Smaller chunks = more precise retrieval
    - Better for semantic search
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Args:
            chunk_size: How many characters per chunk
            chunk_overlap: How many characters overlap between chunks
                          (helps maintain context across boundaries)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def chunk_text(self, text: str) -> list[str]:
        """
        Main chunking method
        
        TODO: Implement chunking logic here
        Options to explore:
        1. Simple character-based splitting
        2. Sentence-aware splitting (better)
        3. Paragraph-aware splitting
        4. Use libraries like langchain's TextSplitter
        
        Returns:
            List of text chunks
        """
        # Placeholder implementation
        # For now, just return the whole text as one chunk
        return [text] if text else []

