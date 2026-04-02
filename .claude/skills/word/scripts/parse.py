#!/usr/bin/env python3
"""Word document parser - Parse .docx/.dotm and extract structured facts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add libs path to sys.path
libs_path = Path(__file__).parent
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

libs_dir = Path(__file__).resolve().parent.parent.parent / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from docx_parser import parse_word_document
from utils import resolve_path, write_json_output


def main():
    parser = argparse.ArgumentParser(description="Parse .docx/.dotm and extract structured facts")
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--output", help="Where to write JSON facts (default: stdout)")
    args = parser.parse_args()

    input_path = resolve_path(args.input)
    payload = parse_word_document(input_path).to_dict()
    write_json_output(payload, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
