#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


shared_word_scripts = Path(__file__).resolve().parents[2] / "word" / "scripts"
if str(shared_word_scripts) not in sys.path:
    sys.path.insert(0, str(shared_word_scripts))

libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from docx_parser import parse_word_document
from utils import resolve_path, write_json_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Query document text")
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--keyword", required=True, help="Keyword to search for")
    parser.add_argument("--output", help="Where to write JSON result")
    args = parser.parse_args()

    facts = parse_word_document(resolve_path(args.input))
    results = []
    for paragraph in facts.paragraphs:
        if args.keyword.lower() in paragraph.text.lower():
            results.append(
                {
                    "index": paragraph.index,
                    "text": paragraph.text,
                    "style_name": paragraph.style_name,
                }
            )

    write_json_output(results, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
