from typing import Dict, Any
import re
import asyncio
from services.base import PDFConverter

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    DocumentConverter = None

class DoclingConverter(PDFConverter):
    """Converter implementation for docling library"""
    
    def __init__(self):
        self._converter = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization - only create DocumentConverter when actually needed"""
        if self._initialized:
            return
        
        if not DOCLING_AVAILABLE:
            raise RuntimeError("docling is not available")
        
        # Only initialize DocumentConverter when first used (lazy loading)
        # This prevents downloading models at startup
        self._converter = DocumentConverter()
        self._initialized = True
    
    @property
    def name(self) -> str:
        return "docling"
    
    @property
    def available(self) -> bool:
        return DOCLING_AVAILABLE
    
    async def convert_to_md(self, file_path: str) -> str:
        if not self.available:
            raise RuntimeError("docling is not available")
        self._ensure_initialized()
        # Run blocking operations in thread executor to avoid blocking the event loop
        result = await asyncio.to_thread(self._converter.convert, file_path)
        return result.document.export_to_markdown()
    
    async def convert_to_json(self, file_path: str) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError("docling is not available")
        self._ensure_initialized()
        md_content = await self.convert_to_md(file_path)
        return {
            "content": md_content,
            "format": "markdown",
            "library": self.name
        }
    
    async def convert_to_text(self, file_path: str) -> str:
        if not self.available:
            raise RuntimeError("docling is not available")
        self._ensure_initialized()
        md_content = await self.convert_to_md(file_path)
        text = re.sub(r'#+\s+', '', md_content)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        return text

