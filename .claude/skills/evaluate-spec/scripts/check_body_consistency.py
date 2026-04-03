#!/usr/bin/env python3
"""Compare body rules (check instructions) against paragraph evidence (paragraph-stats output)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from utils import resolve_path, values_close, write_json_output


def top_value(distribution: list[dict]):
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
        checks: list of check instruction dicts (same format as batch-check input)
        evidence: paragraph-stats output dict with "summary" key
        body_section_keywords: if provided, only compare checks whose "section"
            contains one of these keywords. If empty/None, compare all checks.
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
        # If keywords provided, filter by section
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare body check instructions against paragraph-stats evidence"
    )
    parser.add_argument("--evidence", required=True, help="Path to paragraph-stats output JSON")
    parser.add_argument("--checks", required=True, help="Path to check instructions JSON")
    parser.add_argument("--body-section-keyword", action="append", default=[], help="Only compare checks in these sections (repeatable)")
    parser.add_argument("--output", help="Where to write JSON diagnostics")
    args = parser.parse_args()

    evidence = json.loads(Path(resolve_path(args.evidence)).read_text(encoding="utf-8"))
    checks_raw = json.loads(Path(resolve_path(args.checks)).read_text(encoding="utf-8"))
    checks = checks_raw.get("checks", checks_raw) if isinstance(checks_raw, dict) else checks_raw

    payload = check_body_consistency(
        checks=checks,
        evidence=evidence,
        body_section_keywords=args.body_section_keyword or None,
    )
    write_json_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
