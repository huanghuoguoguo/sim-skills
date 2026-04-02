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
from utils import resolve_path, write_json_output


SECTION_RULES = {
    "页面设置": ["页面设置"],
    "正文": ["正文"],
    "标题": ["标题"],
    "摘要": ["摘要"],
    "图表": ["图", "表"],
    "参考文献": ["参考文献"],
}


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


def check_structure(path: str | Path) -> dict:
    spec_path = Path(path)
    lines = spec_path.read_text(encoding="utf-8").splitlines()
    headings = parse_headings(lines)

    covered = []
    missing = []
    for section_name, keywords in SECTION_RULES.items():
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
    args = parser.parse_args()

    payload = check_structure(resolve_path(args.spec))
    write_json_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
