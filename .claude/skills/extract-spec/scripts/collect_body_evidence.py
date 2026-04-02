#!/usr/bin/env python3
"""Collect likely body-paragraph evidence from a template or thesis document."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import sys

libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from thesis_profiles import load_profile
from utils import resolve_path, setup_word_scripts_path, write_json_output

setup_word_scripts_path(__file__)
from docx_parser import parse_word_document


LATIN_RE = re.compile(r"[A-Za-z]")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def normalized(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", "", value).lower()


def looks_like_heading(text: str, heading_prefix_patterns: tuple[str, ...], heading_keywords: tuple[str, ...]) -> bool:
    compact = text.strip()
    if not compact:
        return False
    if any(re.match(pattern, compact) for pattern in heading_prefix_patterns):
        return True
    if any(compact.startswith(keyword) for keyword in heading_keywords):
        return True
    return False


def looks_like_cover_or_instruction(text: str, instruction_hints: tuple[str, ...]) -> bool:
    compact = text.strip()
    if "    " in text:
        return True
    if compact.count("：") >= 2 and "。" not in compact:
        return True
    if any(hint in compact for hint in instruction_hints):
        return True
    return False


def is_likely_body_paragraph(
    paragraph,
    body_style_hints: tuple[str, ...],
    heading_prefix_patterns: tuple[str, ...],
    heading_keywords: tuple[str, ...],
    instruction_hints: tuple[str, ...],
    exclude_text_hints: tuple[str, ...] = (),
) -> bool:
    text = (paragraph.text or "").strip()
    if len(text) < 20:
        return False
    if any(token in text for token in exclude_text_hints):
        return False
    if looks_like_heading(text, heading_prefix_patterns=heading_prefix_patterns, heading_keywords=heading_keywords):
        return False
    if looks_like_cover_or_instruction(text, instruction_hints=instruction_hints):
        return False

    style_name = normalized(paragraph.style_name)
    properties = paragraph.properties
    has_body_shape = (
        properties.get("alignment") == "justify"
        or (properties.get("first_line_indent_pt") or 0) > 0
    )

    if style_name in body_style_hints:
        return has_body_shape or style_name == "body text indent"

    if style_name == "normal" and len(text) >= 30 and has_body_shape and "。" in text:
        return True
    return False


def summarize_counter(counter: Counter, top_n: int = 5) -> list[dict]:
    return [
        {"value": value, "count": count}
        for value, count in counter.most_common(top_n)
    ]


def round_if_number(value):
    if isinstance(value, float):
        return round(value, 2)
    return value


def collect_body_evidence(
    path: str | Path,
    sample_limit: int = 8,
    exclude_text_hints: tuple[str, ...] = (),
    profile: dict | None = None,
) -> dict:
    profile = profile or load_profile()
    body_sampling = profile["extract_spec"]["body_sampling"]
    body_style_hints = tuple(normalized(item) for item in body_sampling.get("body_style_hints", []))
    heading_prefix_patterns = tuple(body_sampling.get("heading_prefix_patterns", []))
    heading_keywords = tuple(body_sampling.get("heading_keywords", []))
    instruction_hints = tuple(body_sampling.get("instruction_hints", []))

    facts = parse_word_document(path)
    candidates = [
        paragraph
        for paragraph in facts.paragraphs
        if is_likely_body_paragraph(
            paragraph,
            body_style_hints=body_style_hints,
            heading_prefix_patterns=heading_prefix_patterns,
            heading_keywords=heading_keywords,
            instruction_hints=instruction_hints,
            exclude_text_hints=exclude_text_hints,
        )
    ]

    font_sizes = Counter()
    line_spacings = Counter()
    indents = Counter()
    east_asia_fonts = Counter()
    ascii_fonts = Counter()
    styles = Counter()

    examples = []
    for paragraph in candidates:
        properties = paragraph.properties
        styles[paragraph.style_name or "(none)"] += 1

        font_size = properties.get("font_size_pt")
        if font_size is not None:
            font_sizes[round_if_number(font_size)] += 1

        line_mode = properties.get("line_spacing_mode")
        line_value = properties.get("line_spacing_value")
        if line_mode is not None or line_value is not None:
            line_spacings[f"{line_mode}:{round_if_number(line_value)}"] += 1

        indent = properties.get("first_line_indent_pt")
        if indent is not None:
            indents[round_if_number(indent)] += 1

        east_asia_font = properties.get("font_family_east_asia")
        if east_asia_font and CJK_RE.search(paragraph.text or ""):
            east_asia_fonts[east_asia_font] += 1

        ascii_font = properties.get("font_family_ascii")
        if ascii_font and LATIN_RE.search(paragraph.text or ""):
            ascii_fonts[ascii_font] += 1

        if len(examples) < sample_limit:
            examples.append(
                {
                    "paragraph_index": paragraph.index,
                    "style_name": paragraph.style_name,
                    "text_preview": paragraph.text[:120],
                    "properties": {
                        "font_size_pt": font_size,
                        "line_spacing_mode": line_mode,
                        "line_spacing_value": line_value,
                        "first_line_indent_pt": indent,
                        "font_family_east_asia": properties.get("font_family_east_asia"),
                        "font_family_ascii": properties.get("font_family_ascii"),
                    },
                    "property_sources": paragraph.property_sources,
                }
            )

    body_style_facts = []
    for style in facts.styles:
        if normalized(style.name) in body_style_hints:
            body_style_facts.append(
                {
                    "name": style.name,
                    "style_id": style.style_id,
                    "properties": style.properties,
                }
            )

    return {
        "document": str(path),
        "filters": {
            "exclude_text_hints": list(exclude_text_hints),
            "body_style_hints": list(body_style_hints),
            "heading_prefix_patterns": list(heading_prefix_patterns),
            "heading_keywords": list(heading_keywords),
            "instruction_hints": list(instruction_hints),
        },
        "summary": {
            "candidate_count": len(candidates),
            "style_distribution": summarize_counter(styles),
            "font_size_distribution": summarize_counter(font_sizes),
            "line_spacing_distribution": summarize_counter(line_spacings),
            "first_line_indent_distribution": summarize_counter(indents),
            "east_asia_font_distribution": summarize_counter(east_asia_fonts),
            "ascii_font_distribution": summarize_counter(ascii_fonts),
        },
        "body_style_facts": body_style_facts,
        "candidate_examples": examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect likely body-paragraph evidence from a Word document")
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--output", help="Where to write JSON evidence")
    parser.add_argument("--sample-limit", type=int, default=8, help="Maximum candidate examples to include")
    parser.add_argument("--profile-json", help="Optional JSON file overriding the default thesis profile")
    parser.add_argument(
        "--exclude-text-hint",
        action="append",
        default=[],
        help="Exclude candidate paragraphs containing this text hint; repeatable and intended to be passed by the Agent",
    )
    parser.add_argument("--body-style-hint", action="append", default=[], help="Additional body style hint; repeatable")
    parser.add_argument("--heading-prefix-pattern", action="append", default=[], help="Additional regex for heading-like paragraphs; repeatable")
    parser.add_argument("--heading-keyword", action="append", default=[], help="Additional heading keyword prefix; repeatable")
    parser.add_argument("--instruction-hint", action="append", default=[], help="Additional instruction-like text hint; repeatable")
    args = parser.parse_args()

    input_path = resolve_path(args.input)
    overrides = {
        "extract_spec": {
            "body_sampling": {},
        }
    }
    body_sampling_overrides = overrides["extract_spec"]["body_sampling"]
    if args.body_style_hint:
        body_sampling_overrides["body_style_hints"] = args.body_style_hint
    if args.heading_prefix_pattern:
        body_sampling_overrides["heading_prefix_patterns"] = args.heading_prefix_pattern
    if args.heading_keyword:
        body_sampling_overrides["heading_keywords"] = args.heading_keyword
    if args.instruction_hint:
        body_sampling_overrides["instruction_hints"] = args.instruction_hint
    profile = load_profile(args.profile_json, overrides=overrides)
    payload = collect_body_evidence(
        input_path,
        sample_limit=args.sample_limit,
        exclude_text_hints=tuple(args.exclude_text_hint),
        profile=profile,
    )
    write_json_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
