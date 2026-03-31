#!/usr/bin/env python3
"""check-thesis skill - Check thesis against a spec."""

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
from docx_parser_models import ParagraphFact


class Issue:
    def __init__(self, rule_id: str, severity: str, location: dict = None,
                 expected: dict = None, actual: dict = None,
                 message: str = "", fixable: bool = False):
        self.rule_id = rule_id
        self.severity = severity
        self.location = location or {}
        self.expected = expected or {}
        self.actual = actual or {}
        self.message = message
        self.fixable = fixable

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "location": self.location, "expected": self.expected,
            "actual": self.actual, "message": self.message,
            "fixable": self.fixable,
        }


def values_match(expected, actual) -> bool:
    """判断期望值和实际值是否匹配。"""
    if expected is None:
        return True

    # alignment 特殊处理：支持枚举值和字符串互转
    alignment_map = {
        0: "left",
        1: "center",
        2: "right",
        3: "justify",
        "left": 0,
        "center": 1,
        "right": 2,
        "justify": 3,
    }
    if isinstance(expected, (int, str)) and isinstance(actual, (int, str)):
        exp_val = alignment_map.get(expected, expected)
        act_val = alignment_map.get(actual, actual)
        if exp_val == act_val:
            return True

    # 数值比较（允许一定误差）
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(expected - actual) < 0.5

    # 字符串比较（忽略大小写）
    if isinstance(expected, str) and isinstance(actual, str):
        return expected.lower() == actual.lower()

    # 其他类型直接比较
    return expected == actual


def get_paragraphs_by_selector(thesis_facts, selector: str, rule_id: str = ""):
    """根据 selector 获取段落。

    rule_id 用于从规则 ID 中提取样式名信息，以便更精确匹配。
    """
    # 尝试从 rule_id 中提取样式名（如 style-a -> a）
    style_id_hint = None
    if rule_id and rule_id.startswith("style-"):
        style_id_hint = rule_id[6:]  # 去掉 "style-" 前缀

    if selector == "body.paragraph":
        # 如果有样式 ID 提示，只匹配该样式的段落
        if style_id_hint:
            return [p for p in thesis_facts.paragraphs
                    if p.style_id == style_id_hint or (p.style_name and p.style_name.lower() in ("normal", "正文", "body"))]
        # 否则返回所有使用正文样式的段落
        return [p for p in thesis_facts.paragraphs
                if p.style_name and p.style_name.lower() in ("normal", "正文", "body")]

    if selector.startswith("body.heading."):
        level = selector.split(".")[-1]
        return [p for p in thesis_facts.paragraphs
                if p.style_name and (f"heading {level}" in p.style_name.lower() or f"标题{level}" in p.style_name)]
    if selector.startswith("abstract"):
        return [p for p in thesis_facts.paragraphs
                if p.style_name and ("abstract" in p.style_name.lower() or "摘要" in p.style_name)]
    if selector.startswith("toc"):
        return [p for p in thesis_facts.paragraphs
                if p.style_name and ("toc" in p.style_name.lower() or "目录" in p.style_name)]
    if selector.startswith("references"):
        return [p for p in thesis_facts.paragraphs
                if p.style_name and ("reference" in p.style_name.lower() or "bibliography" in p.style_name.lower() or "参考文献" in p.style_name)]
    if selector.startswith("figure.caption"):
        return [p for p in thesis_facts.paragraphs
                if p.style_name and ("caption" in p.style_name.lower() or "题注" in p.style_name)]
    return []


def check_rule(rule: dict, thesis_facts) -> list[Issue]:
    """检查单条规则。"""
    issues = []
    selector = rule.get("selector", "")
    properties = rule.get("properties", {})
    rule_id = rule.get("id", "unknown")
    severity = rule.get("severity", "major")
    message_template = rule.get("message_template", "")

    paragraphs = get_paragraphs_by_selector(thesis_facts, selector, rule_id)

    for para in paragraphs:
        # 跳过空段落（没有实际内容）
        if not para.text.strip():
            continue

        for prop_name, expected_value in properties.items():
            actual_value = para.properties.get(prop_name)
            if actual_value is None:
                continue
            if not values_match(expected_value, actual_value):
                issue = Issue(
                    rule_id=rule_id,
                    severity=severity,
                    location={
                        "paragraph_index": para.index,
                        "paragraph_id": para.id,
                        "style_name": para.style_name,
                        "text_preview": para.text[:50] if para.text else "",
                    },
                    expected={prop_name: expected_value},
                    actual={prop_name: actual_value},
                    message=f"{message_template} 属性 '{prop_name}' 期望值：{expected_value}, 实际值：{actual_value}",
                    fixable=True,
                )
                issues.append(issue)

    return issues


def generate_report(issues: list[Issue], thesis_path: str, spec_name: str) -> str:
    lines = [
        "# 论文格式检查报告",
        "",
        f"**论文**: {Path(thesis_path).name}",
        f"**规范**: {spec_name}",
        f"**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 总计",
        "",
        f"共发现 **{len(issues)}** 个问题。",
        "",
    ]

    by_severity = {"critical": [], "major": [], "minor": [], "info": []}
    for issue in issues:
        by_severity.get(issue.severity, by_severity["info"]).append(issue)

    if by_severity["critical"]:
        lines.append("## 严重问题")
        lines.append("")
        for i, issue in enumerate(by_severity["critical"], 1):
            lines.append(f"{i}. {issue.message}")
            lines.append(f"   - 位置：段落 #{issue.location.get('paragraph_index', '?')}")
            lines.append("")

    if by_severity["major"]:
        lines.append("## 主要问题")
        lines.append("")
        for i, issue in enumerate(by_severity["major"], 1):
            lines.append(f"{i}. {issue.message}")
            lines.append("")

    if by_severity["minor"]:
        lines.append("## 轻微问题")
        lines.append("")
        for i, issue in enumerate(by_severity["minor"], 1):
            lines.append(f"{i}. {issue.message}")
            lines.append("")

    if by_severity["info"]:
        lines.append("## 提示信息")
        lines.append("")
        for i, issue in enumerate(by_severity["info"], 1):
            lines.append(f"{i}. {issue.message}")
            lines.append("")

    if not issues:
        lines.append("恭喜！未发现格式问题。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Check thesis against a spec")
    parser.add_argument("thesis", help="Path to thesis .docx file")
    parser.add_argument("spec", help="Path to spec JSON file")
    parser.add_argument("--output", help="Where to write JSON result")
    args = parser.parse_args()

    # Resolve paths (support glob patterns)
    thesis_path = resolve_path(args.thesis)
    spec_path = resolve_path(args.spec)

    # Load spec
    with open(spec_path, 'r', encoding='utf-8') as f:
        spec_data = json.load(f)

    # Parse thesis
    thesis_facts = parse_word_document(thesis_path)

    # Check rules
    issues = []
    for rule in spec_data.get("rules", []):
        if not rule.get("enabled", True):
            continue
        rule_issues = check_rule(rule, thesis_facts)
        issues.extend(rule_issues)

    # Build report
    report = generate_report(issues, thesis_path, spec_data.get("name", "Unknown Spec"))

    result = {
        "thesis": thesis_path,
        "spec": spec_data.get("name", "Unknown"),
        "checked_at": datetime.now().isoformat(),
        "issue_count": len(issues),
        "issues_by_severity": {
            "critical": len([i for i in issues if i.severity == "critical"]),
            "major": len([i for i in issues if i.severity == "major"]),
            "minor": len([i for i in issues if i.severity == "minor"]),
            "info": len([i for i in issues if i.severity == "info"]),
        },
        "issues": [i.to_dict() for i in issues],
    }

    # Output JSON
    content = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")

    # Save Markdown report
    report_path = Path(thesis_path).stem + "_check_report.md"
    Path(report_path).write_text(report, encoding="utf-8")
    print(f"Markdown report saved to: {report_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
