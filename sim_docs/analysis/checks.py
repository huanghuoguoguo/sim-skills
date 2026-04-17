"""Batch check engine for document property comparison.

This module contains the core logic for comparing parsed document facts
against a list of check instructions and reporting pass/fail/unresolved status.
"""

from __future__ import annotations

import re
from typing import Any

from sim_docs.core.helpers import normalized, values_close


# ---------------------------------------------------------------------------
# Schema: self-describing check capabilities
# ---------------------------------------------------------------------------

CHECK_SCHEMA = {
    "tool": "batch-check",
    "description": (
        "Deterministic document property comparison engine. "
        "Compares parsed document facts against a list of check instructions "
        "and reports pass/fail/unresolved status per check."
    ),
    "check_types": {
        "font": {
            "description": "Compare font family of matching paragraphs",
            "required_fields": ["type", "selector", "expected"],
            "optional_fields": {
                "scope": "east_asia | ascii (default: east_asia)",
                "style_name": "Canonical style name for selector resolution",
                "style_aliases": "Alternative style names to match (string[])",
            },
            "example": {
                "type": "font",
                "scope": "east_asia",
                "selector": "style:Normal",
                "expected": "宋体",
            },
        },
        "font_size": {
            "description": "Compare font size (in pt) of matching paragraphs",
            "required_fields": ["type", "selector", "expected"],
            "tolerance": 0.2,
            "example": {
                "type": "font_size",
                "selector": "style:Heading 1",
                "expected": 16,
                "expected_display": "三号（16pt）",
            },
        },
        "alignment": {
            "description": "Compare paragraph alignment",
            "required_fields": ["type", "selector", "expected"],
            "expected_values": ["left", "center", "right", "justify", "distribute"],
            "example": {
                "type": "alignment",
                "selector": "style:Heading 1",
                "expected": "center",
            },
        },
        "line_spacing": {
            "description": "Compare line spacing mode and value",
            "required_fields": ["type", "selector", "expected"],
            "expected_format": {"mode": "multiple | exact | at_least", "value": "number"},
            "tolerance": 0.1,
            "example": {
                "type": "line_spacing",
                "selector": "style:Normal",
                "expected": {"mode": "multiple", "value": 1.5},
            },
        },
        "spacing_before": {
            "description": "Compare space before paragraph (in pt)",
            "required_fields": ["type", "selector", "expected"],
            "tolerance": 0.5,
            "example": {
                "type": "spacing_before",
                "selector": "style:Heading 1",
                "expected": 24,
            },
        },
        "spacing_after": {
            "description": "Compare space after paragraph (in pt)",
            "required_fields": ["type", "selector", "expected"],
            "tolerance": 0.5,
            "example": {
                "type": "spacing_after",
                "selector": "style:Heading 1",
                "expected": 18,
            },
        },
        "first_line_indent": {
            "description": "Compare first line indent (in pt)",
            "required_fields": ["type", "selector", "expected"],
            "tolerance": 0.5,
            "example": {
                "type": "first_line_indent",
                "selector": "style:Normal",
                "expected": 21,
                "expected_display": "2 字符",
            },
        },
        "margin": {
            "description": "Compare page margin for a specific side (in cm)",
            "required_fields": ["type", "side", "expected"],
            "side_values": ["top", "bottom", "left", "right"],
            "tolerance": 0.05,
            "example": {
                "type": "margin",
                "side": "left",
                "expected": 3.0,
                "selector": "document:layout",
            },
        },
        "page_size": {
            "description": "Compare page size",
            "required_fields": ["type", "expected"],
            "expected_values": ["A4"],
            "example": {
                "type": "page_size",
                "expected": "A4",
                "selector": "document:layout",
            },
        },
        "bold": {
            "description": "Check if paragraphs are bold (true/false)",
            "required_fields": ["type", "selector", "expected"],
            "expected_values": [True, False],
            "example": {
                "type": "bold",
                "selector": "style:Heading 1",
                "expected": True,
            },
        },
        "italic": {
            "description": "Check if paragraphs are italic (true/false)",
            "required_fields": ["type", "selector", "expected"],
            "expected_values": [True, False],
            "example": {
                "type": "italic",
                "selector": "style:Heading 1",
                "expected": False,
            },
        },
    },
    "selectors": {
        "style:<name>": (
            "Match paragraphs whose style_name matches <name> or any of style_aliases "
            "(case-insensitive, whitespace-normalized)"
        ),
        "caption:figure": (
            "Match figure captions by style_aliases or caption_prefix_patterns regex"
        ),
        "caption:table": (
            "Match table captions by style_aliases or caption_prefix_patterns regex"
        ),
        "document:layout": (
            "Document-level layout; auto-assigned for margin and page_size checks"
        ),
    },
    "common_optional_fields": {
        "id": "Unique identifier for this check",
        "section": "Which spec section this check belongs to",
        "rule_text": "Original natural language rule text",
        "expected_display": "Human-readable expected value",
        "style_name": "Canonical style name for paragraph selection",
        "style_aliases": "Alternative style names (string[])",
        "caption_prefix_patterns": "Regex patterns for caption matching (string[])",
    },
}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KNOWN_CHECK_TYPES = set(CHECK_SCHEMA["check_types"].keys())

REQUIRED_FIELDS: dict[str, list[str]] = {
    ctype: info["required_fields"]
    for ctype, info in CHECK_SCHEMA["check_types"].items()
}

A4_SIZE_CM = (21.0, 29.7)

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_check(check: dict, index: int) -> str | None:
    """Return an error message if the check is invalid, else None."""
    ctype = check.get("type")
    if not ctype:
        return f"check[{index}]: missing 'type' field"
    if ctype not in KNOWN_CHECK_TYPES:
        return f"check[{index}]: unknown type '{ctype}'"
    for field in REQUIRED_FIELDS[ctype]:
        if field not in check:
            return f"check[{index}] (type={ctype}): missing required field '{field}'"
    return None


# ---------------------------------------------------------------------------
# Paragraph selection
# ---------------------------------------------------------------------------

def select_paragraphs(paragraphs: list[dict], check: dict) -> list[dict]:
    """Select paragraphs matching the check's selector."""
    selector = check.get("selector", "")
    aliases = {normalized(a) for a in check.get("style_aliases", []) if a}
    style_name = normalized(check.get("style_name"))

    if selector.startswith("style:"):
        names = set(aliases)
        if style_name:
            names.add(style_name)
        selector_name = normalized(selector[len("style:"):])
        if selector_name:
            names.add(selector_name)
        return [p for p in paragraphs if normalized(p.get("style_name")) in names]

    if selector in {"caption:figure", "caption:table"}:
        compiled = [re.compile(pat) for pat in check.get("caption_prefix_patterns", [])]
        return [
            p for p in paragraphs
            if normalized(p.get("style_name")) in aliases
            or any(rx.match(p["text"]) for rx in compiled)
        ]

    return []


def paragraph_location(p: dict) -> dict:
    """Extract location info from a paragraph."""
    return {
        "paragraph_index": p.get("index"),
        "paragraph_id": p.get("id"),
        "style_name": p.get("style_name"),
        "text_preview": p.get("text", "")[:80],
    }


# ---------------------------------------------------------------------------
# Check implementations
# ---------------------------------------------------------------------------

def build_result(
    check: dict,
    status: str,
    actual_display: Any,
    issues: list[dict],
    matched_count: int | None = None,
) -> dict:
    """Build a check result dictionary."""
    return {
        "id": check.get("id"),
        "section": check.get("section"),
        "rule_text": check.get("rule_text"),
        "type": check.get("type"),
        "selector": check.get("selector"),
        "status": status,
        "expected": check.get("expected_display", check.get("expected")),
        "actual": actual_display,
        "matched_count": matched_count,
        "issues": issues,
    }


def _compare_property(
    check: dict,
    p: dict,
    prop_name: str,
    expected: Any,
    actual: Any,
    tolerance: float = 0.5,
) -> dict | None:
    """Compare a property value against expected, return issue if mismatch."""
    if actual is None:
        return {
            "location": paragraph_location(p),
            "expected": check.get("expected_display"),
            "actual": None,
            "message": f"{prop_name} missing",
        }

    passed = False
    if isinstance(expected, bool):
        passed = bool(actual) == expected
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        passed = values_close(float(expected), float(actual), tolerance=tolerance)
    elif isinstance(expected, str) and isinstance(actual, str):
        passed = normalized(expected) == normalized(actual)

    if passed:
        return None

    return {
        "location": paragraph_location(p),
        "expected": check.get("expected_display"),
        "actual": actual,
        "message": f"{prop_name} mismatch",
    }


def _paragraph_result(check: dict, paragraphs: list[dict], issues: list[dict]) -> dict:
    """Build result for paragraph-level checks."""
    if not paragraphs:
        return build_result(
            check, "unresolved", None,
            [{"location": {"selector": check.get("selector")}, "expected": check.get("expected_display"), "actual": None, "message": "no matching paragraphs"}],
        )
    if issues:
        return build_result(check, "fail", f"{len(issues)}/{len(paragraphs)} mismatch", issues, matched_count=len(paragraphs))
    return build_result(check, "pass", f"{len(paragraphs)} ok", [], matched_count=len(paragraphs))


def _check_simple_property(paragraphs: list[dict], check: dict, prop_name: str, tolerance: float) -> dict:
    """Generic check for a single paragraph property against expected value."""
    expected = check["expected"]
    if isinstance(expected, (int, float)):
        expected = float(expected)
    issues = [
        issue for p in paragraphs
        if (issue := _compare_property(check, p, prop_name, expected, p.get("properties", {}).get(prop_name), tolerance=tolerance))
    ]
    return _paragraph_result(check, paragraphs, issues)


def check_font(paragraphs: list[dict], check: dict) -> dict:
    """Check font family property."""
    scope = check.get("scope", "east_asia")
    prop = "font_family_east_asia" if scope == "east_asia" else "font_family_ascii"
    applicable = [p for p in paragraphs if p.get("properties", {}).get(prop) is not None]
    skipped = len(paragraphs) - len(applicable)
    result = _check_simple_property(applicable, check, prop, tolerance=0.0)
    if skipped > 0 and result["status"] != "unresolved":
        result["actual"] = f"{result['actual']} (skipped {skipped} without {scope} font)"
    return result


def check_font_size(paragraphs: list[dict], check: dict) -> dict:
    """Check font size property."""
    return _check_simple_property(paragraphs, check, "font_size_pt", tolerance=0.2)


def check_alignment(paragraphs: list[dict], check: dict) -> dict:
    """Check alignment property."""
    return _check_simple_property(paragraphs, check, "alignment", tolerance=0.0)


def check_bold(paragraphs: list[dict], check: dict) -> dict:
    """Check bold property."""
    return _check_simple_property(paragraphs, check, "bold", tolerance=0.0)


def check_italic(paragraphs: list[dict], check: dict) -> dict:
    """Check italic property."""
    return _check_simple_property(paragraphs, check, "italic", tolerance=0.0)


def check_line_spacing(paragraphs: list[dict], check: dict) -> dict:
    """Check line spacing mode and value."""
    expected = check.get("expected", {})
    issues = []
    for p in paragraphs:
        props = p.get("properties", {})
        actual_mode = props.get("line_spacing_mode")
        actual_value = props.get("line_spacing_value")
        passed = (
            actual_mode == expected.get("mode")
            and actual_value is not None
            and values_close(float(expected.get("value")), float(actual_value), tolerance=0.1)
        )
        if not passed:
            issues.append({
                "location": paragraph_location(p),
                "expected": check.get("expected_display"),
                "actual": None if actual_mode is None and actual_value is None else {"mode": actual_mode, "value": actual_value},
                "message": "line_spacing mismatch",
            })
    return _paragraph_result(check, paragraphs, issues)


def check_spacing(paragraphs: list[dict], check: dict, prop_name: str) -> dict:
    """Check spacing property (before/after/indent)."""
    return _check_simple_property(paragraphs, check, prop_name, tolerance=0.5)


def check_margin(facts: dict, check: dict) -> dict:
    """Check page margin."""
    side = check.get("side")
    expected = check.get("expected")
    actual = facts.get("layout", {}).get("page_margins", {}).get(f"{side}_cm")
    passed = actual is not None and values_close(float(expected), float(actual), tolerance=0.05)
    issue = None
    if not passed:
        issue = {
            "location": {"scope": "document.layout", "side": side},
            "expected": check.get("expected_display", f"{expected}cm"),
            "actual": None if actual is None else f"{actual}cm",
            "message": f"margin {side} mismatch",
        }
    return build_result(check, "pass" if passed else "fail", None if actual is None else f"{actual}cm", [issue] if issue else [])


def check_page_size(facts: dict, check: dict) -> dict:
    """Check page size."""
    expected = normalized(check.get("expected"))
    size = facts.get("layout", {}).get("page_size", {})
    w = size.get("width_cm")
    h = size.get("height_cm")
    if expected == "a4":
        passed = w is not None and h is not None and values_close(w, A4_SIZE_CM[0], 0.1) and values_close(h, A4_SIZE_CM[1], 0.1)
    else:
        passed = False
    issue = None
    if not passed:
        issue = {
            "location": {"scope": "document.layout", "property": "page_size"},
            "expected": check.get("expected_display", check.get("expected")),
            "actual": None if w is None or h is None else f"{w}cm x {h}cm",
            "message": "page_size mismatch",
        }
    actual_display = None if w is None or h is None else f"{w}cm x {h}cm"
    return build_result(check, "pass" if passed else "fail", actual_display, [issue] if issue else [])


# ---------------------------------------------------------------------------
# Dispatch and batch execution
# ---------------------------------------------------------------------------

CHECK_DISPATCH = {
    "font": check_font,
    "font_size": check_font_size,
    "alignment": check_alignment,
    "line_spacing": check_line_spacing,
    "bold": check_bold,
    "italic": check_italic,
}

SPACING_TYPES = {
    "first_line_indent": "first_line_indent_pt",
    "spacing_before": "space_before_pt",
    "spacing_after": "space_after_pt",
}


def _selector_key(check: dict) -> tuple:
    """Generate a cache key for paragraph selection."""
    return (
        check.get("selector", ""),
        normalized(check.get("style_name")),
        tuple(sorted(normalized(a) for a in check.get("style_aliases", []) if a)),
    )


def run_batch_check(facts: dict, checks: list[dict]) -> dict:
    """Execute batch check on document facts.

    Args:
        facts: Parsed document facts (dict from WordDocumentFacts.to_dict()).
        checks: List of check instructions.

    Returns:
        Result dict with summary, results, and issues.
    """
    results = []
    errors = []

    for i, check in enumerate(checks):
        err = validate_check(check, i)
        if err:
            errors.append(err)
    if errors:
        return {"errors": errors, "summary": None, "results": [], "issues": []}

    non_empty = [p for p in facts.get("paragraphs", []) if p.get("text", "").strip()]
    para_cache: dict[tuple, list[dict]] = {}

    for check in checks:
        ctype = check.get("type")

        if ctype == "margin":
            results.append(check_margin(facts, check))
            continue
        if ctype == "page_size":
            results.append(check_page_size(facts, check))
            continue

        key = _selector_key(check)
        if key not in para_cache:
            para_cache[key] = select_paragraphs(non_empty, check)
        paragraphs = para_cache[key]

        handler = CHECK_DISPATCH.get(ctype)
        if handler:
            results.append(handler(paragraphs, check))
        elif ctype in SPACING_TYPES:
            results.append(check_spacing(paragraphs, check, SPACING_TYPES[ctype]))
        else:
            results.append(build_result(
                check, "unresolved", None,
                [{"location": {"selector": check.get("selector")}, "message": f"unsupported check type: {ctype}"}],
            ))

    issues = []
    for r in results:
        if r["status"] in {"fail", "unresolved"}:
            issues.extend(r["issues"])

    summary = {
        "total": len(results),
        "pass": sum(1 for r in results if r["status"] == "pass"),
        "fail": sum(1 for r in results if r["status"] == "fail"),
        "unresolved": sum(1 for r in results if r["status"] == "unresolved"),
    }
    return {"summary": summary, "results": results, "issues": issues}