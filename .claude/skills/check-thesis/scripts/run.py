#!/usr/bin/env python3
"""Workflow wrapper for thesis checking with spec.md + batch_check."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from batch_check import run_batch_check
from summarize_results import build_agent_payload, summarize_deterministic_results
from translate_spec import parse_spec_markdown

libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from utils import resolve_path, setup_word_scripts_path, write_json_output, write_text_output

setup_word_scripts_path(__file__)
from docx_parser import parse_word_document


def build_non_deterministic_results(items: list[dict], status: str, source: str) -> list[dict]:
    results = []
    for item in items:
        results.append(
            {
                "id": item["id"],
                "section": item["section"],
                "rule_text": item["rule_text"],
                "line_number": item["line_number"],
                "status": status,
                "source": source,
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


def format_counter_lines(items: list[dict], default_message: str) -> list[str]:
    if not items:
        return [f"- {default_message}"]
    return [f"- {item['message']}：{item['count']} 处" for item in items]


def format_location_examples(locations: list[str]) -> list[str]:
    if not locations:
        return ["- 未提供定位样例"]
    return [f"- {location}" for location in locations]


def write_artifacts(
    artifacts_dir: Path,
    thesis_facts,
    translated: dict,
    batch_result: dict,
    grouped_failures: list[dict],
    agent_payload: dict,
    result: dict,
    report: str,
) -> None:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    write_json_output(thesis_facts.to_dict(), str(artifacts_dir / "facts.json"))
    write_json_output(translated, str(artifacts_dir / "translated_spec.json"))
    write_json_output(batch_result, str(artifacts_dir / "batch_result.json"))
    write_json_output({"grouped_failures": grouped_failures}, str(artifacts_dir / "grouped_failures.json"))
    write_json_output(agent_payload, str(artifacts_dir / "agent_payload.json"))
    write_json_output(result, str(artifacts_dir / "result.json"))
    write_text_output(report, str(artifacts_dir / "report.md"))


def generate_markdown_report(
    thesis_path: str,
    spec_title: str,
    grouped_failures: list[dict],
    semantic_results: list[dict],
    manual_results: list[dict],
    summary: dict,
    artifacts_dir: Path,
) -> str:
    lines = [
        "# 论文格式检查报告",
        "",
        f"**论文**: {Path(thesis_path).name}",
        f"**规范**: {spec_title}",
        f"**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**中间产物**: {artifacts_dir}",
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

    if grouped_failures:
        lines.extend(["## 确定性问题", ""])
        for failure in grouped_failures:
            lines.append(f"### {failure['rule_text']}")
            lines.append("")
            lines.append(f"- 检查结果：{'不通过' if failure['status'] == 'fail' else '待人工确认'}")
            lines.append(f"- 所属章节：{failure.get('section')}")
            lines.append(f"- 期望值：{failure.get('expected')}")
            if failure.get("matched_count") is not None:
                lines.append(f"- 命中段落：{failure['matched_count']}")
            lines.append(f"- 异常数量：{failure['issue_count']}")
            if failure["actual_summary"]:
                lines.append(f"- 常见实际值：{'；'.join(failure['actual_summary'])}")
            lines.append("- 问题聚合：")
            lines.extend(format_counter_lines(failure["issue_summary"], "存在未细分的问题"))
            lines.append("- 位置样例：")
            lines.extend(format_location_examples(failure["location_examples"]))
            lines.append("")
    else:
        lines.extend(["## 确定性问题", "", "所有已翻译的确定性规则均通过。", ""])

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
    parser.add_argument("--artifacts-dir", help="Where to write intermediate JSON artifacts for downstream Agent consumption")
    parser.add_argument("--sample-limit", type=int, default=5, help="Maximum location examples per failed rule")
    args = parser.parse_args()

    thesis_path = resolve_path(args.thesis)
    spec_path = resolve_path(args.spec)

    translated = parse_spec_markdown(spec_path)
    if args.checks_output:
        write_json_output(translated, args.checks_output)

    thesis_facts = parse_word_document(thesis_path)
    batch_result = run_batch_check(thesis_facts, translated["checks"])
    semantic_results = build_non_deterministic_results(translated["semantic_rules"], "agent_required", "Agent 判断")
    manual_results = build_non_deterministic_results(translated["manual_rules"], "manual_required", "待人工确认")
    grouped_failures = summarize_deterministic_results(batch_result, sample_limit=args.sample_limit)
    summary = build_summary(batch_result, semantic_results, manual_results)
    report_path = Path(args.report) if args.report else Path(thesis_path).with_name(f"{Path(thesis_path).stem}_check_report.md")
    artifacts_dir = Path(args.artifacts_dir) if args.artifacts_dir else report_path.with_name(f"{report_path.stem}_artifacts")
    agent_payload = build_agent_payload(
        thesis_path=thesis_path,
        spec_path=spec_path,
        spec_title=translated["spec_title"],
        translation_summary=translated["summary"],
        summary=summary,
        grouped_failures=grouped_failures,
        semantic_results=semantic_results,
        manual_results=manual_results,
    )

    result = {
        "thesis": thesis_path,
        "spec_path": spec_path,
        "spec_title": translated["spec_title"],
        "checked_at": datetime.now().isoformat(),
        "artifacts_dir": str(artifacts_dir),
        "summary": summary,
        "translation_summary": translated["summary"],
        "deterministic_failures": grouped_failures,
        "semantic_results": semantic_results,
        "manual_results": manual_results,
    }

    write_json_output(result, args.output)

    report = generate_markdown_report(
        thesis_path,
        translated["spec_title"],
        grouped_failures,
        semantic_results,
        manual_results,
        summary,
        artifacts_dir,
    )
    write_text_output(report, str(report_path))
    write_artifacts(artifacts_dir, thesis_facts, translated, batch_result, grouped_failures, agent_payload, result, report)
    print(f"Markdown report saved to: {report_path}", file=sys.stderr)
    print(f"Artifacts saved to: {artifacts_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
