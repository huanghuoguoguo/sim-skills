#!/usr/bin/env python3
"""Workflow wrapper for thesis checking with spec.md + batch_check."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from datetime import datetime
from pathlib import Path

from batch_check import run_batch_check
from translate_spec import parse_spec_markdown


word_scripts = Path(__file__).resolve().parents[2] / "word" / "scripts"
if str(word_scripts) not in sys.path:
    sys.path.insert(0, str(word_scripts))

from docx_parser import parse_word_document


def resolve_path(path_str: str) -> str:
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str


def build_semantic_results(items: list[dict]) -> list[dict]:
    results = []
    for item in items:
        results.append(
            {
                "id": item["id"],
                "section": item["section"],
                "rule_text": item["rule_text"],
                "line_number": item["line_number"],
                "status": "agent_required",
                "source": "Agent 判断",
                "expected": item["rule_text"],
                "actual": None,
                "reason": item.get("reason"),
            }
        )
    return results


def build_manual_results(items: list[dict]) -> list[dict]:
    results = []
    for item in items:
        results.append(
            {
                "id": item["id"],
                "section": item["section"],
                "rule_text": item["rule_text"],
                "line_number": item["line_number"],
                "status": "manual_required",
                "source": "待人工确认",
                "expected": item["rule_text"],
                "actual": None,
                "reason": item.get("reason"),
            }
        )
    return results


def build_summary(batch_result: dict, semantic_results: list[dict], manual_results: list[dict]) -> dict:
    deterministic = batch_result["summary"]
    return {
        "total_items": deterministic["total"] + len(semantic_results) + len(manual_results),
        "deterministic_pass": deterministic["pass"],
        "deterministic_fail": deterministic["fail"],
        "deterministic_unresolved": deterministic["unresolved"],
        "agent_required": len(semantic_results),
        "manual_required": len(manual_results),
    }


def format_issue_lines(issues: list[dict]) -> list[str]:
    lines: list[str] = []
    for issue in issues:
        location = issue.get("location", {})
        location_text = ""
        if "paragraph_index" in location:
            location_text = f"段落 #{location['paragraph_index']}"
            if location.get("style_name"):
                location_text += f"（{location['style_name']}）"
        elif location.get("scope") == "document.layout":
            location_text = "页面设置"
        else:
            location_text = "未定位"

        lines.append(f"- {issue.get('message', '不符合要求')}")
        lines.append(f"  期望：{issue.get('expected')}")
        lines.append(f"  实际：{issue.get('actual')}")
        lines.append(f"  定位：{location_text}")
    return lines


def generate_markdown_report(
    thesis_path: str,
    spec_title: str,
    batch_result: dict,
    semantic_results: list[dict],
    manual_results: list[dict],
    summary: dict,
) -> str:
    lines = [
        "# 论文格式检查报告",
        "",
        f"**论文**: {Path(thesis_path).name}",
        f"**规范**: {spec_title}",
        f"**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 总览",
        "",
        f"- 确定性规则通过：{summary['deterministic_pass']}",
        f"- 确定性规则失败：{summary['deterministic_fail']}",
        f"- 确定性规则未决：{summary['deterministic_unresolved']}",
        f"- 待 Agent 判断：{summary['agent_required']}",
        f"- 待人工确认：{summary['manual_required']}",
        "",
    ]

    failed_results = [result for result in batch_result["results"] if result["status"] in {"fail", "unresolved"}]
    if failed_results:
        lines.extend(["## Python 检查结果", ""])
        for result in failed_results:
            lines.append(f"### {result['rule_text']}")
            lines.append("")
            lines.append(f"- 检查结果：{'不通过' if result['status'] == 'fail' else '待人工确认'}")
            lines.append(f"- 来源：{result['source']}")
            lines.append(f"- 期望值：{result['expected']}")
            lines.append(f"- 实际值：{result['actual']}")
            lines.extend(format_issue_lines(result["issues"]))
            lines.append("")
    else:
        lines.extend(["## Python 检查结果", "", "所有已翻译的确定性规则均通过。", ""])

    if semantic_results:
        lines.extend(["## 待 Agent 判断", ""])
        for result in semantic_results:
            lines.append(f"- {result['rule_text']}")
            lines.append(f"  来源：{result['source']}")
            lines.append(f"  原因：{result.get('reason')}")
        lines.append("")

    if manual_results:
        lines.extend(["## 待人工确认", ""])
        for result in manual_results:
            lines.append(f"- {result['rule_text']}")
            lines.append(f"  来源：{result['source']}")
            if result.get("reason"):
                lines.append(f"  原因：{result['reason']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check thesis against spec.md")
    parser.add_argument("thesis", help="Path to thesis .docx/.dotm")
    parser.add_argument("spec", help="Path to spec.md")
    parser.add_argument("--output", help="Where to write JSON result")
    parser.add_argument("--report", help="Where to write Markdown report")
    parser.add_argument("--checks-output", help="Optional path to save translated checks JSON")
    args = parser.parse_args()

    thesis_path = resolve_path(args.thesis)
    spec_path = resolve_path(args.spec)

    translated = parse_spec_markdown(spec_path)
    if args.checks_output:
        Path(args.checks_output).write_text(json.dumps(translated, ensure_ascii=False, indent=2), encoding="utf-8")

    thesis_facts = parse_word_document(thesis_path)
    batch_result = run_batch_check(thesis_facts, translated["checks"])
    semantic_results = build_semantic_results(translated["semantic_rules"])
    manual_results = build_manual_results(translated["manual_rules"])
    summary = build_summary(batch_result, semantic_results, manual_results)

    result = {
        "thesis": thesis_path,
        "spec_path": spec_path,
        "spec_title": translated["spec_title"],
        "checked_at": datetime.now().isoformat(),
        "summary": summary,
        "translation_summary": translated["summary"],
        "deterministic_results": batch_result["results"],
        "semantic_results": semantic_results,
        "manual_results": manual_results,
    }

    content = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")

    report_path = Path(args.report) if args.report else Path(thesis_path).with_name(f"{Path(thesis_path).stem}_check_report.md")
    report = generate_markdown_report(thesis_path, translated["spec_title"], batch_result, semantic_results, manual_results, summary)
    report_path.write_text(report, encoding="utf-8")
    print(f"Markdown report saved to: {report_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
