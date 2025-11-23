"""ArXiv paper search functionality."""

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    import subprocess
    import sys

    print("Installing httpx...")
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
    import httpx

try:
    import feedparser
except ImportError:
    import subprocess
    import sys

    print("Installing feedparser...")
    subprocess.run([sys.executable, "-m", "pip", "install", "feedparser"], check=True)
    import feedparser


@dataclass
class ArxivPaper:
    """Represents an arXiv paper."""

    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published: datetime
    updated: datetime
    categories: list[str]
    pdf_url: str
    entry_url: str
    primary_category: str

    def __str__(self) -> str:
        """String representation."""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += f" et al. ({len(self.authors)} authors)"
        return (
            f"{self.arxiv_id}: {self.title}\n"
            f"  Authors: {authors_str}\n"
            f"  Published: {self.published.strftime('%Y-%m-%d')}\n"
            f"  Category: {self.primary_category}\n"
            f"  URL: {self.entry_url}"
        )


class ArxivSearcher:
    """Search for papers on arXiv."""

    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self):
        """Initialize arXiv searcher."""
        self.client = httpx.Client(timeout=30.0)

    def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        start: int = 0,
    ) -> list[ArxivPaper]:
        """Search arXiv for papers.

        Args:
            query: Search query (can use arXiv query syntax)
            max_results: Maximum number of results to return
            sort_by: Sort by 'relevance', 'lastUpdatedDate', or 'submittedDate'
            sort_order: 'ascending' or 'descending'
            start: Start index for pagination

        Returns:
            List of ArxivPaper objects

        Examples:
            # Simple keyword search
            search("quantum computing")

            # Field-specific search
            search("ti:neural AND cat:cs.AI")  # title contains "neural" in AI category

            # Author search
            search("au:Buehler")

            # Date range
            search("submittedDate:[202301010000 TO 202312312359]")
        """
        # Build query parameters
        params = {
            "search_query": query,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "start": start,
        }

        # Make request
        response = self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()

        # Parse feed
        feed = feedparser.parse(response.text)

        # Extract papers
        papers = []
        for entry in feed.entries:
            paper = self._parse_entry(entry)
            if paper:
                papers.append(paper)

        return papers

    def _parse_entry(self, entry: Any) -> ArxivPaper | None:
        """Parse feed entry into ArxivPaper.

        Args:
            entry: Feedparser entry object

        Returns:
            ArxivPaper or None if parsing fails
        """
        try:
            # Extract arXiv ID from entry id
            arxiv_id = entry.id.split("/abs/")[-1]

            # Parse authors
            authors = [author.name for author in entry.authors]

            # Parse dates
            published = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
            updated = datetime.strptime(entry.updated, "%Y-%m-%dT%H:%M:%SZ")

            # Parse categories
            categories = [tag.term for tag in entry.tags]
            primary_category = entry.arxiv_primary_category.get("term", categories[0])

            # Get PDF URL
            pdf_url = None
            for link in entry.links:
                if link.type == "application/pdf":
                    pdf_url = link.href
                    break

            if not pdf_url:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            return ArxivPaper(
                arxiv_id=arxiv_id,
                title=entry.title.replace("\n", " ").strip(),
                authors=authors,
                abstract=entry.summary.replace("\n", " ").strip(),
                published=published,
                updated=updated,
                categories=categories,
                pdf_url=pdf_url,
                entry_url=entry.id,
                primary_category=primary_category,
            )

        except Exception as e:
            print(f"Warning: Failed to parse entry: {e}")
            return None

    def download_paper(
        self, paper: ArxivPaper, output_dir: Path | str = "data/papers"
    ) -> Path:
        """Download paper PDF.

        Args:
            paper: ArxivPaper object
            output_dir: Directory to save PDF

        Returns:
            Path to downloaded PDF
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create filename from arXiv ID
        filename = f"{paper.arxiv_id.replace('/', '_').replace('.', '_')}.pdf"
        pdf_path = output_dir / filename

        # Skip if already exists
        if pdf_path.exists():
            print(f"  Already downloaded: {filename}")
            return pdf_path

        # Download with proper headers
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        print(f"  Downloading: {filename}")

        try:
            response = self.client.get(paper.pdf_url, headers=headers, follow_redirects=True)
            response.raise_for_status()

            with open(pdf_path, "wb") as f:
                f.write(response.content)

            file_size = pdf_path.stat().st_size / 1024 / 1024  # MB
            print(f"    ✓ Saved ({file_size:.2f} MB)")

            # Be nice to arXiv - rate limit
            time.sleep(3)

            return pdf_path

        except Exception as e:
            print(f"    ✗ Error downloading: {e}")
            raise

    def search_by_category(
        self, category: str, max_results: int = 10, recent_days: int | None = None
    ) -> list[ArxivPaper]:
        """Search papers in a specific category.

        Args:
            category: arXiv category (e.g., 'cs.AI', 'physics.comp-ph')
            max_results: Maximum results
            recent_days: If set, only return papers from last N days

        Returns:
            List of papers
        """
        query = f"cat:{category}"

        if recent_days:
            # Calculate date range
            from datetime import timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(days=recent_days)

            # Format for arXiv query
            start_str = start_date.strftime("%Y%m%d0000")
            end_str = end_date.strftime("%Y%m%d2359")

            query += f" AND submittedDate:[{start_str} TO {end_str}]"

        return self.search(query, max_results=max_results, sort_by="submittedDate")

    def search_by_author(self, author: str, max_results: int = 10) -> list[ArxivPaper]:
        """Search papers by author.

        Args:
            author: Author name
            max_results: Maximum results

        Returns:
            List of papers
        """
        query = f"au:{author}"
        return self.search(query, max_results=max_results)

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self) -> "ArxivSearcher":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()


def search_arxiv(query: str, max_results: int = 10) -> list[ArxivPaper]:
    """Quick helper to search arXiv.

    Args:
        query: Search query
        max_results: Maximum results

    Returns:
        List of papers
    """
    with ArxivSearcher() as searcher:
        return searcher.search(query, max_results=max_results)
