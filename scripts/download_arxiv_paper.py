#!/usr/bin/env python3
"""
Download research paper from arXiv.

Usage:
    python scripts/download_arxiv_paper.py <arxiv_id>

Example:
    python scripts/download_arxiv_paper.py 2403.11996
"""

import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Installing httpx package...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
    import httpx


def download_paper(arxiv_id: str, output_dir: Path = Path("data/papers")) -> Path:
    """Download paper from arXiv using direct PDF URL.

    Args:
        arxiv_id: arXiv ID (e.g., '2403.11996')
        output_dir: Directory to save PDF

    Returns:
        Path to downloaded PDF
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Remove version suffix if present (e.g., '2403.11996v3' -> '2403.11996')
    clean_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id

    # Construct arXiv PDF URL
    pdf_url = f"https://arxiv.org/pdf/{clean_id}.pdf"

    print(f"Downloading from: {pdf_url}")

    # Download PDF with proper headers
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    with httpx.Client(follow_redirects=True, timeout=60.0, headers=headers) as client:
        response = client.get(pdf_url)
        response.raise_for_status()

        # Save to file
        pdf_path = output_dir / f"{clean_id.replace('.', '_')}.pdf"

        with open(pdf_path, "wb") as f:
            f.write(response.content)

    file_size = pdf_path.stat().st_size / 1024 / 1024  # MB
    print(f"✓ Downloaded to: {pdf_path}")
    print(f"  File size: {file_size:.2f} MB")

    return pdf_path


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/download_arxiv_paper.py <arxiv_id>")
        print("\nExample:")
        print("  python scripts/download_arxiv_paper.py 2403.11996")
        print("\nThis will download the paper to data/papers/")
        sys.exit(1)

    arxiv_id = sys.argv[1]

    try:
        pdf_path = download_paper(arxiv_id)
        print(f"\n✓ Success! Paper downloaded to: {pdf_path}")
        print(f"\nTo extract knowledge graph, run:")
        print(f"  python examples/ingest_paper.py {pdf_path}")

    except Exception as e:
        print(f"\n✗ Error downloading paper: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
