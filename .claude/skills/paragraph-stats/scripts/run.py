#!/usr/bin/env python3
"""Generic paragraph filtering and property distribution statistics."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import json
import re
import sys

libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from utils import load_facts, normalized, resolve_path, write_json_output


LATIN_RE = re.compile(r"[A-Za-z]")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def round_if_number(value):
    if isinstance(value, float):
        return round(value, 2)
    return value


def summarize_counter(counter: Counter, top_n: int = 5) -> list[dict]:
    return [{"value": v, "count": c} for v, c in counter.most_common(top_n)]


# ---------------------------------------------------------------------------
# Paragraph filtering (all criteria via parameters, no defaults)
# ---------------------------------------------------------------------------

def matches_filter(
    p: dict,
    style_hints: tuple[str, ...],
    exclude_texts: tuple[str, ...],
    heading_prefixes: tuple[str, ...],
    heading_keywords: tuple[str, ...],
    instruction_hints: tuple[str, ...],
    min_length: int,
    require_body_shape: bool,
) -> bool:
    text = (p.get("text") or "").strip()
    props = p.get("properties", {})

    if len(text) < min_length:
        return False

    if any(token in text for token in exclude_texts):
        return False

    if any(re.match(pat, text) for pat in heading_prefixes):
        return False
    if any(text.startswith(kw) for kw in heading_keywords):
        return False

    if instruction_hints:
        if "    " in text:
            return False
        if text.count("：") >= 2 and "。" not in text:
            return False
        if any(hint in text for hint in instruction_hints):
            return False

    # Body shape check
    has_body_shape = (
        props.get("alignment") == "justify"
        or (props.get("first_line_indent_pt") or 0) > 0
    )
    if require_body_shape and not has_body_shape:
        return False

    # Style filter: if style_hints provided, require match
    if style_hints:
        style = normalized(p.get("style_name"))
        if style not in style_hints:
            return False

    return True


# ---------------------------------------------------------------------------
# Statistics collection
# ---------------------------------------------------------------------------

def compute_stats(paragraphs: list[dict], sample_limit: int = 8) -> dict:
    font_sizes: Counter = Counter()
    line_spacings: Counter = Counter()
    indents: Counter = Counter()
    east_asia_fonts: Counter = Counter()
    ascii_fonts: Counter = Counter()
    styles: Counter = Counter()
    examples: list[dict] = []

    for p in paragraphs:
        props = p.get("properties", {})
        text = p.get("text", "")
        styles[p.get("style_name") or "(none)"] += 1

        font_size = props.get("font_size_pt")
        if font_size is not None:
            font_sizes[round_if_number(font_size)] += 1

        line_mode = props.get("line_spacing_mode")
        line_value = props.get("line_spacing_value")
        if line_mode is not None or line_value is not None:
            line_spacings[f"{line_mode}:{round_if_number(line_value)}"] += 1

        indent = props.get("first_line_indent_pt")
        if indent is not None:
            indents[round_if_number(indent)] += 1

        ea_font = props.get("font_family_east_asia")
        if ea_font and CJK_RE.search(text):
            east_asia_fonts[ea_font] += 1

        ascii_font = props.get("font_family_ascii")
        if ascii_font and LATIN_RE.search(text):
            ascii_fonts[ascii_font] += 1

        if len(examples) < sample_limit:
            examples.append({
                "paragraph_index": p.get("index"),
                "style_name": p.get("style_name"),
                "text_preview": text[:120],
                "properties": {
                    "font_size_pt": font_size,
                    "line_spacing_mode": line_mode,
                    "line_spacing_value": line_value,
                    "first_line_indent_pt": indent,
                    "font_family_east_asia": props.get("font_family_east_asia"),
                    "font_family_ascii": props.get("font_family_ascii"),
                },
            })

    return {
        "candidate_count": len(paragraphs),
        "style_distribution": summarize_counter(styles),
        "font_size_distribution": summarize_counter(font_sizes),
        "line_spacing_distribution": summarize_counter(line_spacings),
        "first_line_indent_distribution": summarize_counter(indents),
        "east_asia_font_distribution": summarize_counter(east_asia_fonts),
        "ascii_font_distribution": summarize_counter(ascii_fonts),
        "candidate_examples": examples,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Filter paragraphs by criteria and compute property distributions"
    )
    parser.add_argument("input", help="Path to facts.json or .docx/.dotm")
    parser.add_argument("--output", help="Where to write JSON result")
    parser.add_argument("--sample-limit", type=int, default=8, help="Max candidate examples")
    parser.add_argument("--style-hint", action="append", default=[], help="Style names to include (repeatable)")
    parser.add_argument("--exclude-text", action="append", default=[], help="Exclude paragraphs containing text (repeatable)")
    parser.add_argument("--heading-prefix", action="append", default=[], help="Regex for heading-like paragraphs to exclude (repeatable)")
    parser.add_argument("--heading-keyword", action="append", default=[], help="Keyword prefix for heading exclusion (repeatable)")
    parser.add_argument("--instruction-hint", action="append", default=[], help="Text hint for instruction-like exclusion (repeatable)")
    parser.add_argument("--min-length", type=int, default=0, help="Min paragraph text length")
    parser.add_argument("--require-body-shape", action="store_true", help="Only paragraphs with justify alignment or first-line indent")
    args = parser.parse_args()

    facts = load_facts(resolve_path(args.input), anchor_file=__file__)
    non_empty = [p for p in facts.get("paragraphs", []) if (p.get("text") or "").strip()]

    style_hints = tuple(normalized(s) for s in args.style_hint)
    candidates = [
        p for p in non_empty
        if matches_filter(
            p,
            style_hints=style_hints,
            exclude_texts=tuple(args.exclude_text),
            heading_prefixes=tuple(args.heading_prefix),
            heading_keywords=tuple(args.heading_keyword),
            instruction_hints=tuple(args.instruction_hint),
            min_length=args.min_length,
            require_body_shape=args.require_body_shape,
        )
    ]

    result = {
        "input": args.input,
        "filters": {
            "style_hints": list(style_hints),
            "exclude_texts": args.exclude_text,
            "heading_prefixes": args.heading_prefix,
            "heading_keywords": args.heading_keyword,
            "instruction_hints": args.instruction_hint,
            "min_length": args.min_length,
            "require_body_shape": args.require_body_shape,
        },
        "summary": compute_stats(candidates, sample_limit=args.sample_limit),
    }

    write_json_output(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
