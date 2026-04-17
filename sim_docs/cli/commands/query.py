"""Query commands - query-style and query-text."""

from __future__ import annotations

import argparse
import json
import sys

from sim_docs.api import word
from ._base import write_output


# query-style
NAME_STYLE = "query-style"
HELP_STYLE = "Query document style properties"


def add_parser_style(subparsers) -> None:
    parser = subparsers.add_parser(NAME_STYLE, help=HELP_STYLE)
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--style", required=True, help="Style name to query")
    parser.add_argument("--output", help="Output JSON file path")


def run_style(args) -> int:
    results = word.query_style(args.input, args.style)
    if not results:
        print(json.dumps({"error": f"Style containing '{args.style}' not found"}), file=sys.stderr)
        return 1
    output_data = [
        {"name": s.name, "style_id": s.style_id, "type": s.style_type, "properties": s.properties}
        for s in results
    ]
    write_output(output_data, args.output)
    return 0


# query-text
NAME_TEXT = "query-text"
HELP_TEXT = "Query paragraphs by keyword"


def add_parser_text(subparsers) -> None:
    parser = subparsers.add_parser(NAME_TEXT, help=HELP_TEXT)
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--keyword", required=True, help="Keyword to search")
    parser.add_argument("--output", help="Output JSON file path")


def run_text(args) -> int:
    results = word.query_text(args.input, args.keyword)
    output_data = [
        {"id": p.id, "index": p.index, "text": p.text, "style_name": p.style_name, "properties": p.properties}
        for p in results
    ]
    write_output(output_data, args.output)
    return 0