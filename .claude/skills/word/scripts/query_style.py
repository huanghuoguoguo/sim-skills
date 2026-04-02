#!/usr/bin/env python3
"""Query the parsed word document for style properties."""

from __future__ import annotations

import argparse
import json
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
    parser = argparse.ArgumentParser(description="Query document style")
    parser.add_argument("input", help="Path to .docx file")
    parser.add_argument("--style", required=True, help="Style name to query")
    args = parser.parse_args()

    facts = parse_word_document(resolve_path(args.input))
    results = []
    for s in facts.styles:
        if args.style.lower() in (s.name or "").lower():
            results.append({
                "name": s.name,
                "style_id": s.style_id,
                "type": s.style_type,
                "properties": s.properties
            })

    if not results:
        print(json.dumps({"error": f"Style containing '{args.style}' not found"}), file=sys.stderr)
        return 1

    write_json_output(results)
    return 0

if __name__ == "__main__":
    sys.exit(main())
