#!/usr/bin/env python3
"""Run deterministic thesis format checks in batch."""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path


word_scripts = Path(__file__).resolve().parents[2] / "word" / "scripts"
if str(word_scripts) not in sys.path:
    sys.path.insert(0, str(word_scripts))

from docx_parser import parse_word_document


A4_SIZE_CM = (21.0, 29.7)


def resolve_path(path_str: str) -> str:
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str


def normalized(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", "", value).lower()


def values_close(expected: float, actual: float, tolerance: float = 0.5) -> bool:
    return abs(expected - actual) <= tolerance


def select_paragraphs(facts, check: dict) -> list:
    selector = check.get("selector", "")
    aliases = [normalized(alias) for alias in check.get("style_aliases", []) if alias]
    style_name = normalized(check.get("style_name"))

    paragraphs = [paragraph for paragraph in facts.paragraphs if paragraph.text.strip()]
    if selector == "style:Normal" or selector.startswith("style:"):
        names = set(aliases)
        if style_name:
            names.add(style_name)
        return [paragraph for paragraph in paragraphs if normalized(paragraph.style_name) in names]

    if selector == "caption:figure":
        return [
            paragraph for paragraph in paragraphs
            if normalized(paragraph.style_name) in aliases
            or re.match(r"^图\s*[0-9一二三四五六七八九十]", paragraph.text)
        ]

    if selector == "caption:table":
        return [
            paragraph for paragraph in paragraphs
            if normalized(paragraph.style_name) in aliases
            or re.match(r"^表\s*[0-9一二三四五六七八九十]", paragraph.text)
        ]

    return []


def paragraph_location(paragraph) -> dict:
    return {
        "paragraph_index": paragraph.index,
        "paragraph_id": paragraph.id,
        "style_name": paragraph.style_name,
        "text_preview": paragraph.text[:80],
    }


def check_margin(facts, check: dict) -> dict:
    side = check.get("side")
    expected = check.get("expected")
    actual = facts.layout.get("page_margins", {}).get(f"{side}_cm")
    passed = actual is not None and values_close(float(expected), float(actual), tolerance=0.05)
    issue = None
    if not passed:
        issue = {
            "location": {"scope": "document.layout", "side": side},
            "expected": check.get("expected_display", f"{expected}cm"),
            "actual": None if actual is None else f"{actual}cm",
            "message": f"页边距 {side} 不符合要求",
        }
    return build_check_result(check, "pass" if passed else "fail", actual_display=None if actual is None else f"{actual}cm", issues=[issue] if issue else [])


def check_page_size(facts, check: dict) -> dict:
    expected = normalized(check.get("expected"))
    size = facts.layout.get("page_size", {})
    actual_width = size.get("width_cm")
    actual_height = size.get("height_cm")
    if expected == "a4":
        passed = (
            actual_width is not None
            and actual_height is not None
            and values_close(actual_width, A4_SIZE_CM[0], tolerance=0.1)
            and values_close(actual_height, A4_SIZE_CM[1], tolerance=0.1)
        )
    else:
        passed = False

    issue = None
    if not passed:
        issue = {
            "location": {"scope": "document.layout", "property": "page_size"},
            "expected": check.get("expected_display", check.get("expected")),
            "actual": None if actual_width is None or actual_height is None else f"{actual_width}cm x {actual_height}cm",
            "message": "纸张大小不符合要求",
        }

    actual_display = None if actual_width is None or actual_height is None else f"{actual_width}cm x {actual_height}cm"
    return build_check_result(check, "pass" if passed else "fail", actual_display=actual_display, issues=[issue] if issue else [])


def compare_paragraph_property(check: dict, paragraph, property_name: str, expected, actual, tolerance: float = 0.5) -> dict | None:
    if actual is None:
        return {
            "location": paragraph_location(paragraph),
            "expected": check.get("expected_display"),
            "actual": None,
            "message": f"{property_name} 缺失，无法与规范比对",
        }

    passed = False
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        passed = values_close(float(expected), float(actual), tolerance=tolerance)
    elif isinstance(expected, str) and isinstance(actual, str):
        passed = normalized(expected) == normalized(actual)

    if passed:
        return None

    return {
        "location": paragraph_location(paragraph),
        "expected": check.get("expected_display"),
        "actual": actual,
        "message": f"{property_name} 不符合要求",
    }


def check_font(paragraphs: list, check: dict) -> dict:
    scope = check.get("scope", "east_asia")
    property_name = "font_family_east_asia" if scope == "east_asia" else "font_family_ascii"
    issues = []
    for paragraph in paragraphs:
        issue = compare_paragraph_property(check, paragraph, property_name, check.get("expected"), paragraph.properties.get(property_name), tolerance=0.0)
        if issue:
            issues.append(issue)
    return paragraph_result(check, paragraphs, issues)


def check_font_size(paragraphs: list, check: dict) -> dict:
    issues = []
    for paragraph in paragraphs:
        issue = compare_paragraph_property(check, paragraph, "font_size_pt", float(check.get("expected")), paragraph.properties.get("font_size_pt"), tolerance=0.2)
        if issue:
            issues.append(issue)
    return paragraph_result(check, paragraphs, issues)


def check_alignment(paragraphs: list, check: dict) -> dict:
    issues = []
    for paragraph in paragraphs:
        issue = compare_paragraph_property(check, paragraph, "alignment", check.get("expected"), paragraph.properties.get("alignment"), tolerance=0.0)
        if issue:
            issues.append(issue)
    return paragraph_result(check, paragraphs, issues)


def check_spacing(paragraphs: list, check: dict, property_name: str) -> dict:
    issues = []
    for paragraph in paragraphs:
        issue = compare_paragraph_property(check, paragraph, property_name, float(check.get("expected")), paragraph.properties.get(property_name), tolerance=0.5)
        if issue:
            issues.append(issue)
    return paragraph_result(check, paragraphs, issues)


def check_line_spacing(paragraphs: list, check: dict) -> dict:
    expected = check.get("expected", {})
    issues = []
    for paragraph in paragraphs:
        actual_mode = paragraph.properties.get("line_spacing_mode")
        actual_value = paragraph.properties.get("line_spacing_value")
        passed = actual_mode == expected.get("mode") and actual_value is not None and values_close(float(expected.get("value")), float(actual_value), tolerance=0.1)
        if not passed:
            issues.append(
                {
                    "location": paragraph_location(paragraph),
                    "expected": check.get("expected_display"),
                    "actual": None if actual_mode is None and actual_value is None else {"mode": actual_mode, "value": actual_value},
                    "message": "line_spacing 不符合要求",
                }
            )
    return paragraph_result(check, paragraphs, issues)


def paragraph_result(check: dict, paragraphs: list, issues: list[dict]) -> dict:
    if not paragraphs:
        return build_check_result(
            check,
            status="unresolved",
            actual_display=None,
            issues=[
                {
                    "location": {"selector": check.get("selector")},
                    "expected": check.get("expected_display"),
                    "actual": None,
                    "message": "未找到可匹配的段落",
                }
            ],
        )

    if issues:
        return build_check_result(check, status="fail", actual_display=f"{len(issues)}/{len(paragraphs)} 段不符合", issues=issues, matched_count=len(paragraphs))

    return build_check_result(check, status="pass", actual_display=f"{len(paragraphs)} 段通过", issues=[], matched_count=len(paragraphs))


def build_check_result(check: dict, status: str, actual_display, issues: list[dict], matched_count: int | None = None) -> dict:
    return {
        "id": check.get("id"),
        "section": check.get("section"),
        "rule_text": check.get("rule_text"),
        "line_number": check.get("line_number"),
        "type": check.get("type"),
        "selector": check.get("selector"),
        "status": status,
        "source": "Python 检查",
        "expected": check.get("expected_display"),
        "actual": actual_display,
        "matched_count": matched_count,
        "issues": issues,
    }


def run_batch_check(facts, checks: list[dict]) -> dict:
    results = []
    for check in checks:
        check_type = check.get("type")
        if check_type == "margin":
            results.append(check_margin(facts, check))
            continue
        if check_type == "page_size":
            results.append(check_page_size(facts, check))
            continue

        paragraphs = select_paragraphs(facts, check)
        if check_type == "font":
            results.append(check_font(paragraphs, check))
        elif check_type == "font_size":
            results.append(check_font_size(paragraphs, check))
        elif check_type == "alignment":
            results.append(check_alignment(paragraphs, check))
        elif check_type == "line_spacing":
            results.append(check_line_spacing(paragraphs, check))
        elif check_type == "first_line_indent":
            results.append(check_spacing(paragraphs, check, "first_line_indent_pt"))
        elif check_type == "spacing_before":
            results.append(check_spacing(paragraphs, check, "space_before_pt"))
        elif check_type == "spacing_after":
            results.append(check_spacing(paragraphs, check, "space_after_pt"))
        else:
            results.append(
                build_check_result(
                    check,
                    status="unresolved",
                    actual_display=None,
                    issues=[
                        {
                            "location": {"selector": check.get("selector")},
                            "expected": check.get("expected_display"),
                            "actual": None,
                            "message": f"当前 batch_check 尚不支持类型 {check_type}",
                        }
                    ],
                )
            )

    issues = []
    for result in results:
        if result["status"] in {"fail", "unresolved"}:
            issues.extend(result["issues"])

    summary = {
        "total": len(results),
        "pass": sum(1 for result in results if result["status"] == "pass"),
        "fail": sum(1 for result in results if result["status"] == "fail"),
        "unresolved": sum(1 for result in results if result["status"] == "unresolved"),
    }
    return {
        "summary": summary,
        "results": results,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic checks against a thesis")
    parser.add_argument("thesis", help="Path to thesis .docx/.dotm")
    parser.add_argument("checks", help="Path to translated checks JSON")
    parser.add_argument("--output", help="Where to write JSON result")
    args = parser.parse_args()

    thesis_path = resolve_path(args.thesis)
    checks_path = resolve_path(args.checks)

    payload = json.loads(Path(checks_path).read_text(encoding="utf-8"))
    checks = payload.get("checks", payload)
    thesis_facts = parse_word_document(thesis_path)
    result = {
        "thesis": thesis_path,
        "check_count": len(checks),
        **run_batch_check(thesis_facts, checks),
    }

    content = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
