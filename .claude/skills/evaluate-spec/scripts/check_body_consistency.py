#!/usr/bin/env python3
"""Compare body rules in spec.md against sampled body evidence from a source document."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

extract_scripts_dir = Path(__file__).resolve().parents[2] / "extract-spec" / "scripts"
if str(extract_scripts_dir) not in sys.path:
    sys.path.insert(0, str(extract_scripts_dir))

check_scripts_dir = Path(__file__).resolve().parents[2] / "check-thesis" / "scripts"
if str(check_scripts_dir) not in sys.path:
    sys.path.insert(0, str(check_scripts_dir))

from collect_body_evidence import collect_body_evidence
from thesis_profiles import load_profile
from translate_spec import parse_spec_markdown_with_profile
from utils import resolve_path, write_json_output


def top_item(distribution: list[dict]):
    if not distribution:
        return None
    return distribution[0]


def approx_equal(expected, actual, tolerance: float = 0.5) -> bool:
    if expected is None or actual is None:
        return False
    try:
        return abs(float(expected) - float(actual)) <= tolerance
    except (TypeError, ValueError):
        return False


def check_body_consistency(
    spec_path: str | Path,
    document_path: str | Path,
    exclude_text_hints: tuple[str, ...] = (),
    profile: dict | None = None,
) -> dict:
    profile = profile or load_profile()
    body_section_keywords = profile["evaluate_spec"]["body_section_keywords"]
    translated = parse_spec_markdown_with_profile(spec_path, profile=profile)
    evidence = collect_body_evidence(document_path, exclude_text_hints=exclude_text_hints, profile=profile)
    summary = evidence["summary"]

    top_font_size_item = top_item(summary["font_size_distribution"])
    top_line_spacing_item = top_item(summary["line_spacing_distribution"])
    top_indent_item = top_item(summary["first_line_indent_distribution"])
    top_east_asia_font_item = top_item(summary["east_asia_font_distribution"])
    top_ascii_font_item = top_item(summary["ascii_font_distribution"])

    top_font_size = top_font_size_item["value"] if top_font_size_item else None
    top_line_spacing = top_line_spacing_item["value"] if top_line_spacing_item else None
    top_indent = top_indent_item["value"] if top_indent_item else None
    top_east_asia_font = top_east_asia_font_item["value"] if top_east_asia_font_item else None
    top_ascii_font = top_ascii_font_item["value"] if top_ascii_font_item else None

    # Map check types to (expected_value, actual_value, match_test, extra_fields) per type
    top_values = {
        "font_size": top_font_size,
        "line_spacing": top_line_spacing,
        "first_line_indent": top_indent,
    }
    reasons = {
        "font_size": "正文主字号分布与 spec 不一致。",
        "line_spacing": "正文主行距分布与 spec 不一致。",
        "first_line_indent": "正文主缩进分布与 spec 不一致。",
        "font": "正文主字体分布与 spec 不一致。",
    }

    mismatches = []
    supported = []
    for check in translated["checks"]:
        if not any(keyword in (check.get("section") or "") for keyword in body_section_keywords):
            continue
        check_type = check.get("type")
        rule_text = check["rule_text"]

        if check_type in ("font_size", "first_line_indent"):
            expected = check.get("expected")
            actual = top_values[check_type]
            tol = 0.2 if check_type == "font_size" else 1.0
            if approx_equal(expected, actual, tolerance=tol):
                supported.append({"rule_text": rule_text, "evidence": actual})
            else:
                mismatches.append({"rule_text": rule_text, "type": check_type, "expected": expected, "actual": actual, "reason": reasons[check_type]})
        elif check_type == "line_spacing":
            expected = check.get("expected", {})
            expected_value = f"{expected.get('mode')}:{expected.get('value')}"
            if top_line_spacing == expected_value:
                supported.append({"rule_text": rule_text, "evidence": top_line_spacing})
            else:
                mismatches.append({"rule_text": rule_text, "type": "line_spacing", "expected": expected_value, "actual": top_line_spacing, "reason": reasons["line_spacing"]})
        elif check_type == "font":
            scope = check.get("scope", "east_asia")
            evidence_item = top_east_asia_font_item if scope == "east_asia" else top_ascii_font_item
            if evidence_item is None or evidence_item["count"] < 3:
                continue
            actual = evidence_item["value"]
            if actual == check.get("expected"):
                supported.append({"rule_text": rule_text, "evidence": actual})
            else:
                mismatches.append({"rule_text": rule_text, "type": "font", "scope": scope, "expected": check.get("expected"), "actual": actual, "reason": reasons["font"]})

    status = "pass" if not mismatches else "needs_revision"
    return {
        "spec_path": str(spec_path),
        "document_path": str(document_path),
        "status": status,
        "body_evidence_summary": summary,
        "supported_rules": supported,
        "mismatches": mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether body rules in spec.md match sampled body evidence")
    parser.add_argument("spec", help="Path to spec.md")
    parser.add_argument("document", help="Path to template/thesis .docx/.dotm")
    parser.add_argument("--output", help="Where to write JSON diagnostics")
    parser.add_argument("--profile-json", help="Optional JSON file overriding the default thesis profile")
    parser.add_argument(
        "--exclude-text-hint",
        action="append",
        default=[],
        help="Exclude candidate paragraphs containing this text hint; repeatable and intended to be passed by the Agent",
    )
    parser.add_argument("--body-section-keyword", action="append", default=[], help="Override body section keyword; repeatable")
    args = parser.parse_args()

    overrides = {
        "evaluate_spec": {},
    }
    if args.body_section_keyword:
        overrides["evaluate_spec"]["body_section_keywords"] = args.body_section_keyword
    profile = load_profile(args.profile_json, overrides=overrides)
    payload = check_body_consistency(
        resolve_path(args.spec),
        resolve_path(args.document),
        exclude_text_hints=tuple(args.exclude_text_hint),
        profile=profile,
    )
    write_json_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
