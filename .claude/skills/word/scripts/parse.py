#!/usr/bin/env python3
"""Word document parser - Parse .docx/.dotm and extract structured facts."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

# Add libs path to sys.path
libs_path = Path(__file__).parent
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

from docx_parser import parse_word_document


def resolve_path(path_str: str) -> str:
    """Resolve a path, supporting glob patterns."""
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str


def main():
    parser = argparse.ArgumentParser(description="Parse .docx/.dotm and extract structured facts")
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--output", help="Where to write JSON facts (default: stdout)")
    args = parser.parse_args()

    # Resolve path (support glob patterns)
    input_path = resolve_path(args.input)

    payload = parse_word_document(input_path).to_dict()

    if args.output:
        Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
