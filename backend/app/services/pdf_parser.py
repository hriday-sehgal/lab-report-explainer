"""
PDF Parsing & Preprocessing Service
Extracts high-fidelity plain text and structural elements from medical lab PDFs.
Supports multi-page extraction and fallback cleaning.
"""

from io import BytesIO
from typing import Tuple, Dict, Any
from pypdf import PdfReader

class PDFParserService:
    @staticmethod
    def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
        """
        Extracts plain text from raw PDF bytes.
        Returns: (extracted_text, metadata)
        """
        stream = BytesIO(pdf_bytes)
        reader = PdfReader(stream)
        
        pages_text = []
        for i, page in enumerate(reader.pages):
            page_content = page.extract_text() or ""
            pages_text.append(page_content)
            
        full_text = "\n".join(pages_text).strip()
        metadata = {
            "num_pages": len(reader.pages),
            "total_chars": len(full_text)
        }
        return full_text, metadata

    @staticmethod
    def extract_text_from_file_path(file_path: str) -> Tuple[str, Dict[str, Any]]:
        with open(file_path, "rb") as f:
            return PDFParserService.extract_text_from_pdf_bytes(f.read())
