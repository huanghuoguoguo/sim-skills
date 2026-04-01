#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
import sys


legacy_dir = Path(__file__).resolve().parents[2] / "word" / "scripts"
if str(legacy_dir) not in sys.path:
    sys.path.insert(0, str(legacy_dir))

from docx_parser import parse_word_document


ALIGNMENT_MAP = {
    0: "left",
    1: "center",
    2: "right",
    3: "justify",
}

EMU_PER_PT = 12700


def resolve_path(path_str: str) -> str:
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str


def to_points(value):
    if not isinstance(value, (int, float)):
        return value
    return round(value / EMU_PER_PT, 2)


def normalize_properties(properties: dict) -> dict:
    normalized = dict(properties)

    alignment = normalized.get("alignment")
    if alignment in ALIGNMENT_MAP:
        normalized["alignment"] = ALIGNMENT_MAP[alignment]

    if "space_before" in normalized:
        normalized["space_before_pt"] = to_points(normalized["space_before"])
    if "space_after" in normalized:
        normalized["space_after_pt"] = to_points(normalized["space_after"])
    if "first_line_indent" in normalized:
        normalized["first_line_indent_pt"] = to_points(normalized["first_line_indent"])
    if "line_spacing" in normalized:
        normalized["line_spacing_pt"] = to_points(normalized["line_spacing"])
    if "font_family" in normalized and "font_family_zh" not in normalized:
        normalized["font_family_zh"] = normalized["font_family"]

    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="Query document style with normalized properties")
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--style", required=True, help="Style name to query")
    parser.add_argument("--output", help="Where to write JSON result")
    args = parser.parse_args()

    facts = parse_word_document(resolve_path(args.input))
    results = []
    for style in facts.styles:
        if args.style.lower() in (style.name or "").lower():
            results.append(
                {
                    "name": style.name,
                    "style_id": style.style_id,
                    "type": style.style_type,
                    "properties": normalize_properties(style.properties),
                    "raw_properties": style.properties,
                }
            )

    if not results:
        print(json.dumps({"error": f"Style containing '{args.style}' not found"}), file=sys.stderr)
        return 1

    payload = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
