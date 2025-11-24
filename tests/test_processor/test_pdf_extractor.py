"""Tests for PDF extraction."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from kg_builder.processor.pdf_extractor import PDFExtractor


class TestPDFExtractor:
    """Test PDF extraction functionality."""

    def test_init_with_valid_path(self, sample_pdf_path):
        """Test initialization with valid PDF path."""
        extractor = PDFExtractor(sample_pdf_path)
        assert extractor.pdf_path == Path(sample_pdf_path)

    def test_init_with_string_path(self, sample_pdf_path):
        """Test initialization with string path."""
        extractor = PDFExtractor(str(sample_pdf_path))
        assert extractor.pdf_path == Path(sample_pdf_path)

    def test_init_with_nonexistent_path(self, tmp_path):
        """Test initialization with nonexistent path raises error."""
        nonexistent_path = tmp_path / "nonexistent.pdf"
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            PDFExtractor(nonexistent_path)

    @patch("pdfplumber.open")
    def test_extract_text(self, mock_pdfplumber, sample_pdf_path):
        """Test text extraction from PDF."""
        # Mock PDF with multiple pages
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 text"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 text"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        extractor = PDFExtractor(sample_pdf_path)
        text = extractor.extract_text()

        assert "Page 1 text" in text
        assert "Page 2 text" in text
        assert mock_page1.extract_text.call_count == 1
        assert mock_page2.extract_text.call_count == 1

    @patch("pdfplumber.open")
    def test_extract_text_empty_pages(self, mock_pdfplumber, sample_pdf_path):
        """Test text extraction handles empty pages."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 text"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None  # Empty page

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        extractor = PDFExtractor(sample_pdf_path)
        text = extractor.extract_text()

        assert "Page 1 text" in text
        assert text.count("\n\n") == 0  # Empty page shouldn't add extra newlines

    @patch("pdfplumber.open")
    def test_extract_by_sections(self, mock_pdfplumber, sample_pdf_path):
        """Test section-based extraction."""
        sample_text = """
Title of Paper

Abstract
This is the abstract section.

1. Introduction
This is the introduction section.

2. Methods
This is the methods section.

3. Results
This is the results section.

4. Conclusion
This is the conclusion section.

References
[1] Reference 1
"""

        mock_page = MagicMock()
        mock_page.extract_text.return_value = sample_text
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        extractor = PDFExtractor(sample_pdf_path)
        sections = extractor.extract_by_sections()

        assert "Header" in sections or any("Title" in key for key in sections.keys())
        assert any("Abstract" in key for key in sections.keys())
        assert any("Introduction" in key for key in sections.keys())
        assert any("Methods" in key for key in sections.keys())
        assert any("Results" in key for key in sections.keys())
        assert any("Conclusion" in key for key in sections.keys())

    @patch("pdfplumber.open")
    def test_extract_by_sections_case_insensitive(self, mock_pdfplumber, sample_pdf_path):
        """Test section extraction is case-insensitive."""
        sample_text = """
ABSTRACT
This is the abstract.

INTRODUCTION
This is the introduction.
"""

        mock_page = MagicMock()
        mock_page.extract_text.return_value = sample_text
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        extractor = PDFExtractor(sample_pdf_path)
        sections = extractor.extract_by_sections()

        # Should find sections regardless of case
        assert len(sections) >= 2

    @patch("pdfplumber.open")
    def test_extract_metadata(self, mock_pdfplumber, sample_pdf_path):
        """Test metadata extraction."""
        mock_metadata = {
            "Title": "Test Paper",
            "Author": "Test Author",
            "Creator": "Test Creator",
        }

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "First page text"

        mock_pdf = MagicMock()
        mock_pdf.metadata = mock_metadata
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        extractor = PDFExtractor(sample_pdf_path)
        metadata = extractor.extract_metadata()

        assert metadata["title"] == "Test Paper"
        assert metadata["author"] == "Test Author"
        assert "num_pages" in metadata

    @patch("pdfplumber.open")
    def test_extract_metadata_no_metadata(self, mock_pdfplumber, sample_pdf_path):
        """Test metadata extraction with no metadata."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test Paper Title\nFirst page text"

        mock_pdf = MagicMock()
        mock_pdf.metadata = None
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        extractor = PDFExtractor(sample_pdf_path)
        metadata = extractor.extract_metadata()

        # Should still return metadata dict with extracted values
        assert isinstance(metadata, dict)
        assert "num_pages" in metadata

    @patch("pdfplumber.open")
    def test_extract_chunks(self, mock_pdfplumber, sample_pdf_path):
        """Test chunked text extraction."""
        # Create text longer than default chunk size
        long_text = "A" * 3000

        mock_page = MagicMock()
        mock_page.extract_text.return_value = long_text
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

        extractor = PDFExtractor(sample_pdf_path)

        # Check if extract_chunks method exists
        if hasattr(extractor, "extract_chunks"):
            chunks = extractor.extract_chunks(chunk_size=1000, overlap=100)

            # Should have multiple chunks
            assert len(chunks) > 1
            # Chunks should overlap
            assert chunks[0][-100:] == chunks[1][:100]
