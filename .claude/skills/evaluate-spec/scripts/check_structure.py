#!/usr/bin/env python3
"""Check whether a spec.md covers common thesis formatting sections."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from spec_rules import parse_heading
from thesis_profiles import load_profile
from utils import resolve_path, write_json_output


def parse_section_rule(value: str) -> tuple[str, list[str]]:
    if "=" not in value:
        raise ValueError("section rule must be in the form LABEL=kw1,kw2")
    label, raw_keywords = value.split("=", 1)
    keywords = [item.strip() for item in raw_keywords.split(",") if item.strip()]
    if not label.strip() or not keywords:
        raise ValueError("section rule must include a label and at least one keyword")
    return label.strip(), keywords


def parse_headings(lines: list[str]) -> list[dict]:
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


def check_structure(path: str | Path, section_rules: dict[str, list[str]]) -> dict:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether spec.md covers core thesis sections")
    parser.add_argument("spec", help="Path to spec.md")
    parser.add_argument("--output", help="Where to write JSON diagnostics")
    parser.add_argument("--profile-json", help="Optional JSON file overriding the default thesis profile")
    parser.add_argument(
        "--section-rule",
        action="append",
        default=[],
        help="Override required section rule as LABEL=kw1,kw2; repeatable",
    )
    args = parser.parse_args()

    overrides = {"evaluate_spec": {}}
    if args.section_rule:
        section_rules = {}
        for item in args.section_rule:
            label, keywords = parse_section_rule(item)
            section_rules[label] = keywords
        overrides["evaluate_spec"]["section_rules"] = section_rules
    profile = load_profile(args.profile_json, overrides=overrides)
    payload = check_structure(
        resolve_path(args.spec),
        section_rules=profile["evaluate_spec"]["section_rules"],
    )
    write_json_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
