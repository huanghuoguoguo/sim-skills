#!/usr/bin/env python3
"""extract-spec skill - Extract format rules from template + guidelines with AI review."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Add word skill scripts to sys.path
word_scripts = Path(__file__).parent.parent.parent / "word" / "scripts"
if str(word_scripts) not in sys.path:
    sys.path.insert(0, str(word_scripts))

from docx_parser import parse_word_document


class Rule:
    def __init__(self, id: str, type: str, selector: str, applies_to: str,
                 properties: dict, severity: str = "major", enabled: bool = True,
                 source_refs: list = None, confidence: float = 0.0, message_template: str = ""):
        self.id = id
        self.type = type
        self.selector = selector
        self.applies_to = applies_to
        self.properties = properties
        self.severity = severity
        self.enabled = enabled
        self.source_refs = source_refs or []
        self.confidence = confidence
        self.message_template = message_template

    def to_dict(self) -> dict:
        return {
            "id": self.id, "type": self.type, "selector": self.selector,
            "applies_to": self.applies_to, "properties": self.properties,
            "severity": self.severity, "enabled": self.enabled,
            "source_refs": self.source_refs, "confidence": self.confidence,
            "message_template": self.message_template,
        }


class Source:
    def __init__(self, id: str, source_type: str, file_ref: str,
                 anchor: dict = None, excerpt: str = ""):
        self.id = id
        self.source_type = source_type
        self.file_ref = file_ref
        self.anchor = anchor or {}
        self.excerpt = excerpt

    def to_dict(self) -> dict:
        return {
            "id": self.id, "source_type": self.source_type,
            "file_ref": self.file_ref, "anchor": self.anchor,
            "excerpt": self.excerpt,
        }


class PendingConfirmation:
    def __init__(self, rule_id: str, question: str, evidence: str,
                 suggestion: str = None, confidence: str = "medium"):
        self.rule_id = rule_id
        self.question = question
        self.evidence = evidence
        self.suggestion = suggestion
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "question": self.question,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
        }


def map_style_to_selector(style_name: str) -> str | None:
    name = style_name.lower()
    if "heading 1" in name or "标题 1" in name:
        return "body.heading.level1"
    if "heading 2" in name or "标题 2" in name:
        return "body.heading.level2"
    if "heading 3" in name or "标题 3" in name:
        return "body.heading.level3"
    if "body" in name or "正文" in name or name == "normal":
        return "body.paragraph"
    if "abstract" in name or "摘要" in name:
        return "abstract.body"
    if "toc" in name or "目录" in name:
        return "toc.entry"
    if "caption" in name or "题注" in name:
        return "figure.caption"
    if "reference" in name or "bibliography" in name or "参考文献" in name:
        return "references.entry"
    if "cover" in name or "封面" in name:
        return "cover.title"
    return None


def normalize_properties(props: dict) -> dict:
    """Normalize style properties, converting EMU to pt for spacing values.

    Note: python-docx returns raw EMU values for some properties:
    - line_spacing: can be EMU (for EXACTLY rule) or float multiple
    - space_before/space_after: Length objects with .pt property
    - first_line_indent: Length objects with .pt property
    EMU conversion: 12700 EMU = 1 pt
    """
    normalized = {}

    # Font family
    if "font_family" in props:
        normalized["font_family_zh"] = props["font_family"]
    if "font_family_zh" in props:
        normalized["font_family_zh"] = props["font_family_zh"]

    # Font size
    if "font_size_pt" in props:
        normalized["font_size_pt"] = props["font_size_pt"]

    # Alignment
    if "alignment" in props:
        normalized["alignment"] = props["alignment"]

    # Line spacing - handle both 'line_spacing' (raw) and 'line_spacing_value'
    line_spacing_value = props.get("line_spacing_value") or props.get("line_spacing")
    line_spacing_rule = props.get("line_spacing_rule")

    if line_spacing_value is not None:
        # Determine if value is in EMU (large number) or already in pt/multiple
        if isinstance(line_spacing_value, (int, float)) and line_spacing_value > 1000:
            # Likely EMU - convert to pt
            line_spacing_value = line_spacing_value / 12700.0

        # Determine mode from rule
        if line_spacing_rule:
            rule_str = str(line_spacing_rule).lower() if not isinstance(line_spacing_rule, str) else line_spacing_rule.lower()
            if 'exact' in rule_str:
                normalized["line_spacing_mode"] = "exact"
                normalized["line_spacing_pt"] = line_spacing_value
            elif 'multiple' in rule_str or 'at_least' in rule_str:
                normalized["line_spacing_mode"] = "multiple"
                normalized["line_spacing_multiple"] = line_spacing_value
            else:
                normalized["line_spacing_mode"] = line_spacing_rule
                normalized["line_spacing_pt"] = line_spacing_value
        else:
            # No rule specified, assume exact if value looks like pt
            normalized["line_spacing_pt"] = line_spacing_value

    # Space before/after - handle both 'space_before_pt' and 'space_before'
    space_before = props.get("space_before_pt") or props.get("space_before")
    if space_before is not None:
        if isinstance(space_before, (int, float)) and space_before > 100:
            space_before = space_before / 12700.0
        normalized["space_before_pt"] = space_before

    space_after = props.get("space_after_pt") or props.get("space_after")
    if space_after is not None:
        if isinstance(space_after, (int, float)) and space_after > 100:
            space_after = space_after / 12700.0
        normalized["space_after_pt"] = space_after

    # First line indent - handle both 'first_line_indent_pt' and 'first_line_indent'
    first_line_indent = props.get("first_line_indent_pt") or props.get("first_line_indent")
    if first_line_indent is not None:
        if isinstance(first_line_indent, (int, float)) and first_line_indent > 100:
            first_line_indent = first_line_indent / 12700.0
        normalized["first_line_indent_pt"] = first_line_indent
        # Also calculate character count (assuming 12pt font)
        normalized["first_line_indent_chars"] = round(first_line_indent / 12.0)

    return normalized


def generate_pending_confirmations(rules: list[Rule], template_facts) -> list[PendingConfirmation]:
    """生成待确认项列表 - AI 校对的核心逻辑。"""
    confirmations = []
    rules_by_selector = {r.selector: r for r in rules}

    # 1. 检查正文首行缩进
    body_rule = rules_by_selector.get("body.paragraph")
    if body_rule:
        first_line_indent = body_rule.properties.get("first_line_indent_chars", 0)
        if first_line_indent == 0 or first_line_indent is None:
            confirmations.append(PendingConfirmation(
                rule_id="rule-body-paragraph",
                question="正文是否要求首行缩进 2 字符？",
                evidence="模板中首行缩进为 0 或未定义",
                suggestion="中文论文通常要求首行缩进 2 字符",
                confidence="high",
            ))

    # 2. 检查行距
    if body_rule:
        line_spacing = body_rule.properties.get("line_spacing_multiple")
        line_spacing_pt = body_rule.properties.get("line_spacing_pt")
        if line_spacing is None and line_spacing_pt is None:
            confirmations.append(PendingConfirmation(
                rule_id="rule-body-paragraph",
                question="正文行距要求是什么？",
                evidence="模板中行距未明确定义",
                suggestion="中文论文通常要求 1.5 倍行距或 20pt 固定行距",
                confidence="medium",
            ))
        elif line_spacing_pt is not None and line_spacing_pt < 18:
            confirmations.append(PendingConfirmation(
                rule_id="rule-body-paragraph",
                question="正文行距是否需要调整？",
                evidence=f"模板中行距为 {line_spacing_pt}pt，可能偏小",
                suggestion="建议设置为 1.5 倍行距或 20pt 固定行距",
                confidence="medium",
            ))

    # 3. 检查段前段后距
    if body_rule:
        space_before = body_rule.properties.get("space_before_pt", 0)
        space_after = body_rule.properties.get("space_after_pt", 0)
        if space_before == 0 and space_after == 0:
            confirmations.append(PendingConfirmation(
                rule_id="rule-body-paragraph",
                question="正文段落是否需要段前段后距？",
                evidence="模板中段前段后距均为 0",
                suggestion="部分学校要求段前 6pt 或段后 6pt",
                confidence="low",
            ))

    # 4. 检查一级标题
    h1_rule = rules_by_selector.get("body.heading.level1")
    if h1_rule:
        h1_size = h1_rule.properties.get("font_size_pt")
        if h1_size and h1_size < 14:
            confirmations.append(PendingConfirmation(
                rule_id="rule-body-heading-level1",
                question="一级标题字号是否需要加大？",
                evidence=f"模板中一级标题为 {h1_size}pt",
                suggestion="一级标题通常要求 16-18pt 或小二/三号",
                confidence="medium",
            ))

        # 检查一级标题段前段后距
        h1_space_before = h1_rule.properties.get("space_before_pt")
        h1_space_after = h1_rule.properties.get("space_after_pt")
        if h1_space_before is None and h1_space_after is None:
            confirmations.append(PendingConfirmation(
                rule_id="rule-body-heading-level1",
                question="一级标题是否需要段前段后距？",
                evidence="模板中段前段后距未定义",
                suggestion="一级标题通常要求段前 24pt、段后 12pt",
                confidence="medium",
            ))

    # 5. 检查参考文献
    ref_rule = rules_by_selector.get("references.entry")
    if ref_rule:
        ref_size = ref_rule.properties.get("font_size_pt")
        if ref_size and ref_size > 10.5:
            confirmations.append(PendingConfirmation(
                rule_id="rule-references-entry",
                question="参考文献字号是否需要调整？",
                evidence=f"模板中参考文献为 {ref_size}pt",
                suggestion="参考文献通常要求小五号 (9pt) 或五号 (10.5pt)",
                confidence="low",
            ))

    # 6. 检查图题表题
    caption_rule = rules_by_selector.get("figure.caption")
    if caption_rule:
        caption_size = caption_rule.properties.get("font_size_pt")
        if caption_size and caption_size > 10.5:
            confirmations.append(PendingConfirmation(
                rule_id="rule-figure-caption",
                question="图题表题字号是否需要调整？",
                evidence=f"模板中题注为 {caption_size}pt",
                suggestion="题注通常要求小五号 (9pt) 或五号 (10.5pt)",
                confidence="low",
            ))

    return confirmations


def ai_review_rules(rules: list[Rule], pending_confirmations: list[PendingConfirmation]) -> list[Rule]:
    """AI 校对规则 - 补充缺失的关键属性建议。"""
    reviewed_rules = []

    for rule in rules:
        reviewed_props = dict(rule.properties)

        # 根据待确认项补充建议值
        for pc in pending_confirmations:
            if pc.rule_id == rule.id and pc.suggestion:
                # 标记为需要人工确认的属性
                if "需要人工确认" not in rule.properties:
                    reviewed_props["_review_needed"] = True

        reviewed_rule = Rule(
            id=rule.id,
            type=rule.type,
            selector=rule.selector,
            applies_to=rule.applies_to,
            properties=reviewed_props,
            severity=rule.severity,
            enabled=rule.enabled,
            source_refs=rule.source_refs,
            confidence=rule.confidence,
            message_template=rule.message_template,
        )
        reviewed_rules.append(reviewed_rule)

    return reviewed_rules


def resolve_path(path_str: str) -> str:
    """Resolve a path, supporting glob patterns."""
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str


def extract_format_texts(template_facts) -> list[str]:
    """从文档段落中提取包含格式说明的文字。

    AI 主动读取文档中的格式描述文字，而不是仅依赖样式 XML。
    """
    format_keywords = [
        '字体', '字号', '行距', '缩进', '宋体', '黑体', '楷体', '仿宋',
        'Times', 'Arial', '小四', '四号', '三号', '五号', '一号', '二号',
        '居中', '左对齐', '右对齐', '两端对齐', '加粗', 'bold',
        '段前', '段后', '间距', 'pt', '字符', '厘米', 'cm'
    ]

    format_texts = []
    for p in template_facts.paragraphs:
        if p.text:
            # 检查是否包含格式相关的关键词
            if any(kw in p.text for kw in format_keywords):
                format_texts.append(p.text)
    return format_texts


def parse_format_text_to_props(text: str) -> dict:
    """从格式说明文字中解析属性。

    例如：
    - "宋体小四号" → {font_family_zh: "宋体", font_size_pt: 12.0}
    - "首行缩进 2 字符" → {first_line_indent_chars: 2}
    - "行距 20pt" → {line_spacing_value: 20.0}
    """
    import re
    props = {}

    # 中文字体
    if '宋体' in text:
        props['font_family_zh'] = '宋体'
    if '黑体' in text:
        props['font_family_zh'] = '黑体'
    if '楷体' in text:
        props['font_family_zh'] = '楷体'
    if '仿宋' in text:
        props['font_family_zh'] = '仿宋'

    # 英文字体
    if 'Times New Roman' in text or 'times new roman' in text.lower():
        props['font_family_en'] = 'Times New Roman'
    if 'Arial' in text:
        props['font_family_en'] = 'Arial'

    # 字号（中文）- 按顺序匹配，先匹配"小四"再匹配"四号"，避免误匹配
    # 使用正则精确匹配
    size_map = [
        ('一号', 26.0), ('小一', 24.0),
        ('二号', 22.0), ('小二', 18.0),
        ('三号', 16.0), ('小三', 15.0),
        ('小四', 12.0), ('四号', 14.0),  # 先匹配小四
        ('小五', 9.0), ('五号', 10.5),   # 先匹配小五
    ]
    for zh_size, pt in size_map:
        # 使用正则避免匹配到"小四号字"中的"小四"后面的内容
        if re.search(rf'{zh_size}(?:号 | 字)?', text):
            props['font_size_pt'] = pt
            props['font_size_chinese'] = zh_size
            break

    # 字号（数字 + pt）- 要最后匹配，避免误匹配行距、段前段后距中的 pt 值
    # 只有当文中没有"行距"、"段前"、"段后"等关键词时才匹配
    has_line_spacing = '行距' in text or '固定行距' in text
    has_space_before = '段前' in text
    has_space_after = '段后' in text
    if not (has_line_spacing or has_space_before or has_space_after):
        pt_match = re.search(r'(\d+(?:\.\d+)?)\s*pt', text)
        if pt_match and 'font_size_pt' not in props:
            props['font_size_pt'] = float(pt_match.group(1))

    # 首行缩进 - 支持多种表述："首行缩进 2 字符"、"首行缩进 2 个中文字符"
    # 注意：从 docx 解析的文本中"首行缩进"和数字之间可能没有空格
    indent_match = re.search(r'首行缩进\s*[^\d]*(\d+)\s*(?:个)?(?:中)?(?:文)?(?:字)?(?:字符)?', text)
    if indent_match:
        chars = int(indent_match.group(1))
        props['first_line_indent_chars'] = chars
        props['first_line_indent_pt'] = chars * 12.0  # 按小四号估算
    # 也检查"缩进 2 字符"这种表述
    elif '缩进' in text:
        indent_match2 = re.search(r'缩进\s*[^\d]*(\d+)\s*字符', text)
        if indent_match2:
            chars = int(indent_match2.group(1))
            props['first_line_indent_chars'] = chars
            props['first_line_indent_pt'] = chars * 12.0

    # 行距 - 支持"行距 20pt"、"固定行距 17pt"等
    # 先检查"固定行距" - 使用 \s* 允许有无空格
    if '固定行距' in text:
        fixed_match = re.search(r'固定行距\s*(\d+(?:\.\d+)?)\s*(?:pt|磅)?', text)
        if fixed_match:
            props['line_spacing_value'] = float(fixed_match.group(1))
            props['line_spacing_mode'] = 'exact'
    # 再检查一般"行距" - 使用 \s* 允许有无空格
    elif '行距' in text:
        spacing_match = re.search(r'行距\s*(\d+(?:\.\d+)?)\s*(?:pt|磅)?', text)
        if spacing_match:
            props['line_spacing_value'] = float(spacing_match.group(1))
            props['line_spacing_mode'] = 'exact'

    # 段前段后距 - 支持"段前间距 3pt"、"段前 3pt"等
    # 使用 \s* 允许"段前"和"间距"之间有空格或无空格
    before_match = re.search(r'段前\s*(?:间距)?[^\d]*(\d+(?:\.\d+)?)\s*(?:pt|磅)?', text)
    if before_match:
        props['space_before_pt'] = float(before_match.group(1))
    after_match = re.search(r'段后\s*(?:间距)?[^\d]*(\d+(?:\.\d+)?)\s*(?:pt|磅)?', text)
    if after_match:
        props['space_after_pt'] = float(after_match.group(1))

    # 对齐方式
    if '居中' in text:
        props['alignment'] = 'center'
    elif '左对齐' in text:
        props['alignment'] = 'left'
    elif '右对齐' in text:
        props['alignment'] = 'right'
    elif '两端对齐' in text:
        props['alignment'] = 'justify'

    # 加粗
    if '加粗' in text or 'bold' in text.lower():
        props['font_weight'] = 'bold'

    return props


def merge_text_props_into_rules(rules: list[Rule], format_texts: list[str], template_facts) -> list[Rule]:
    """将文档文字中提取的属性合并到规则中。

    AI 理解文档中的格式描述，补充样式 XML 中缺失的信息。

    注意：摘要和正文通常使用相同的字体字号和段落格式，
    所以从摘要描述中提取的行距、缩进等信息也应同步到正文规则。
    """
    # 收集所有段落文本中的属性（按 selector 分组）
    text_props_by_selector = defaultdict(list)

    # 用于跟踪摘要/正文相关的属性（以便后续同步到正文规则）
    abstract_body_props = []

    for text in format_texts:
        props = parse_format_text_to_props(text)
        if not props:
            continue

        # 判断这段文字描述的是哪种元素 - 基于关键词和上下文
        # 优先匹配具体的元素类型，再匹配通用类型

        # 参考文献（优先匹配，因为有特定关键词）
        if '参考文献' in text:
            text_props_by_selector['references.entry'].append(props)
            continue

        # 关键词
        if '关键词' in text:
            if '英文' in text or 'Key words' in text:
                text_props_by_selector['keywords.english'].append(props)
            else:
                text_props_by_selector['keywords.chinese'].append(props)
            continue

        # 目录
        if '目录' in text:
            text_props_by_selector['toc.entry'].append(props)
            continue

        # 图题表题
        if '图题' in text or '图 ' in text or '图号' in text:
            text_props_by_selector['figure.caption'].append(props)
            continue
        if '表题' in text or '表头' in text or '表 ' in text:
            text_props_by_selector['table.caption'].append(props)
            continue

        # 封面相关
        if '论文题目' in text and '一号' in text:
            text_props_by_selector['cover.title'].append(props)
            continue
        if '指导教师' in text or '作者姓名' in text or '学科专业' in text or '研究方向' in text:
            text_props_by_selector['cover.info'].append(props)
            continue

        # 标题级别
        if '一级标题' in text or '一级学科' in text:
            text_props_by_selector['body.heading.level1'].append(props)
            continue
        if '二级标题' in text or '标题 2' in text:
            text_props_by_selector['body.heading.level2'].append(props)
            continue
        if '三级标题' in text or '标题 3' in text:
            text_props_by_selector['body.heading.level3'].append(props)
            continue

        # 摘要 - 摘要的格式通常与正文相同，所以提取的属性也要同步到正文
        if '摘要' in text:
            text_props_by_selector['abstract.body'].append(props)
            # 保存摘要的属性，以便后续同步到正文规则
            abstract_body_props.append(props)
            continue

        # 正文 - 最通用的匹配
        # 如果文中包含"正文"或描述了正文的典型属性（如"首行缩进"、"行距"等）
        if '正文' in text:
            text_props_by_selector['body.paragraph'].append(props)
            continue
        # 如果文字中包含行距、缩进等正文常见属性，也归类为正文规则
        # 但要排除"无缩进"这种否定表述
        if any(kw in text for kw in ['首行缩进', '固定行距']):
            # 排除"无缩进"的情况
            if '无缩进' not in text:
                text_props_by_selector['body.paragraph'].append(props)
                continue

    # 合并属性到现有规则
    rules_by_selector = {r.selector: r for r in rules}

    # 首先处理摘要属性同步到正文
    if abstract_body_props and 'body.paragraph' in rules_by_selector:
        body_rule = rules_by_selector['body.paragraph']
        for props in abstract_body_props:
            # 只同步关键的段落格式属性（行距、缩进等）
            for key in ['first_line_indent_chars', 'first_line_indent_pt',
                        'line_spacing_value', 'line_spacing_mode',
                        'space_before_pt', 'space_after_pt']:
                if key not in props:
                    continue
                # 如果正文规则中已有该属性，但摘要的值更明确（如明确的 2 字符），则覆盖
                if key in body_rule.properties:
                    # 对于 first_line_indent_chars，如果摘要中是明确的整数值，优先使用
                    if key == 'first_line_indent_chars' and isinstance(props[key], int):
                        existing = body_rule.properties.get(key)
                        # 如果现有值不是整数或小于 props 的值，使用摘要的值
                        if not isinstance(existing, int) or existing < props[key]:
                            body_rule.properties[key] = props[key]
                            body_rule.confidence = min(body_rule.confidence + 0.02, 0.98)
                    elif key == 'first_line_indent_pt':
                        # 如果摘要中的缩进值更大（更完整），使用摘要的值
                        if props[key] > body_rule.properties.get(key, 0):
                            body_rule.properties[key] = props[key]
                            # 同步更新字符数
                            body_rule.properties['first_line_indent_chars'] = round(props[key] / 12.0)
                            body_rule.confidence = min(body_rule.confidence + 0.02, 0.98)
                else:
                    body_rule.properties[key] = props[key]
                    body_rule.confidence = min(body_rule.confidence + 0.02, 0.98)

    for selector, prop_list in text_props_by_selector.items():
        # 合并所有相关属性
        merged_props = {}
        source_excerpts = []
        for props in prop_list:
            merged_props.update(props)

        if selector in rules_by_selector:
            # 补充现有规则
            rule = rules_by_selector[selector]
            for key, value in merged_props.items():
                if key not in rule.properties:
                    rule.properties[key] = value
                    rule.confidence = min(rule.confidence + 0.05, 0.98)
        else:
            # 创建新规则
            if merged_props:
                new_rule = Rule(
                    id=f"rule-{selector.replace('.', '-')}",
                    type="style_rule",
                    selector=selector,
                    applies_to="paragraph",
                    properties=merged_props,
                    severity="major",
                    enabled=True,
                    source_refs=["src-template-001"],
                    confidence=0.90,
                    message_template=f"{selector} 格式不符合要求。",
                )
                rules.append(new_rule)

    return rules


def main():
    parser = argparse.ArgumentParser(description="Extract format rules from template + guidelines")
    parser.add_argument("template", help="Path to template .docx/.dotm file")
    parser.add_argument("guidelines", nargs="*", help="Optional guideline files")
    parser.add_argument("--output", help="Where to write JSON spec")
    parser.add_argument("--skip-review", action="store_true", help="Skip AI review step")
    parser.add_argument("--skip-text-analysis", action="store_true", help="Skip AI text analysis step")
    args = parser.parse_args()

    # Resolve template path (support glob patterns)
    template_path = resolve_path(args.template)
    template_facts = parse_word_document(template_path)

    rules = []
    sources = []

    # Add template source
    template_source = Source(
        id="src-template-001",
        source_type="template_docx",
        file_ref=Path(template_path).name,
        anchor={"kind": "template"},
        excerpt=f"模板：{Path(template_path).name}",
    )
    sources.append(template_source)

    # Only extract key styles (filter out lists, tables, internal styles, etc.)
    key_style_names = {
        "normal", "正文", "body",
        "heading 1", "标题 1",
        "heading 2", "标题 2",
        "heading 3", "标题 3",
        "abstract", "摘要",
        "toc", "目录",
        "caption", "题注",
        "reference", "bibliography", "参考文献",
        "cover", "封面",
    }

    # Group rules by selector for later merging
    rules_by_selector = defaultdict(list)

    # Extract rules from styles
    for style in template_facts.styles:
        if not style.properties:
            continue

        # Only keep key styles
        style_name_lower = style.name.lower()
        if not any(key in style_name_lower for key in key_style_names):
            continue

        rule_id = f"style-{style.style_id or style.name}".lower().replace(" ", "-")
        selector = map_style_to_selector(style.name)
        if not selector:
            continue

        # 根据属性完整度设置置信度
        prop_count = len(style.properties)
        if prop_count >= 5:
            confidence = 0.95
        elif prop_count >= 3:
            confidence = 0.85
        else:
            confidence = 0.7

        rule = Rule(
            id=rule_id,
            type="style_rule",
            selector=selector,
            applies_to="paragraph",
            properties=normalize_properties(style.properties),
            severity="major",
            enabled=True,
            source_refs=[template_source.id],
            confidence=confidence,
            message_template=f"{selector} 格式不符合要求。",
        )
        rules_by_selector[selector].append(rule)

    # Merge rules: keep only the one with most properties per selector
    for selector, selector_rules in rules_by_selector.items():
        best_rule = max(selector_rules, key=lambda r: len(r.properties))
        best_rule.id = f"rule-{selector.replace('.', '-')}"
        rules.append(best_rule)

    # AI Text Analysis: 从文档文字中提取格式规则
    if not args.skip_text_analysis:
        format_texts = extract_format_texts(template_facts)
        rules = merge_text_props_into_rules(rules, format_texts, template_facts)

    # Add guideline sources
    for i, gp in enumerate(args.guidelines or []):
        source = Source(
            id=f"src-guideline-{i+1:03d}",
            source_type="guideline_text",
            file_ref=Path(gp).name,
            anchor={"kind": "guideline"},
            excerpt=f"规范：{Path(gp).name}",
        )
        sources.append(source)

    # AI Review: Generate pending confirmations
    pending_confirmations = []
    if not args.skip_review:
        pending_confirmations = generate_pending_confirmations(rules, template_facts)
        rules = ai_review_rules(rules, pending_confirmations)

    # Build spec
    spec = {
        "spec_id": f"spec-{Path(template_path).stem.lower()}",
        "version": "0.1.0",
        "status": "extracted",
        "name": f"从 {Path(template_path).name} 提取的规则",
        "artifact_type": "document",
        "scope": "university_thesis",
        "rules": [r.to_dict() for r in rules],
        "sources": [s.to_dict() for s in sources],
        "pending_confirmations": [pc.to_dict() for pc in pending_confirmations],
        "metadata": {
            "template": template_path,
            "guidelines": args.guidelines or [],
            "extraction_method": "hybrid",  # 样式 XML + 文档文字 AI 分析
            "style_count": len(rules),
            "pending_confirmation_count": len(pending_confirmations),
            "extracted_at": datetime.now().isoformat(),
        },
        "ai_review": {
            "enabled": not args.skip_review,
            "review_notes": "AI 已校对常见论文格式要求，待确认项需要人工判断",
        } if not args.skip_review else {"enabled": False},
        "ai_text_analysis": {
            "enabled": not args.skip_text_analysis,
            "method": "keyword-based-extraction",
            "notes": "AI 从模板文档中自动识别格式说明文字（如'宋体小四号'、'首行缩进 2 字符'、'固定行距 17pt'等），补充样式 XML 中缺失的信息",
        } if not args.skip_text_analysis else {"enabled": False},
    }

    content = json.dumps(spec, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
