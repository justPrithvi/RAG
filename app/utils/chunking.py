"""
Text Chunking Utilities
"""
import re


class TextChunker:
    """
    Chunks text into smaller pieces for embedding
    
    Strategy:
    - Split by paragraphs first (maintains semantic boundaries)
    - If paragraph is too large, split by sentences
    - Maintain overlap between chunks for context
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def chunk_text(self, text: str) -> list[str]:
        """Smart text chunking with sentence awareness"""
        if not text or not text.strip():
            return []
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                if len(paragraph) > self.chunk_size:
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
        
        if current_chunk:
            chunks.append(current_chunk)
        
        if self.chunk_overlap > 0 and len(chunks) > 1:
            chunks = self._add_overlap(chunks)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences using regex"""
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _add_overlap(self, chunks: list[str]) -> list[str]:
        """Add overlap between consecutive chunks"""
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
            overlapped_chunks.append(overlap_text + " " + chunks[i])
        
        return overlapped_chunks
    
    def get_chunk_count(self, text: str) -> int:
        """Estimate how many chunks will be created"""
        if not text:
            return 0
        return max(1, len(text) // self.chunk_size)
    
    async def chunk_text_token_based(
        self, 
        text: str, 
        max_tokens: int = 512,
        overlap_sentences: int = 1
    ) -> list[str]:
        """
        Token-based chunking with paragraph/sentence awareness
        
        Strategy:
        1. Try to fit complete paragraphs within token limit
        2. If paragraph exceeds limit, split by sentences
        3. If sentence exceeds limit, split by words (recursive fallback)
        4. Optional: Include last N sentences from previous chunk for context
        
        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk (default: 512)
            overlap_sentences: Number of sentences to overlap between chunks (0 = no overlap)
        
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        CHARS_PER_TOKEN = 4
        max_chars = max_tokens * CHARS_PER_TOKEN
        
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk_sentences = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            paragraph_token_estimate = len(paragraph) // CHARS_PER_TOKEN
            
            if paragraph_token_estimate <= max_tokens:
                current_size = sum(len(s) for s in current_chunk_sentences)
                
                if current_size + len(paragraph) + 2 <= max_chars:
                    current_chunk_sentences.append(paragraph)
                else:
                    if current_chunk_sentences:
                        chunks.append('\n\n'.join(current_chunk_sentences))
                    current_chunk_sentences = [paragraph]
            else:
                if current_chunk_sentences:
                    chunks.append('\n\n'.join(current_chunk_sentences))
                    current_chunk_sentences = []
                
                sentences = self._split_into_sentences(paragraph)
                
                for sentence in sentences:
                    sentence_token_estimate = len(sentence) // CHARS_PER_TOKEN
                    
                    if sentence_token_estimate <= max_tokens:
                        current_size = sum(len(s) for s in current_chunk_sentences)
                        
                        if current_size + len(sentence) + 1 <= max_chars:
                            current_chunk_sentences.append(sentence)
                        else:
                            if current_chunk_sentences:
                                chunks.append(' '.join(current_chunk_sentences))
                            current_chunk_sentences = [sentence]
                    else:
                        if current_chunk_sentences:
                            chunks.append(' '.join(current_chunk_sentences))
                            current_chunk_sentences = []
                        
                        word_chunks = self._split_long_sentence(sentence, max_chars)
                        chunks.extend(word_chunks[:-1])
                        if word_chunks:
                            current_chunk_sentences = [word_chunks[-1]]
        
        if current_chunk_sentences:
            chunks.append(' '.join(current_chunk_sentences))
        
        if overlap_sentences > 0 and len(chunks) > 1:
            chunks = self._add_sentence_overlap(chunks, overlap_sentences)
        
        return chunks
    
    def _split_long_sentence(self, sentence: str, max_chars: int) -> list[str]:
        """
        Recursive fallback: Split a very long sentence by words
        This handles edge cases where a single sentence exceeds token limit
        """
        words = sentence.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1
            
            if current_length + word_length <= max_chars:
                current_chunk.append(word)
                current_length += word_length
            else:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [sentence]
    
    def _add_sentence_overlap(self, chunks: list[str], overlap_sentences: int) -> list[str]:
        """
        Add overlap between chunks by including last N sentences from previous chunk
        This maintains context continuity without arbitrary character cutoffs
        """
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            prev_sentences = self._split_into_sentences(prev_chunk)
            
            overlap_text = ' '.join(prev_sentences[-overlap_sentences:]) if len(prev_sentences) >= overlap_sentences else prev_chunk
            
            overlapped_chunks.append(overlap_text + ' ' + chunks[i])
        
        return overlapped_chunks
