#!/usr/bin/env python3
"""Extract text, tables, and structure from PDF files.

Usage:
    python run.py <file.pdf> [options]

Options:
    --pages RANGE     Page range (e.g., "1-5", "1,3,5")
    --tables          Extract tables only
    --images          Convert pages to images
    --all             Full extraction (text + tables)
    --output PATH     Output JSON file path
    --output-dir DIR  Directory for image output (default: current dir)
"""

import argparse
import json
import sys
from pathlib import Path

# Resolve shared libs
libs_path = Path(__file__).parent.parent.parent / "__libs__"
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

from utils import resolve_path, write_json_output


def parse_page_range(page_range_str: str, total_pages: int) -> list[int]:
    """Parse page range string like '1-5' or '1,3,5' into list of 0-based indices."""
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


def extract_text(pdf_path: str, page_range: str | None = None) -> dict:
    """Extract text and optionally tables from PDF."""
    import pdfplumber

    result = {
        "input": Path(pdf_path).name,
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


def extract_tables(pdf_path: str, page_range: str | None = None) -> dict:
    """Extract tables from PDF."""
    import pdfplumber

    result = {
        "input": Path(pdf_path).name,
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


def convert_to_images(pdf_path: str, output_dir: str, page_range: str | None = None, dpi: int = 150) -> dict:
    """Convert PDF pages to images."""
    from pdf2image import convert_from_path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    first_page = None
    last_page = None
    if page_range is not None:
        # pdf2image uses 1-based page numbers; parse_page_range needs total_pages
        # but we don't have it without opening the PDF. Use a large upper bound.
        page_indices = parse_page_range(page_range, 999999)
        if page_indices:
            first_page = min(page_indices) + 1
            last_page = max(page_indices) + 1

    images = convert_from_path(
        pdf_path,
        dpi=dpi,
        first_page=first_page,
        last_page=last_page,
    )

    saved = []
    for i, img in enumerate(images):
        page_num = (first_page or 1) + i
        img_path = output_path / f"page_{page_num}.png"
        img.save(str(img_path), "PNG")
        saved.append(str(img_path))

    return {
        "input": Path(pdf_path).name,
        "images": saved,
        "count": len(saved),
    }


def extract_all(pdf_path: str, page_range: str | None = None) -> dict:
    """Full extraction: text + tables."""
    import pdfplumber

    result = {
        "input": Path(pdf_path).name,
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


def main():
    parser = argparse.ArgumentParser(description="Extract content from PDF files")
    parser.add_argument("file", help="PDF file path")
    parser.add_argument("--pages", help="Page range (e.g., '1-5', '1,3,5')")
    parser.add_argument("--tables", action="store_true", help="Extract tables only")
    parser.add_argument("--images", action="store_true", help="Convert pages to images")
    parser.add_argument("--all", action="store_true", help="Full extraction (text + tables)")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--output-dir", default=".", help="Directory for image output")
    parser.add_argument("--dpi", type=int, default=150, help="Image resolution (default: 150)")
    args = parser.parse_args()

    pdf_path = resolve_path(args.file)
    if not Path(pdf_path).exists():
        print(json.dumps({"error": f"File not found: {args.file}"}))
        sys.exit(1)

    if not pdf_path.lower().endswith(".pdf"):
        print(json.dumps({"error": f"Not a PDF file: {args.file}"}))
        sys.exit(1)

    # Parse page range (deferred — extraction functions resolve it internally)
    page_range = args.pages  # raw string, resolved inside extraction with the already-open PDF

    # Execute requested operation
    if args.images:
        result = convert_to_images(pdf_path, args.output_dir, page_range, args.dpi)
    elif args.tables:
        result = extract_tables(pdf_path, page_range)
    elif args.all:
        result = extract_all(pdf_path, page_range)
    else:
        result = extract_text(pdf_path, page_range)

    write_json_output(result, args.output)


if __name__ == "__main__":
    main()
