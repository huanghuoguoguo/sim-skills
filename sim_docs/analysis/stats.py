"""Stats engine for paragraph filtering and property distribution computation.

Migrated from .claude/skills/paragraph-stats/scripts/run.py.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from sim_docs.core.helpers import normalized


LATIN_RE = re.compile(r"[A-Za-z]")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def round_if_number(value: Any) -> Any:
    """Round value if it's a float."""
    if isinstance(value, float):
        return round(value, 2)
    return value


def summarize_counter(counter: Counter, top_n: int = 5) -> list[dict]:
    """Summarize counter as list of value/count dicts."""
    return [{"value": v, "count": c} for v, c in counter.most_common(top_n)]


# ---------------------------------------------------------------------------
# Paragraph filtering
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
    """Check if paragraph matches all filter criteria.

    Args:
        p: Paragraph dict with text and properties.
        style_hints: Normalized style names to match (empty = all).
        exclude_texts: Text tokens to exclude.
        heading_prefixes: Regex patterns for heading exclusion.
        heading_keywords: Keywords that indicate headings.
        instruction_hints: Text hints for instruction-like exclusion.
        min_length: Minimum text length.
        require_body_shape: Require justify alignment or first-line indent.

    Returns:
        True if paragraph matches all criteria.
    """
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
# Statistics computation
# ---------------------------------------------------------------------------

def compute_stats(paragraphs: list[dict], sample_limit: int = 8) -> dict:
    """Compute property distributions from paragraphs.

    Args:
        paragraphs: List of paragraph dicts with properties.
        sample_limit: Max number of example paragraphs to include.

    Returns:
        Dict with distributions for font_size, line_spacing, indent, fonts,
        and candidate examples.
    """
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
# Main entry point
# ---------------------------------------------------------------------------

def filter_and_compute_stats(
    facts: dict,
    style_hints: list[str] | None = None,
    min_length: int = 0,
    require_body_shape: bool = False,
    exclude_texts: list[str] | None = None,
    heading_prefixes: list[str] | None = None,
    heading_keywords: list[str] | None = None,
    instruction_hints: list[str] | None = None,
    sample_limit: int = 8,
) -> dict:
    """Filter paragraphs and compute statistics.

    Args:
        facts: Document facts dict with paragraphs.
        style_hints: Style names to filter (normalized).
        min_length: Minimum paragraph text length.
        require_body_shape: Only paragraphs with justify/indent.
        exclude_texts: Exclude paragraphs containing these texts.
        heading_prefixes: Regex patterns for heading exclusion.
        heading_keywords: Keyword prefixes for heading exclusion.
        instruction_hints: Text hints for instruction exclusion.
        sample_limit: Max candidate examples.

    Returns:
        Dict with filters, summary, and stats.
    """
    non_empty = [p for p in facts.get("paragraphs", []) if (p.get("text") or "").strip()]

    style_hints_tuple = tuple(normalized(s) for s in style_hints or [])
    exclude_texts_tuple = tuple(exclude_texts or [])
    heading_prefixes_tuple = tuple(heading_prefixes or [])
    heading_keywords_tuple = tuple(heading_keywords or [])
    instruction_hints_tuple = tuple(instruction_hints or [])

    candidates = [
        p for p in non_empty
        if matches_filter(
            p,
            style_hints=style_hints_tuple,
            exclude_texts=exclude_texts_tuple,
            heading_prefixes=heading_prefixes_tuple,
            heading_keywords=heading_keywords_tuple,
            instruction_hints=instruction_hints_tuple,
            min_length=min_length,
            require_body_shape=require_body_shape,
        )
    ]

    return {
        "filters": {
            "style_hints": list(style_hints_tuple),
            "exclude_texts": exclude_texts or [],
            "heading_prefixes": heading_prefixes or [],
            "heading_keywords": heading_keywords or [],
            "instruction_hints": instruction_hints or [],
            "min_length": min_length,
            "require_body_shape": require_body_shape,
        },
        "summary": compute_stats(candidates, sample_limit=sample_limit),
    }