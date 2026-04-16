"""PDF engine for text and table extraction.

Migrated from .claude/skills/read-pdf/scripts/run.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_page_range(page_range_str: str, total_pages: int) -> list[int]:
    """Parse page range string like '1-5' or '1,3,5' into list of 0-based indices.

    Args:
        page_range_str: Page range string (e.g., "1-5", "1,3,5").
        total_pages: Total number of pages in the PDF.

    Returns:
        List of 0-based page indices.
    """
    pages = []
    for part in page_range_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = max(1, int(start))
            end = min(total_pages, int(end))
            pages.extend(range(start - 1, end))
        else:
            idx = int(part) - 1
            if 0 <= idx < total_pages:
                pages.append(idx)
    return sorted(set(pages))


def extract_text(pdf_path: str | Path, page_range: str | None = None) -> dict:
    """Extract text from PDF.

    Args:
        pdf_path: Path to PDF file.
        page_range: Optional page range string (e.g., "1-5").

    Returns:
        Dict with input, pages, full_text, and page_count.
    """
    import pdfplumber

    pdf_path = Path(pdf_path)
    result = {
        "input": pdf_path.name,
        "pages": [],
        "full_text": "",
    }

    with pdfplumber.open(pdf_path) as pdf:
        result["page_count"] = len(pdf.pages)
        page_indices = parse_page_range(page_range, len(pdf.pages)) if page_range else list(range(len(pdf.pages)))

        all_text = []
        for idx in page_indices:
            if idx >= len(pdf.pages):
                continue
            page = pdf.pages[idx]
            text = page.extract_text() or ""
            page_data = {
                "page_number": idx + 1,
                "width": round(float(page.width), 1),
                "height": round(float(page.height), 1),
                "text": text,
            }
            result["pages"].append(page_data)
            all_text.append(text)

        result["full_text"] = "\n\n".join(all_text)

    return result


def extract_tables(pdf_path: str | Path, page_range: str | None = None) -> dict:
    """Extract tables from PDF.

    Args:
        pdf_path: Path to PDF file.
        page_range: Optional page range string.

    Returns:
        Dict with input, pages, table_count, and page_count.
    """
    import pdfplumber

    pdf_path = Path(pdf_path)
    result = {
        "input": pdf_path.name,
        "pages": [],
        "table_count": 0,
    }

    with pdfplumber.open(pdf_path) as pdf:
        result["page_count"] = len(pdf.pages)
        page_indices = parse_page_range(page_range, len(pdf.pages)) if page_range else list(range(len(pdf.pages)))

        total_tables = 0
        for idx in page_indices:
            if idx >= len(pdf.pages):
                continue
            page = pdf.pages[idx]
            tables = page.extract_tables()
            if tables:
                result["pages"].append({
                    "page_number": idx + 1,
                    "tables": tables,
                })
                total_tables += len(tables)

        result["table_count"] = total_tables

    return result


def extract_all(pdf_path: str | Path, page_range: str | None = None) -> dict:
    """Full extraction: text + tables.

    Args:
        pdf_path: Path to PDF file.
        page_range: Optional page range string.

    Returns:
        Dict with input, pages, full_text, table_count, and page_count.
    """
    import pdfplumber

    pdf_path = Path(pdf_path)
    result = {
        "input": pdf_path.name,
        "pages": [],
        "full_text": "",
        "table_count": 0,
    }

    with pdfplumber.open(pdf_path) as pdf:
        result["page_count"] = len(pdf.pages)
        page_indices = parse_page_range(page_range, len(pdf.pages)) if page_range else list(range(len(pdf.pages)))

        all_text = []
        total_tables = 0
        for idx in page_indices:
            if idx >= len(pdf.pages):
                continue
            page = pdf.pages[idx]
            text = page.extract_text() or ""
            tables = page.extract_tables()

            page_data = {
                "page_number": idx + 1,
                "width": round(float(page.width), 1),
                "height": round(float(page.height), 1),
                "text": text,
            }
            if tables:
                page_data["tables"] = tables
                total_tables += len(tables)

            result["pages"].append(page_data)
            all_text.append(text)

        result["full_text"] = "\n\n".join(all_text)
        result["table_count"] = total_tables

    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def extract_pdf(
    pdf_path: str | Path,
    pages: str | None = None,
    extract_tables: bool = False,
    extract_all_content: bool = False,
) -> dict:
    """Extract content from PDF file.

    Args:
        pdf_path: Path to PDF file.
        pages: Page range string (e.g., "1-5").
        extract_tables: Extract tables only.
        extract_all_content: Full extraction (text + tables).

    Returns:
        Extraction result dict.

    Raises:
        FileNotFoundError: If PDF file does not exist.
        ValueError: If file is not a PDF.
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path}")

    if extract_tables:
        return extract_tables(pdf_path, pages)
    elif extract_all_content:
        return extract_all(pdf_path, pages)
    else:
        return extract_text(pdf_path, pages)