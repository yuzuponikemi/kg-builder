"""PDF text extraction module."""

import re
from pathlib import Path
from typing import Any

import pdfplumber


class PDFExtractor:
    """Extract text and metadata from PDF files."""

    def __init__(self, pdf_path: str | Path):
        """Initialize PDF extractor.

        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    def extract_text(self) -> str:
        """Extract all text from PDF.

        Returns:
            Extracted text
        """
        text_parts = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        return "\n\n".join(text_parts)

    def extract_by_sections(self) -> dict[str, str]:
        """Extract text organized by sections.

        Returns:
            Dictionary mapping section names to their content
        """
        full_text = self.extract_text()

        # Common section headers in scientific papers
        section_patterns = [
            r"\n\s*(Abstract|ABSTRACT)\s*\n",
            r"\n\s*(\d+\.?\s*Introduction|INTRODUCTION)\s*\n",
            r"\n\s*(\d+\.?\s*Methods?|METHODS?|Methodology|METHODOLOGY)\s*\n",
            r"\n\s*(\d+\.?\s*Results?|RESULTS?)\s*\n",
            r"\n\s*(\d+\.?\s*Discussion|DISCUSSION)\s*\n",
            r"\n\s*(\d+\.?\s*Conclusion|CONCLUSION)\s*\n",
            r"\n\s*(\d+\.?\s*References?|REFERENCES?)\s*\n",
        ]

        sections: dict[str, str] = {}
        current_section = "Header"
        current_text = []

        lines = full_text.split("\n")

        for line in lines:
            # Check if line is a section header
            is_section_header = False
            for pattern in section_patterns:
                if re.search(pattern, "\n" + line + "\n", re.IGNORECASE):
                    # Save previous section
                    if current_text:
                        sections[current_section] = "\n".join(current_text).strip()

                    # Start new section
                    current_section = line.strip()
                    current_text = []
                    is_section_header = True
                    break

            if not is_section_header:
                current_text.append(line)

        # Save last section
        if current_text:
            sections[current_section] = "\n".join(current_text).strip()

        return sections

    def extract_metadata(self) -> dict[str, Any]:
        """Extract PDF metadata.

        Returns:
            Dictionary with metadata fields
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            metadata = pdf.metadata or {}

            # Try to extract title from first page
            title = metadata.get("Title", "")
            if not title and pdf.pages:
                first_page_text = pdf.pages[0].extract_text() or ""
                # First non-empty line is often the title
                lines = [line.strip() for line in first_page_text.split("\n") if line.strip()]
                if lines:
                    title = lines[0]

            return {
                "title": title,
                "author": metadata.get("Author", ""),
                "subject": metadata.get("Subject", ""),
                "creator": metadata.get("Creator", ""),
                "producer": metadata.get("Producer", ""),
                "creation_date": metadata.get("CreationDate", ""),
                "modification_date": metadata.get("ModDate", ""),
                "num_pages": len(pdf.pages),
                "file_size": self.pdf_path.stat().st_size,
            }

    def extract_chunks(self, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
        """Extract text in overlapping chunks for processing.

        Args:
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        full_text = self.extract_text()
        chunks = []

        start = 0
        while start < len(full_text):
            end = start + chunk_size
            chunk = full_text[start:end]

            # Try to break at sentence boundaries
            if end < len(full_text):
                # Find last period in chunk
                last_period = chunk.rfind(". ")
                if last_period > chunk_size // 2:  # Only break if period is in second half
                    chunk = chunk[: last_period + 1]
                    end = start + last_period + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Quick helper to extract text from PDF.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text
    """
    extractor = PDFExtractor(pdf_path)
    return extractor.extract_text()
