#!/usr/bin/env python3
"""Query the parsed word document for paragraphs containing a keyword."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

libs_path = Path(__file__).parent
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

libs_dir = Path(__file__).resolve().parent.parent.parent / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from docx_parser import parse_word_document
from utils import resolve_path, write_json_output


def main():
    parser = argparse.ArgumentParser(description="Query document text")
    parser.add_argument("input", help="Path to .docx file")
    parser.add_argument("--keyword", required=True, help="Keyword to search for")
    args = parser.parse_args()

    facts = parse_word_document(resolve_path(args.input))
    results = []
    for p in facts.paragraphs:
        if args.keyword.lower() in p.text.lower():
            results.append({
                "index": p.index,
                "text": p.text,
                "style_name": p.style_name
            })
    write_json_output(results)


if __name__ == "__main__":
    main()
