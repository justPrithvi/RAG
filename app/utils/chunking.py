"""
Text Chunking Utilities
Implements text chunking logic for RAG processing

Think of this like a utility service in NestJS
"""
import re


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
        Smart text chunking with sentence awareness
        
        Strategy:
        1. Split by paragraphs first (maintains semantic boundaries)
        2. If paragraph is too large, split by sentences
        3. Maintain overlap between chunks for context
        
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph keeps us under limit, add it
            if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Current chunk is full, save it
                if current_chunk:
                    chunks.append(current_chunk)
                
                # If paragraph itself is too large, split it
                if len(paragraph) > self.chunk_size:
                    # Split by sentences
                    sentences = self._split_into_sentences(paragraph)
                    current_chunk = ""
                    
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                            if current_chunk:
                                current_chunk += " " + sentence
                            else:
                                current_chunk = sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sentence
                else:
                    current_chunk = paragraph
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # Add overlap between chunks for context
        if self.chunk_overlap > 0 and len(chunks) > 1:
            chunks = self._add_overlap(chunks)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences
        Simple implementation using regex
        """
        # Split on . ! ? followed by space and capital letter or end of string
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _add_overlap(self, chunks: list[str]) -> list[str]:
        """
        Add overlap between consecutive chunks
        Takes the last N characters from previous chunk and prepends to next
        """
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            # Get overlap from previous chunk
            prev_chunk = chunks[i - 1]
            overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
            
            # Prepend overlap to current chunk
            overlapped_chunks.append(overlap_text + " " + chunks[i])
        
        return overlapped_chunks
    
    def get_chunk_count(self, text: str) -> int:
        """
        Estimate how many chunks will be created
        Useful for showing progress
        """
        if not text:
            return 0
        return max(1, len(text) // self.chunk_size)

