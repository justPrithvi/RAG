"""
Text Cleaning Utilities
Cleans and normalizes text for RAG processing
"""
import re


class TextCleaner:
    """
    Cleans extracted text from documents
    Removes unwanted characters, normalizes whitespace, etc.
    """
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text
        
        Steps:
        1. Remove excessive line breaks
        2. Normalize whitespace
        3. Remove special characters (optional)
        4. Remove extra spaces
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove null bytes and other control characters
        text = text.replace('\x00', '')
        
        # Replace multiple line breaks with double line break
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        
        # Remove carriage returns
        text = text.replace('\r', '')
        
        # Remove excessive whitespace around line breaks
        text = re.sub(r' *\n *', '\n', text)
        
        # Trim leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_for_chunking(text: str) -> str:
        """
        Clean text specifically for chunking
        Preserves paragraph structure but removes noise
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text ready for chunking
        """
        # First do basic cleaning
        text = TextCleaner.clean_text(text)
        
        # Keep only single line breaks between paragraphs
        # This helps with semantic chunking
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'[\uf0b7\u2022\u2023\u2043]', '', text)  # Remove bullet points
        text = re.sub(r'[^\x00-\x7F\n]+', ' ', text)  # Remove non-ASCII except newlines (optional)
        
        # Remove page numbers at the start of lines (e.g., "Page 1", "1", etc.)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Page \d+\s*$', '', text, flags=re.MULTILINE)
        
        # Final cleanup
        text = re.sub(r' {2,}', ' ', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def remove_headers_footers(text: str, header_lines: int = 2, footer_lines: int = 2) -> str:
        """
        Remove common headers and footers from text
        Useful for PDF documents with repeated headers/footers
        
        Args:
            text: Text to clean
            header_lines: Number of header lines to remove
            footer_lines: Number of footer lines to remove
            
        Returns:
            Text without headers/footers
        """
        lines = text.split('\n')
        
        # Remove header lines
        if len(lines) > header_lines:
            lines = lines[header_lines:]
        
        # Remove footer lines
        if len(lines) > footer_lines:
            lines = lines[:-footer_lines]
        
        return '\n'.join(lines)

