#!/usr/bin/env python3
"""Render a specific page of a Word document to an image for LLM visual analysis."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

libs_dir = Path(__file__).resolve().parent.parent.parent / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from utils import resolve_path

import fitz  # PyMuPDF


def convert_to_pdf(docx_path: str, outdir: str) -> str:
    """Uses libreoffice headless to convert .docx/.dotm to .pdf."""
    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", outdir,
        docx_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error converting document: {e.stderr.decode()}", file=sys.stderr)
        print("\nNote: Please ensure 'libreoffice-core' is installed on your system.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'libreoffice' command not found. Please install libreoffice.", file=sys.stderr)
        sys.exit(1)

    return str(Path(outdir) / (Path(docx_path).stem + ".pdf"))


def extract_page_as_image(pdf_path: str, page_num: int, out_path: str):
    """Uses PyMuPDF to extract a specific page to a png file."""
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}", file=sys.stderr)
        sys.exit(1)

    if page_num < 1 or page_num > len(doc):
        print(f"Error: Page {page_num} is out of bounds. The document has {len(doc)} pages.", file=sys.stderr)
        sys.exit(1)

    page = doc.load_page(page_num - 1)
    pix = page.get_pixmap(dpi=150)
    pix.save(out_path)
    print(f"Successfully rendered page {page_num} to '{out_path}' for visual inspection.")


def main():
    parser = argparse.ArgumentParser(description="Render a specific page of a Word document to an image via headless LibreOffice and PyMuPDF.")
    parser.add_argument("input", help="Path to .docx or .dotm file")
    parser.add_argument("--page", type=int, default=1, help="Page number to extract (1-indexed, default: 1)")
    parser.add_argument("--output", required=True, help="Output image file (e.g., page1.png)")
    args = parser.parse_args()

    input_path = resolve_path(args.input)
    if not Path(input_path).exists():
        print(f"File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = convert_to_pdf(input_path, tmpdir)
        extract_page_as_image(pdf_path, args.page, args.output)


if __name__ == "__main__":
    main()
