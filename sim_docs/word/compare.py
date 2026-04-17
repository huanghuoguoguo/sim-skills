"""Compare engine for document format comparison.

Migrated from .claude/skills/compare-docs/scripts/run.py.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def generate_diff_report(diffs: list[dict], ref_path: str, target_path: str) -> str:
    """Generate Markdown comparison report.

    Args:
        diffs: List of difference dicts.
        ref_path: Reference document path.
        target_path: Target document path.

    Returns:
        Markdown report string.
    """
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


def compare_documents(
    ref_facts: dict,
    target_facts: dict,
    ref_path: str | None = None,
    target_path: str | None = None,
) -> dict:
    """Compare two document facts for format differences.

    Args:
        ref_facts: Reference document facts dict.
        target_facts: Target document facts dict.
        ref_path: Optional reference document path for report.
        target_path: Optional target document path for report.

    Returns:
        Dict with diff_count, diffs, and compared_at timestamp.
    """
    diffs = []

    # Paragraph count
    ref_count = len(ref_facts.get("paragraphs", []))
    target_count = len(target_facts.get("paragraphs", []))
    if ref_count != target_count:
        diffs.append({
            "type": "structure",
            "aspect": "paragraph_count",
            "reference": ref_count,
            "target": target_count,
            "message": f"段落数量不一致：参考={ref_count}, 目标={target_count}",
        })

    # Layout comparison
    ref_layout = ref_facts.get("layout", {})
    target_layout = target_facts.get("layout", {})
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

    result = {
        "diff_count": len(diffs),
        "diffs": diffs,
        "compared_at": datetime.now().isoformat(),
    }

    if ref_path:
        result["reference"] = ref_path
    if target_path:
        result["target"] = target_path

    return result