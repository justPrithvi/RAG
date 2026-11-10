"""
Text Cleaning Utilities
"""
import re


class TextCleaner:
    """Cleans extracted text from documents"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text
        - Removes control characters
        - Normalizes whitespace
        - Removes excessive line breaks
        """
        if not text:
            return ""
        
        text = text.replace('\x00', '')
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = text.replace('\t', ' ')
        text = text.replace('\r', '')
        text = re.sub(r' *\n *', '\n', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_for_chunking(text: str) -> str:
        """
        Clean text for chunking
        Preserves paragraph structure but removes noise
        """
        text = TextCleaner.clean_text(text)
        text = re.sub(r'\n\n+', '\n\n', text)
        text = re.sub(r'[\uf0b7\u2022\u2023\u2043]', '', text)
        text = re.sub(r'[^\x00-\x7F\n]+', ' ', text)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^Page \d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r' {2,}', ' ', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def remove_headers_footers(text: str, header_lines: int = 2, footer_lines: int = 2) -> str:
        """Remove common headers and footers from text"""
        lines = text.split('\n')
        
        if len(lines) > header_lines:
            lines = lines[header_lines:]
        
        if len(lines) > footer_lines:
            lines = lines[:-footer_lines]
        
        return '\n'.join(lines)
