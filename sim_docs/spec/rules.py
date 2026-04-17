"""Shared helpers for thesis spec parsing and validation."""

from __future__ import annotations

import re


FONT_SIZE_MAP = {
    "初号": 42.0,
    "小初": 36.0,
    "一号": 26.0,
    "小一": 24.0,
    "二号": 22.0,
    "小二": 18.0,
    "三号": 16.0,
    "小三": 15.0,
    "四号": 14.0,
    "小四": 12.0,
    "五号": 10.5,
    "小五": 9.0,
    "六号": 7.5,
    "小六": 6.5,
    "七号": 5.5,
    "八号": 5.0,
}


def compact_text(value: str) -> str:
    return re.sub(r"\s+", "", value or "")


def extract_explicit_pt_values(value: str) -> list[float]:
    return [float(match) for match in re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*pt", value, re.IGNORECASE)]


def extract_named_font_sizes(value: str) -> list[tuple[str, float]]:
    compact = compact_text(value)
    matched: list[tuple[str, float]] = []
    occupied = [False] * len(compact)

    def sort_key(item: tuple[str, float]) -> tuple[int, int]:
        name = item[0]
        return (len(name), 1 if name.startswith("小") else 0)

    for name, pt in sorted(FONT_SIZE_MAP.items(), key=sort_key, reverse=True):
        pattern = re.escape(name)
        if not name.endswith("号"):
            pattern += r"(?:号)?"
        for match in re.finditer(pattern, compact):
            if any(occupied[index] for index in range(match.start(), match.end())):
                continue
            for index in range(match.start(), match.end()):
                occupied[index] = True
            matched.append((name, pt))
            break
    return matched


def parse_font_size_signals(value: str, tolerance: float = 0.2) -> dict:
    named_sizes = extract_named_font_sizes(value)
    explicit_pts = extract_explicit_pt_values(value)

    named_pt_values = sorted({pt for _, pt in named_sizes})
    explicit_pt_values = sorted(set(explicit_pts))

    conflict_reasons: list[str] = []
    if len(named_pt_values) > 1:
        labels = ", ".join(name for name, _ in named_sizes)
        conflict_reasons.append(f"字号名冲突：{labels}")
    if len(explicit_pt_values) > 1:
        values = ", ".join(f"{pt:g}pt" for pt in explicit_pt_values)
        conflict_reasons.append(f"显式 pt 数值冲突：{values}")

    if named_pt_values and explicit_pt_values:
        named_pt = named_pt_values[0]
        explicit_pt = explicit_pt_values[0]
        if abs(named_pt - explicit_pt) > tolerance:
            label = named_sizes[0][0]
            conflict_reasons.append(f"字号名 {label} 对应 {named_pt:g}pt，但文本写成 {explicit_pt:g}pt")

    resolved_pt = None
    if not conflict_reasons:
        if explicit_pt_values:
            resolved_pt = explicit_pt_values[0]
        elif named_pt_values:
            resolved_pt = named_pt_values[0]

    return {
        "named_sizes": named_sizes,
        "explicit_pts": explicit_pt_values,
        "resolved_pt": resolved_pt,
        "conflict": bool(conflict_reasons),
        "conflict_reasons": conflict_reasons,
    }


def parse_heading(line: str) -> tuple[int, str] | None:
    """Parse a markdown heading line. Returns (level, text) or None."""
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    if not match:
        return None
    return len(match.group(1)), match.group(2).strip()
