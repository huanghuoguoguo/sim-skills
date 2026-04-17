"""Spec engine for evaluating spec.md files.

Migrated from .claude/skills/evaluate-spec/scripts/check_conflicts.py,
check_structure.py, and check_body_consistency.py.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from spec_rules import parse_font_size_signals, parse_heading
from utils import values_close


LINE_SPACING_MODE_KEYWORDS = {"固定值", "最小值", "多倍行距", "exact", "at_least", "multiple"}
LINE_SPACING_VALUE_RE = re.compile(r"行距[^|]*?(\d+\.?\d*)\s*pt", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Check conflicts
# ---------------------------------------------------------------------------

def check_conflicts(path: str | Path) -> dict:
    """Check obvious contradictions inside spec.md.

    Args:
        path: Path to spec.md file.

    Returns:
        Dict with spec_path, status, conflicts, and summary.
    """
    spec_path = Path(path)
    lines = spec_path.read_text(encoding="utf-8").splitlines()

    conflicts = []
    headings: dict[int, str] = {}
    named_size_assignments: dict[str, list[dict]] = {}

    for line_number, raw_line in enumerate(lines, 1):
        parsed = parse_heading(raw_line)
        if parsed:
            level, text = parsed
            headings[level] = text
            for stale_level in list(headings):
                if stale_level > level:
                    headings.pop(stale_level, None)
            continue

        signals = parse_font_size_signals(raw_line)
        if signals["conflict"]:
            conflicts.append(
                {
                    "line_number": line_number,
                    "context": " / ".join(headings[level] for level in sorted(headings)),
                    "text": raw_line.strip(),
                    "type": "font_size_conflict",
                    "reasons": signals["conflict_reasons"],
                }
            )

        if len(signals["named_sizes"]) == 1 and len(signals["explicit_pts"]) == 1:
            name, _ = signals["named_sizes"][0]
            named_size_assignments.setdefault(name, []).append(
                {
                    "line_number": line_number,
                    "context": " / ".join(headings[level] for level in sorted(headings)),
                    "text": raw_line.strip(),
                    "pt": signals["explicit_pts"][0],
                }
            )

    for name, assignments in named_size_assignments.items():
        unique_pts = sorted({assignment["pt"] for assignment in assignments})
        if len(unique_pts) <= 1:
            continue
        conflicts.append(
            {
                "line_number": assignments[0]["line_number"],
                "context": assignments[0]["context"],
                "text": name,
                "type": "font_size_inconsistent_across_spec",
                "reasons": [
                    f"字号名 {name} 在 spec 中对应多个 pt 值："
                    + ", ".join(f"{pt:g}pt" for pt in unique_pts)
                ],
                "examples": assignments,
            }
        )

    # Check line_spacing completeness
    for line_number, raw_line in enumerate(lines, 1):
        if LINE_SPACING_VALUE_RE.search(raw_line):
            line_lower = raw_line.lower()
            has_mode = any(kw in raw_line for kw in LINE_SPACING_MODE_KEYWORDS) or \
                       any(kw in line_lower for kw in {"exact", "at_least", "multiple"})
            if not has_mode:
                conflicts.append(
                    {
                        "line_number": line_number,
                        "context": " / ".join(headings[level] for level in sorted(headings)),
                        "text": raw_line.strip(),
                        "type": "line_spacing_mode_missing",
                        "reasons": [
                            "行距规则缺少模式（固定值/最小值/多倍行距），下游 batch-check 无法执行"
                        ],
                    }
                )

    return {
        "spec_path": str(spec_path),
        "status": "pass" if not conflicts else "needs_revision",
        "conflicts": conflicts,
        "summary": {
            "conflict_count": len(conflicts),
        },
    }


# ---------------------------------------------------------------------------
# Check structure
# ---------------------------------------------------------------------------

def parse_headings(lines: list[str]) -> list[dict]:
    """Parse headings from spec.md lines.

    Args:
        lines: Lines from spec.md.

    Returns:
        List of heading dicts with line_number, level, text.
    """
    headings = []
    for line_number, raw_line in enumerate(lines, 1):
        parsed = parse_heading(raw_line)
        if not parsed:
            continue
        level, text = parsed
        headings.append(
            {
                "line_number": line_number,
                "level": level,
                "text": text,
            }
        )
    return headings


def check_structure(
    path: str | Path,
    section_rules: dict[str, list[str]] | None = None,
) -> dict:
    """Check whether spec.md covers required sections.

    Args:
        path: Path to spec.md file.
        section_rules: Dict mapping section names to keyword lists.
            Default: {"正文": ["正文", "正文格式", "body"]}.

    Returns:
        Dict with spec_path, status, covered_sections, missing_sections.
    """
    if section_rules is None:
        section_rules = {
            "正文": ["正文", "正文格式", "body"],
            "标题": ["标题", "heading"],
            "字体": ["字体", "font"],
            "页眉": ["页眉", "header"],
            "页脚": ["页脚", "footer"],
            "页边距": ["页边距", "margin"],
        }

    spec_path = Path(path)
    lines = spec_path.read_text(encoding="utf-8").splitlines()
    headings = parse_headings(lines)

    covered = []
    missing = []
    for section_name, keywords in section_rules.items():
        matched = [
            heading for heading in headings
            if any(keyword in heading["text"] for keyword in keywords)
        ]
        if matched:
            covered.append(
                {
                    "section": section_name,
                    "matched_headings": matched,
                }
            )
        else:
            missing.append(
                {
                    "section": section_name,
                    "reason": "未找到相关标题，评估 Agent 应确认是否遗漏该主题或已被其他章节覆盖。",
                }
            )

    status = "pass" if not missing else "needs_revision"
    return {
        "spec_path": str(spec_path),
        "status": status,
        "covered_sections": covered,
        "missing_sections": missing,
    }


# ---------------------------------------------------------------------------
# Check body consistency
# ---------------------------------------------------------------------------

def top_value(distribution: list[dict]) -> dict | None:
    """Get top value from distribution."""
    if not distribution:
        return None
    return distribution[0]


def check_body_consistency(
    checks: list[dict],
    evidence: dict,
    body_section_keywords: list[str] | None = None,
) -> dict:
    """Compare check instructions against paragraph-stats evidence.

    Args:
        checks: List of check instruction dicts.
        evidence: paragraph-stats output dict with "summary" key.
        body_section_keywords: Only compare checks whose section contains
            one of these keywords. If None, compare all checks.

    Returns:
        Dict with status, body_evidence_summary, supported_rules, mismatches.
    """
    summary = evidence.get("summary", {})

    top_east_asia_font = top_value(summary.get("east_asia_font_distribution", []))
    top_ascii_font = top_value(summary.get("ascii_font_distribution", []))

    top_values = {
        "font_size": (top_value(summary.get("font_size_distribution", [])) or {}).get("value"),
        "line_spacing": (top_value(summary.get("line_spacing_distribution", [])) or {}).get("value"),
        "first_line_indent": (top_value(summary.get("first_line_indent_distribution", [])) or {}).get("value"),
    }

    mismatches = []
    supported = []

    for check in checks:
        # Filter by section keywords
        if body_section_keywords:
            section = check.get("section") or ""
            if not any(kw in section for kw in body_section_keywords):
                continue

        check_type = check.get("type")
        rule_text = check.get("rule_text", "")

        if check_type in ("font_size", "first_line_indent"):
            expected = check.get("expected")
            actual = top_values.get(check_type)
            tol = 0.2 if check_type == "font_size" else 1.0
            if values_close(expected, actual, tolerance=tol):
                supported.append({"rule_text": rule_text, "evidence": actual})
            else:
                mismatches.append({
                    "rule_text": rule_text, "type": check_type,
                    "expected": expected, "actual": actual,
                    "reason": f"Body {check_type} distribution does not match expected.",
                })
        elif check_type == "line_spacing":
            expected = check.get("expected", {})
            expected_value = f"{expected.get('mode')}:{expected.get('value')}"
            if top_values["line_spacing"] == expected_value:
                supported.append({"rule_text": rule_text, "evidence": top_values["line_spacing"]})
            else:
                mismatches.append({
                    "rule_text": rule_text, "type": "line_spacing",
                    "expected": expected_value, "actual": top_values["line_spacing"],
                    "reason": "Body line_spacing distribution does not match expected.",
                })
        elif check_type == "font":
            scope = check.get("scope", "east_asia")
            evidence_item = top_east_asia_font if scope == "east_asia" else top_ascii_font
            if evidence_item is None or evidence_item["count"] < 3:
                continue
            actual = evidence_item["value"]
            if actual == check.get("expected"):
                supported.append({"rule_text": rule_text, "evidence": actual})
            else:
                mismatches.append({
                    "rule_text": rule_text, "type": "font", "scope": scope,
                    "expected": check.get("expected"), "actual": actual,
                    "reason": "Body font distribution does not match expected.",
                })

    status = "pass" if not mismatches else "needs_revision"
    return {
        "status": status,
        "body_evidence_summary": summary,
        "supported_rules": supported,
        "mismatches": mismatches,
    }