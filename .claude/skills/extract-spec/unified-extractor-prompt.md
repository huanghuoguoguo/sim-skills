# Unified Extractor Agent

从模板文件中提取所有格式规则，输出结构化的 extraction_result.json。

## 输入

- 文件路径：`{file_path}`
- 已解析的 facts：`{facts_path}`
- Profile schema：从 thesis_profiles.py 加载

---

## ⚡ IRON LAW: 内部验证 + 常识检查

**输出前必须执行：**

1. **三源验证**（适用 section）：style_definition + actual_paragraphs + text_instructions
2. **常识检查**：西文字体≠宋体/黑体/楷体/仿宋
3. **完整性检查**：所有 required section 必须有数据

**违反表现：**
- font_rule.ascii=宋体 且 common_sense_check=pass → 错误
- 缺少 cross_validation.sources → 错误
- required section 缺失 → NEEDS_CONTEXT

---

## 🔧 执行流程

### Phase 1: 加载 Profile

```
从 thesis_profiles.py 加载 DEFAULT_THESIS_PROFILE
获取 required_sections 和 optional_sections
```

### Phase 2: 提取各 Section

按 profile spec_schema.sections 顺序提取：

#### 2.1 页面设置 (layout)

```
facts = load_json(facts_path)
layout = facts.layout

layout_rules = {
    paper_size: layout.page_width × layout.page_height,
    margins: {top, bottom, left, right},
    header_distance: layout.header_distance_cm,
    footer_distance: layout.footer_distance_cm
}

source: "facts_layout"
cross_validation: {sources: ["facts_layout"]}
```

#### 2.2 正文 (font)

```
# Step 1: 样式定义
style_def = run("python3 -m sim_docs query-style {file_path} --style Normal")

# Step 2: 实际段落
stats = run("python3 -m sim_docs stats {facts_path} --style-hint Normal")

# Step 3: 文字说明
text_1 = run("python3 -m sim_docs query-text {file_path} --keyword 西文")
text_2 = run("python3 -m sim_docs query-text {file_path} --keyword Times")
text_3 = run("python3 -m sim_docs query-text {file_path} --keyword 字体")

# Step 4: 三源比对 + 常识检查
font_rule = cross_validate_font(style_def, stats, text_instructions)

# Step 5: 常识检查（强制执行）
if font_rule.ascii_font in [宋体, 黑体, 楷体, 仿宋]:
    font_rule.ascii_font = "⚠️ 待确认（模板使用 {font_rule.ascii_font}）"
    common_sense_check = "needs_revision"
else:
    common_sense_check = "pass"
```

#### 2.3 标题 (heading)

```
heading_rules = []

for level in [1, 2, 3, 4]:
    style_def = run("python3 -m sim_docs query-style {file_path} --style Heading {level}")
    stats = run("python3 -m sim_docs stats {facts_path} --style-hint Heading {level}")
    
    # 使用实际段落值（用户看到的是实际）
    rule = {
        level: level,
        font: stats.top_font or style_def.font,
        font_size: stats.top_size or style_def.font_size,
        source: stats.matched_count > 0 ? "actual_paragraphs" : "style_definition_only"
    }
    
    # 常识检查
    if rule.ascii_font in [宋体, 黑体, 楷体, 仿宋]:
        rule.ascii_font = "⚠️ 待确认（模板使用 {rule.ascii_font}）"
    
    heading_rules.append(rule)
```

#### 2.4 摘要 (abstract)

```
# 文字说明提取
text = run("python3 -m sim_docs query-text {file_path} --keyword 摘要")
text_en = run("python3 -m sim_docs query-text {file_path} --keyword Abstract")

abstract_rules = {
    chinese_abstract: {
        title_format: extract_from_text(text, "摘要标题"),
        body_format: extract_from_text(text, "摘要正文"),
        word_count: extract_from_text(text, "字数")
    },
    english_abstract: {
        title_format: {font: "Times New Roman", ...},
        body_format: extract_from_text(text_en, "英文摘要正文")
    },
    source: "text_instructions"
}
```

#### 2.5 关键词 (keyword)

```
text = run("python3 -m sim_docs query-text {file_path} --keyword 关键词")

keyword_rules = {
    label_format: extract_from_text(text, "关键词："),
    content_format: extract_from_text(text, "关键词内容"),
    count_requirement: extract_from_text(text, "数量"),
    source: "text_instructions"
}
```

#### 2.6 图表Caption (caption)

```
style_def = run("python3 -m sim_docs query-style {file_path} --style Caption")
stats = run("python3 -m sim_docs stats {facts_path} --style-hint Caption")
text = run("python3 -m sim_docs query-text {file_path} --keyword 图")
text2 = run("python3 -m sim_docs query-text {file_path} --keyword 表")

# 检测编号模式
numbering_style = detect_numbering_pattern(facts_path)

caption_rules = {
    style: stats.top_values or style_def,
    numbering_style: numbering_style,
    source: ...
}
```

#### 2.7 参考文献 (reference)

```
text = run("python3 -m sim_docs query-text {file_path} --keyword 参考文献")

reference_rules = {
    font: extract_from_text(text, "字体"),
    font_size: extract_from_text(text, "字号"),
    citation_style: extract_from_text(text, "引用风格"),
    count_requirements: extract_from_text(text, "数量"),
    source: "text_instructions"
}
```

#### 2.8 页眉页脚 (header_footer)

```
facts = load_json(facts_path)
headers = facts.headers
footers = facts.footers

header_footer_rules = {
    header_format: extract_from_headers(headers),
    footer_format: extract_from_footers(footers),
    page_numbering: detect_page_number_format(footers),
    source: "facts_headers_footers"
}
```

#### 2.9 目录 (toc)

```
text = run("python3 -m sim_docs query-text {file_path} --keyword 目录")
style_def = run("python3 -m sim_docs query-style {file_path} --style TOC 1")

toc_rules = {
    toc_format: extract_from_text(text) or style_def,
    heading_levels_included: extract_from_text(text, "标题级别"),
    source: ...
}
```

### Phase 3: Optional Sections

对于 optional sections（封面、附录、致谢）：
- 检查模板是否包含
- 如包含，提取规则
- 如不包含，标注 "模板未包含"

### Phase 4: 常识检查 + 输出

```
# 遍历所有 section 执行常识检查
for section in extraction_result:
    if section.has_font_rule and section.ascii_font in CHINESE_FONTS:
        apply Rule 1

# 检查完整性
for section in required_sections:
    if section.data is null:
        return NEEDS_CONTEXT

# 输出
return {
    status: "DONE",
    output: extraction_result,
    cross_validation: {...},
    tool_errors: [],
    common_sense_check: "pass" | "needs_revision"
}
```

---

## 📤 Output Format

```json
{
  "status": "DONE" | "NEEDS_CONTEXT",
  "output": {
    "layout_rules": {...},
    "font_rules": {...},
    "heading_rules": [...],
    "abstract_rules": {...},
    "keyword_rules": {...},
    "caption_rules": {...},
    "reference_rules": {...},
    "header_footer_rules": {...},
    "toc_rules": {...},
    "optional_sections": {
      "封面": "模板未包含",
      "附录": {...},
      "致谢": "模板未包含"
    }
  },
  "cross_validation": {
    "font": {
      "sources": ["style_definition", "actual_paragraphs", "text_instructions"],
      "conflicts": []
    },
    ...
  },
  "tool_errors": [],
  "common_sense_check": "pass" | "needs_revision",
  "common_sense_issues": []
}
```

---

## ⚠️ 强制执行项

| 检查项 | 强制执行 | 违反后果 |
|--------|----------|----------|
| 西文字体常识检查 | ✓ 必须 | common_sense_check ≠ pass |
| cross_validation.sources 标注 | ✓ 必须 | 视为流程错误 |
| required section 完整性 | ✓ 必须 | NEEDS_CONTEXT |
| 来源 source 标注 | ✓ 必须 | 视为流程错误 |

---

## 📋 CHINESE_FONTS 常识列表

```python
CHINESE_FONTS = ["宋体", "黑体", "楷体", "仿宋", "微软雅黑", "华文宋体", "华文黑体"]
```

任何 font_rule.ascii_font ∈ CHINESE_FONTS 都需要标注待确认。