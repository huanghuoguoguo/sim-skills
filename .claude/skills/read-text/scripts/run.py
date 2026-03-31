#!/usr/bin/env python3
"""read-text skill - Read text from .txt/.md/.docx files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add libs path to sys.path
libs_path = Path(__file__).parent.parent.parent / "__libs__"
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

from text_sources import read_text_source


def main():
    parser = argparse.ArgumentParser(description="Read text from .txt/.md/.docx files")
    parser.add_argument("input", help="Path to .txt/.md/.docx file")
    parser.add_argument("--output", help="Where to write JSON payload (default: stdout)")
    args = parser.parse_args()

    text = read_text_source(args.input)
    payload = {
        "input": args.input,
        "text": text,
        "line_count": len(text.splitlines()),
    }

    if args.output:
        Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
