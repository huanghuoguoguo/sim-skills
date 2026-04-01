#!/usr/bin/env python3
"""Query the parsed word document for paragraphs containing a keyword."""

import argparse
import glob
import json
import sys
from pathlib import Path

libs_path = Path(__file__).parent
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

from docx_parser import parse_word_document

def resolve_path(path_str: str) -> str:
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str

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
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
