"""Read commands - read-text and read-pdf."""

from __future__ import annotations

import argparse

from sim_docs.api import pdf, text
from ._base import write_output


# read-text
NAME_TEXT = "read-text"
HELP_TEXT = "Read text from .txt/.md/.docx"


def add_parser_text(subparsers) -> None:
    parser = subparsers.add_parser(NAME_TEXT, help=HELP_TEXT)
    parser.add_argument("input", help="Path to text file")
    parser.add_argument("--output", help="Output JSON file path")


def run_text(args) -> int:
    result = text.read(args.input)
    write_output(result, args.output)
    return 0


# read-pdf
NAME_PDF = "read-pdf"
HELP_PDF = "Extract content from PDF"


def add_parser_pdf(subparsers) -> None:
    parser = subparsers.add_parser(NAME_PDF, help=HELP_PDF)
    parser.add_argument("input", help="Path to PDF file")
    parser.add_argument("--pages", help="Page range (e.g., '1-5')")
    parser.add_argument("--tables", action="store_true", help="Extract tables only")
    parser.add_argument("--all", action="store_true", help="Full extraction (text + tables)")
    parser.add_argument("--output", help="Output JSON file path")


def run_pdf(args) -> int:
    result = pdf.extract(args.input, pages=args.pages, include_tables=args.tables, extract_all=args.all)
    write_output(result, args.output)
    return 0