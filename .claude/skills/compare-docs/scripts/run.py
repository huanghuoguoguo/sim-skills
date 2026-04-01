#!/usr/bin/env python3
"""compare-docs skill - Compare two documents for format differences."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from datetime import datetime
from pathlib import Path


def resolve_path(path_str: str) -> str:
    """Resolve a path, supporting glob patterns."""
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str

# Add word skill scripts to sys.path
word_scripts = Path(__file__).parent.parent.parent / "word" / "scripts"
if str(word_scripts) not in sys.path:
    sys.path.insert(0, str(word_scripts))

from docx_parser import parse_word_document


def generate_diff_report(diffs: list, ref_path: str, target_path: str) -> str:
    lines = [
        "# 文档格式比对报告",
        "",
        f"**参考文档**: {Path(ref_path).name}",
        f"**目标文档**: {Path(target_path).name}",
        f"**比对时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 总计",
        "",
        f"共发现 **{len(diffs)}** 处差异。",
        "",
    ]

    by_type = {"structure": [], "layout": [], "style": [], "other": []}
    for diff in diffs:
        by_type.get(diff.get("type", "other"), by_type["other"]).append(diff)

    if by_type["structure"]:
        lines.append("## 结构差异")
        lines.append("")
        for i, diff in enumerate(by_type["structure"], 1):
            lines.append(f"{i}. {diff['message']}")
            lines.append("")

    if by_type["layout"]:
        lines.append("## 布局差异")
        lines.append("")
        for i, diff in enumerate(by_type["layout"], 1):
            lines.append(f"{i}. {diff['message']}")
            lines.append("")

    if by_type["style"]:
        lines.append("## 样式差异")
        lines.append("")
        for i, diff in enumerate(by_type["style"], 1):
            lines.append(f"{i}. {diff['message']}")
            lines.append("")

    if not diffs:
        lines.append("两份文档格式一致。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compare two documents for format differences")
    parser.add_argument("reference", help="Path to reference .docx file")
    parser.add_argument("target", help="Path to target .docx file")
    parser.add_argument("--output", help="Where to write JSON result")
    args = parser.parse_args()

    # Resolve paths (support glob patterns)
    ref_path = resolve_path(args.reference)
    target_path = resolve_path(args.target)

    ref_facts = parse_word_document(ref_path)
    target_facts = parse_word_document(target_path)

    diffs = []

    # Compare paragraph counts
    ref_count = len(ref_facts.paragraphs)
    target_count = len(target_facts.paragraphs)
    if ref_count != target_count:
        diffs.append({
            "type": "structure",
            "aspect": "paragraph_count",
            "reference": ref_count,
            "target": target_count,
            "message": f"段落数量不一致：参考={ref_count}, 目标={target_count}",
        })

    # Compare layouts
    ref_layout = ref_facts.layout
    target_layout = target_facts.layout
    for key in set(ref_layout.keys()) | set(target_layout.keys()):
        ref_val = ref_layout.get(key)
        target_val = target_layout.get(key)
        if ref_val != target_val:
            diffs.append({
                "type": "layout",
                "aspect": key,
                "reference": ref_val,
                "target": target_val,
                "message": f"{key}: 参考={ref_val}, 目标={target_val}",
            })

    report = generate_diff_report(diffs, ref_path, target_path)

    result = {
        "reference": ref_path,
        "target": target_path,
        "compared_at": datetime.now().isoformat(),
        "diff_count": len(diffs),
        "diffs": diffs,
    }

    # Output JSON
    content = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")

    # Save Markdown report
    report_path = Path(target_path).stem + "_diff_report.md"
    Path(report_path).write_text(report, encoding="utf-8")
    print(f"Markdown report saved to: {report_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
