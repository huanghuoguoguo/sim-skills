#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
import sys


shared_word_scripts = Path(__file__).resolve().parents[2] / "word" / "scripts"
if str(shared_word_scripts) not in sys.path:
    sys.path.insert(0, str(shared_word_scripts))

from docx_parser import parse_word_document


def resolve_path(path_str: str) -> str:
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str


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

    payload = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
