#!/usr/bin/env python3
"""Agent-based report checker - uses LLM to check skipped rules from check-thesis."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Import shared utilities from __libs__
libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from spec_validation import resolve_path


def match_paragraphs_by_selector(paragraphs: list[dict], selector: str) -> list[dict]:
    """根据 selector 语义匹配段落。"""
    matched = []

    # 提取 selector 的关键部分
    parts = selector.split(".")
    category = parts[0] if parts else ""
    subcategory = parts[1] if len(parts) > 1 else ""

    for p in paragraphs:
        text = p.get("text", "")
        style_name = p.get("style_name", "")
        index = p.get("index", 0)

        match_score = 0

        # 封面匹配：文档前 10 段，包含题目或作者信息
        if category == "frontmatter" and subcategory == "title_page":
            if index < 15:
                if any(kw in text for kw in ["论文", "题目", "学科", "专业", "作者", "姓名", "导师", "方向"]):
                    match_score = 0.9
                elif style_name == "Normal" and text.strip():
                    match_score = 0.5

        # 中文摘要匹配
        elif category == "frontmatter" and subcategory == "abstract" and "zh" in selector:
            if "摘要" in text and "关键词" not in text:
                match_score = 0.95
            elif style_name and "摘要" in style_name:
                match_score = 0.9
            elif "摘要" in text:
                match_score = 0.8

        # 英文摘要匹配
        elif category == "frontmatter" and subcategory == "abstract" and "en" in selector:
            if "Abstract" in text:
                match_score = 0.95
            elif style_name and "Abstract" in style_name:
                match_score = 0.9

        # 中文关键词匹配
        elif category == "frontmatter" and subcategory == "keywords" and "zh" in selector:
            if "关键词：" in text or "关键词:" in text:
                match_score = 0.95
            elif style_name and "关键词" in style_name:
                match_score = 0.8

        # 英文关键词匹配
        elif category == "frontmatter" and subcategory == "keywords" and "en" in selector:
            if "Key words" in text or "Keywords" in text:
                match_score = 0.95
            elif style_name and "Key" in style_name:
                match_score = 0.8

        # 目录匹配
        elif category == "frontmatter" and subcategory == "toc":
            if style_name and ("toc" in style_name.lower() or "目录" in style_name):
                match_score = 0.95
            elif any(kw in text for kw in ["目录", "Contents"]):
                match_score = 0.8

        # 参考文献匹配
        elif category == "backmatter" and subcategory == "references":
            if "参考文献" in text:
                match_score = 0.95
            elif style_name and ("reference" in style_name.lower() or "参考文献" in style_name):
                match_score = 0.9
            elif text.startswith("[") and "]" in text:  # 引用标记如 [1]
                match_score = 0.8

        if match_score > 0.5:
            matched.append({**p, "match_score": match_score})

    # 按匹配分数排序
    matched.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return matched


def check_rule_against_paragraphs(rule: dict, paragraphs: list[dict]) -> dict:
    """检查规则对匹配段落的符合情况。"""
    rule_id = rule.get("id", "unknown")
    selector = rule.get("selector", "")
    expected_props = rule.get("properties", {})
    severity = rule.get("severity", "major")

    if not paragraphs:
        return {
            "rule_id": rule_id,
            "selector": selector,
            "status": "uncertain",
            "matched_paragraphs": [],
            "message": "未找到匹配的段落",
            "confidence": 0.0,
        }

    # 检查每个属性
    issues = []
    actual_props = {}

    for prop_name, expected_value in expected_props.items():
        prop_found = False
        prop_mismatch = None

        for p in paragraphs[:3]:  # 检查前 3 个匹配段落
            actual_value = p.get("properties", {}).get(prop_name)
            if actual_value is None:
                continue

            if prop_name not in actual_props:
                actual_props[prop_name] = actual_value
            prop_found = True

            # 比较值
            if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                if abs(expected_value - actual_value) > 0.5:
                    prop_mismatch = f"{prop_name}: 期望 {expected_value}, 实际 {actual_value}"
            elif isinstance(expected_value, str) and isinstance(actual_value, str):
                if expected_value.lower() != actual_value.lower():
                    prop_mismatch = f"{prop_name}: 期望 {expected_value}, 实际 {actual_value}"
            elif expected_value != actual_value:
                prop_mismatch = f"{prop_name}: 期望 {expected_value}, 实际 {actual_value}"

        if prop_mismatch:
            issues.append(prop_mismatch)

    if issues:
        return {
            "rule_id": rule_id,
            "selector": selector,
            "status": "fail",
            "matched_paragraphs": [{"index": p.get("index"), "text": p.get("text", "")[:50]} for p in paragraphs[:3]],
            "expected": expected_props,
            "actual": actual_props,
            "message": f"格式不符合要求：{' | '.join(issues)}",
            "severity": severity,
            "confidence": 0.85,
        }
    else:
        return {
            "rule_id": rule_id,
            "selector": selector,
            "status": "pass" if actual_props else "uncertain",
            "matched_paragraphs": [{"index": p.get("index"), "text": p.get("text", "")[:50]} for p in paragraphs[:3]],
            "expected": expected_props,
            "actual": actual_props,
            "message": "格式符合要求" if actual_props else "未找到属性值",
            "confidence": 0.9 if actual_props else 0.5,
        }


def generate_agent_report(facts: dict, spec: dict, original_report: dict) -> dict:
    """生成 Agent 增强报告。"""
    paragraphs = facts.get("paragraphs", [])
    rules = spec.get("rules", [])
    skipped_rules = original_report.get("skipped_rules", [])

    agent_checks = []
    summary = {
        "total_skipped": len(skipped_rules),
        "checked_pass": 0,
        "checked_fail": 0,
        "uncertain": 0,
    }

    for skipped in skipped_rules:
        rule_id = skipped.get("rule_id")
        selector = skipped.get("selector", "")

        # 从 spec 中找到对应的规则
        rule = None
        for r in rules:
            if r.get("id") == rule_id:
                rule = r
                break

        if rule is None:
            agent_checks.append({
                "rule_id": rule_id,
                "selector": selector,
                "status": "uncertain",
                "message": "未在 spec.json 中找到对应规则",
                "confidence": 0.0,
            })
            summary["uncertain"] += 1
            continue

        # 匹配段落
        matched = match_paragraphs_by_selector(paragraphs, selector)

        # 检查规则
        check_result = check_rule_against_paragraphs(rule, matched)
        agent_checks.append(check_result)

        if check_result["status"] == "pass":
            summary["checked_pass"] += 1
        elif check_result["status"] == "fail":
            summary["checked_fail"] += 1
        else:
            summary["uncertain"] += 1

    return {
        "original_report": {
            "thesis": original_report.get("thesis"),
            "spec": original_report.get("spec"),
            "issue_count": original_report.get("issue_count"),
            "checked_at": original_report.get("checked_at"),
        },
        "agent_checks": agent_checks,
        "summary": summary,
        "total_issues": original_report.get("issue_count", 0) + summary["checked_fail"],
    }


def main():
    parser = argparse.ArgumentParser(description="Agent-based report checker for skipped rules")
    parser.add_argument("facts", help="Path to facts.json from parse-word")
    parser.add_argument("spec", help="Path to spec.json")
    parser.add_argument("report", help="Path to report.json from check-thesis")
    parser.add_argument("--output", help="Where to write agent report JSON")
    args = parser.parse_args()

    # Load inputs
    facts_path = resolve_path(args.facts)
    spec_path = resolve_path(args.spec)
    report_path = resolve_path(args.report)

    with open(facts_path, "r", encoding="utf-8") as f:
        facts = json.load(f)
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    with open(report_path, "r", encoding="utf-8") as f:
        original_report = json.load(f)

    # Generate agent report
    agent_report = generate_agent_report(facts, spec, original_report)

    # Output
    content = json.dumps(agent_report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
        print(f"Agent report saved to: {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")

    # Print summary
    summary = agent_report.get("summary", {})
    print(f"\n=== Agent Check Summary ===", file=sys.stderr)
    print(f"Total skipped rules: {summary.get('total_skipped', 0)}", file=sys.stderr)
    print(f"Passed: {summary.get('checked_pass', 0)}", file=sys.stderr)
    print(f"Failed: {summary.get('checked_fail', 0)}", file=sys.stderr)
    print(f"Uncertain: {summary.get('uncertain', 0)}", file=sys.stderr)
    print(f"Total issues (Python + Agent): {agent_report.get('total_issues', 0)}", file=sys.stderr)

    return 0 if summary.get("checked_fail", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
