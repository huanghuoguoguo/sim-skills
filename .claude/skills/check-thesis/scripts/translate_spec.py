#!/usr/bin/env python3
"""Translate spec.md into deterministic checks plus semantic/manual review items."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from spec_rules import parse_font_size_signals, parse_heading
from utils import resolve_path, write_json_output

CM_TO_PT = 28.3464567
# Word "小四" (12pt) character width, used for "首行缩进 N 字符" conversion
DEFAULT_CHAR_WIDTH_PT = 10.5

MARGIN_SIDE_MAP = {
    "上边距": "top",
    "下边距": "bottom",
    "左边距": "left",
    "右边距": "right",
}

ALIGNMENT_MAP = {
    "左对齐": "left",
    "居左": "left",
    "居中": "center",
    "居中对齐": "center",
    "右对齐": "right",
    "居右": "right",
    "两端对齐": "justify",
    "分散对齐": "distribute",
}

TITLE_STYLE_MAP = {
    "一级标题": ("Heading 1", ["Heading 1", "标题1", "一级标题", "1级标题"]),
    "二级标题": ("Heading 2", ["Heading 2", "标题2", "二级标题", "2级标题"]),
    "三级标题": ("Heading 3", ["Heading 3", "标题3", "三级标题", "3级标题"]),
    "四级标题": ("Heading 4", ["Heading 4", "标题4", "四级标题", "4级标题"]),
    "五级标题": ("Heading 5", ["Heading 5", "标题5", "五级标题", "5级标题"]),
    "六级标题": ("Heading 6", ["Heading 6", "标题6", "六级标题", "6级标题"]),
}


def parse_alignment(value: str) -> str | None:
    compact = value.strip().replace(" ", "")
    return ALIGNMENT_MAP.get(compact)


def parse_spacing_pt(value: str) -> tuple[float | None, str]:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*pt", value, re.IGNORECASE)
    if match:
        return float(match.group(1)), value.strip()
    return None, value.strip()


def parse_indent(value: str) -> tuple[float | None, str]:
    cm_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*cm", value, re.IGNORECASE)
    if cm_match:
        return round(float(cm_match.group(1)) * CM_TO_PT, 2), value.strip()

    char_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*字?符", value)
    if char_match:
        chars = float(char_match.group(1))
        # Word 中常见“首行缩进 2 字符”约等于 21pt。
        return round(chars * DEFAULT_CHAR_WIDTH_PT, 2), value.strip()

    pt_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*pt", value, re.IGNORECASE)
    if pt_match:
        return float(pt_match.group(1)), value.strip()

    return None, value.strip()


def parse_line_spacing(value: str) -> tuple[dict | None, str]:
    compact = value.strip().replace(" ", "")
    if "单倍行距" in compact:
        return {"mode": "multiple", "value": 1.0}, value.strip()
    if "1.5倍行距" in compact:
        return {"mode": "multiple", "value": 1.5}, value.strip()
    if "双倍行距" in compact:
        return {"mode": "multiple", "value": 2.0}, value.strip()

    multiple_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*倍行距", value)
    if multiple_match:
        return {"mode": "multiple", "value": float(multiple_match.group(1))}, value.strip()

    exact_match = re.search(r"固定值\s*([0-9]+(?:\.[0-9]+)?)\s*pt", value, re.IGNORECASE)
    if exact_match:
        return {"mode": "exact", "value": float(exact_match.group(1))}, value.strip()

    at_least_match = re.search(r"最小值\s*([0-9]+(?:\.[0-9]+)?)\s*pt", value, re.IGNORECASE)
    if at_least_match:
        return {"mode": "at_least", "value": float(at_least_match.group(1))}, value.strip()

    return None, value.strip()


def parse_margins(value: str) -> dict[str, float]:
    matches = re.findall(r"(上|下|左|右)\s*([0-9]+(?:\.[0-9]+)?)\s*cm", value)
    side_map = {"上": "top", "下": "bottom", "左": "left", "右": "right"}
    parsed: dict[str, float] = {}
    for side_label, margin_value in matches:
        parsed[side_map[side_label]] = float(margin_value)
    return parsed



def parse_bullet(line: str) -> str | None:
    match = re.match(r"^\s*[-*]\s+(.*\S)\s*$", line)
    if not match:
        return None
    return match.group(1).strip()


def split_compound_rule(text: str) -> list[str]:
    if text.count("：") + text.count(":") <= 1:
        return [text]

    parts = [part.strip() for part in re.split(r"[，,；;]", text) if part.strip()]
    colon_parts = [part for part in parts if "：" in part or ":" in part]
    return colon_parts or [text]


def classify_context(headings: list[str]) -> dict:
    normalized = [heading.strip() for heading in headings if heading.strip()]
    joined = " / ".join(normalized)

    if not normalized:
        return {"kind": "unknown", "name": joined}

    if any("来源" in heading for heading in normalized):
        return {"kind": "ignored", "name": joined}
    if any("待确认项" in heading for heading in normalized):
        return {"kind": "manual", "name": joined}
    if any(keyword in joined for keyword in ("摘要", "参考文献", "目录")):
        return {"kind": "semantic", "name": joined}
    if any("页面设置" in heading for heading in normalized):
        return {"kind": "layout", "name": joined}
    if any("图题" in heading for heading in normalized):
        return {
            "kind": "paragraph_style",
            "name": joined,
            "selector": "caption:figure",
            "style_name": "Caption",
            "style_aliases": ["Caption", "题注", "图题"],
        }
    if any("表题" in heading for heading in normalized):
        return {
            "kind": "paragraph_style",
            "name": joined,
            "selector": "caption:table",
            "style_name": "Caption",
            "style_aliases": ["Caption", "题注", "表题"],
        }

    deepest = normalized[-1]
    if deepest in TITLE_STYLE_MAP or any("标题" == heading for heading in normalized):
        title_heading = next((heading for heading in reversed(normalized) if heading in TITLE_STYLE_MAP), deepest)
        style_name, aliases = TITLE_STYLE_MAP.get(title_heading, ("Heading 1", ["Heading 1", "标题1", "一级标题"]))
        return {
            "kind": "paragraph_style",
            "name": joined,
            "selector": f"style:{style_name}",
            "style_name": style_name,
            "style_aliases": aliases,
        }

    if any("正文" in heading for heading in normalized):
        return {
            "kind": "paragraph_style",
            "name": joined,
            "selector": "style:Normal",
            "style_name": "Normal",
            "style_aliases": ["Normal", "正文", "Body Text", "Body"],
        }

    return {"kind": "unknown", "name": joined}


def build_check(base: dict, check_type: str, expected, expected_display: str, **extra) -> dict:
    payload = {
        "id": base["id"],
        "section": base["section"],
        "rule_text": base["rule_text"],
        "line_number": base["line_number"],
        "type": check_type,
        "selector": base["selector"],
        "expected": expected,
        "expected_display": expected_display,
        "style_name": base.get("style_name"),
        "style_aliases": base.get("style_aliases", []),
    }
    payload.update(extra)
    return payload


def translate_rule(context: dict, rule_text: str, line_number: int) -> tuple[list[dict], list[dict], list[dict]]:
    checks: list[dict] = []
    semantic_rules: list[dict] = []
    manual_rules: list[dict] = []

    base_record = {
        "section": context["name"],
        "rule_text": rule_text,
        "line_number": line_number,
        "selector": context.get("selector"),
        "style_name": context.get("style_name"),
        "style_aliases": context.get("style_aliases", []),
    }

    if context["kind"] == "ignored":
        return checks, semantic_rules, manual_rules

    if context["kind"] == "semantic":
        semantic_rules.append(
            {
                "id": f"semantic-L{line_number}",
                "section": context["name"],
                "rule_text": rule_text,
                "line_number": line_number,
                "status": "agent_required",
                "source": "Agent 判断",
                "reason": "语义性规则，需要 Agent 结合上下文判断。",
            }
        )
        return checks, semantic_rules, manual_rules

    if context["kind"] == "manual":
        manual_rules.append(
            {
                "id": f"manual-L{line_number}",
                "section": context["name"],
                "rule_text": rule_text,
                "line_number": line_number,
                "status": "manual_required",
                "source": "待人工确认",
            }
        )
        return checks, semantic_rules, manual_rules

    if context["kind"] == "unknown":
        manual_rules.append(
            {
                "id": f"manual-L{line_number}",
                "section": context["name"],
                "rule_text": rule_text,
                "line_number": line_number,
                "status": "manual_required",
                "source": "待人工确认",
                "reason": "当前翻译器无法确定该规则对应的检查范围。",
            }
        )
        return checks, semantic_rules, manual_rules

    if rule_text.startswith("[ ]") or rule_text.startswith("[x]") or rule_text.startswith("[X]"):
        manual_rules.append(
            {
                "id": f"manual-L{line_number}",
                "section": context["name"],
                "rule_text": rule_text,
                "line_number": line_number,
                "status": "manual_required",
                "source": "待人工确认",
            }
        )
        return checks, semantic_rules, manual_rules

    segments = split_compound_rule(rule_text)
    if context["kind"] == "layout" and len(segments) > 1:
        segments = [rule_text]

    for segment_index, segment in enumerate(segments):
        match = re.match(r"^([^：:]+)[：:]\s*(.+)$", segment)
        if not match:
            manual_rules.append(
                {
                    "id": f"manual-L{line_number}-{segment_index + 1}",
                    "section": context["name"],
                    "rule_text": segment,
                    "line_number": line_number,
                    "status": "manual_required",
                    "source": "待人工确认",
                    "reason": "规则不是明确的“属性：值”格式。",
                }
            )
            continue

        label = match.group(1).strip()
        value = match.group(2).strip()
        base = dict(base_record)
        base["id"] = f"L{line_number}-{segment_index + 1}"

        if context["kind"] == "layout":
            if label == "纸张":
                checks.append(
                    build_check(base, "page_size", value.strip().upper(), value, selector="document:layout")
                )
                continue
            if label == "页边距":
                margins = parse_margins(value)
                if not margins:
                    manual_rules.append(
                        {
                            "id": f"manual-L{line_number}-{segment_index + 1}",
                            "section": context["name"],
                            "rule_text": segment,
                            "line_number": line_number,
                            "status": "manual_required",
                            "source": "待人工确认",
                            "reason": "未能解析页边距数值。",
                        }
                    )
                    continue
                for side, margin_value in margins.items():
                    checks.append(
                        build_check(
                            base,
                            "margin",
                            margin_value,
                            f"{margin_value}cm",
                            side=side,
                            id=f"{base['id']}-{side}",
                            selector="document:layout",
                        )
                    )
                continue

            if label in MARGIN_SIDE_MAP:
                margin_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*cm", value, re.IGNORECASE)
                if margin_match:
                    checks.append(
                        build_check(
                            base,
                            "margin",
                            float(margin_match.group(1)),
                            value,
                            side=MARGIN_SIDE_MAP[label],
                            selector="document:layout",
                        )
                    )
                    continue

        normalized_label = label.replace(" ", "")
        if normalized_label in {"中文字体", "字体", "正文字体"}:
            checks.append(build_check(base, "font", value, value, scope="east_asia"))
            continue
        if normalized_label in {"西文字体", "英文字体"}:
            checks.append(build_check(base, "font", value, value, scope="ascii"))
            continue
        if normalized_label == "字号":
            signals = parse_font_size_signals(value)
            if signals["conflict"]:
                manual_rules.append(
                    {
                        "id": f"manual-L{line_number}-{segment_index + 1}",
                        "section": context["name"],
                        "rule_text": segment,
                        "line_number": line_number,
                        "status": "manual_required",
                        "source": "待人工确认",
                        "reason": "字号表达存在冲突：" + "；".join(signals["conflict_reasons"]),
                    }
                )
                continue
            pt_value, display = signals["resolved_pt"], value.strip()
            if pt_value is not None:
                checks.append(build_check(base, "font_size", pt_value, display))
                continue
        if normalized_label == "行距":
            line_spacing, display = parse_line_spacing(value)
            if line_spacing is not None:
                checks.append(build_check(base, "line_spacing", line_spacing, display))
                continue
        if normalized_label in {"首行缩进", "缩进"}:
            indent_pt, display = parse_indent(value)
            if indent_pt is not None:
                checks.append(build_check(base, "first_line_indent", indent_pt, display))
                continue
        if normalized_label == "段前距":
            spacing_pt, display = parse_spacing_pt(value)
            if spacing_pt is not None:
                checks.append(build_check(base, "spacing_before", spacing_pt, display))
                continue
        if normalized_label == "段后距":
            spacing_pt, display = parse_spacing_pt(value)
            if spacing_pt is not None:
                checks.append(build_check(base, "spacing_after", spacing_pt, display))
                continue
        if normalized_label in {"对齐", "对齐方式"}:
            alignment = parse_alignment(value)
            if alignment is not None:
                checks.append(build_check(base, "alignment", alignment, value))
                continue

        manual_rules.append(
            {
                "id": f"manual-L{line_number}-{segment_index + 1}",
                "section": context["name"],
                "rule_text": segment,
                "line_number": line_number,
                "status": "manual_required",
                "source": "待人工确认",
                "reason": "当前翻译器暂不支持该属性。",
            }
        )

    return checks, semantic_rules, manual_rules


def parse_spec_markdown(path: str | Path) -> dict:
    spec_path = Path(path)
    lines = spec_path.read_text(encoding="utf-8").splitlines()

    headings: dict[int, str] = {}
    document_title = spec_path.stem
    checks: list[dict] = []
    semantic_rules: list[dict] = []
    manual_rules: list[dict] = []

    for line_number, raw_line in enumerate(lines, 1):
        heading = parse_heading(raw_line)
        if heading:
            level, text = heading
            if level == 1:
                document_title = text
            headings[level] = text
            for stale_level in list(headings):
                if stale_level > level:
                    headings.pop(stale_level, None)
            continue

        bullet = parse_bullet(raw_line)
        if bullet is None:
            continue

        active_headings = [headings[level] for level in sorted(headings)]
        context = classify_context(active_headings)
        item_checks, item_semantic, item_manual = translate_rule(context, bullet, line_number)
        checks.extend(item_checks)
        semantic_rules.extend(item_semantic)
        manual_rules.extend(item_manual)

    return {
        "spec_path": str(spec_path),
        "spec_title": document_title,
        "checks": checks,
        "semantic_rules": semantic_rules,
        "manual_rules": manual_rules,
        "summary": {
            "check_count": len(checks),
            "semantic_rule_count": len(semantic_rules),
            "manual_rule_count": len(manual_rules),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Translate spec.md to deterministic checks")
    parser.add_argument("spec", help="Path to spec.md")
    parser.add_argument("--output", help="Where to write translated checks JSON")
    args = parser.parse_args()

    spec_path = resolve_path(args.spec)
    payload = parse_spec_markdown(spec_path)
    write_json_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
