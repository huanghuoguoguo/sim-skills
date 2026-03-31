# Spec Schema 草案

## 1. 目标

定义系统中 `Spec` 的最小稳定结构，用于：

- 表达模板或规范的结构化规则
- 驱动 `spec -> artifact` 合规检查
- 支持后续 `artifact -> artifact` 差异比对扩展

本草案优先服务 `.docx` 论文场景，但字段命名不绑定单一格式。

## 2. 设计原则

- schema-first：所有 AI 输出必须落在 schema 内
- engine-friendly：字段能被程序稳定执行
- source-aware：每条规则都能追溯来源
- uncertainty-aware：支持待确认项与置信度
- versioned：允许规则迭代而不破坏历史结果

## 3. 顶层对象

```json
{
  "spec_id": "demo-university-undergrad",
  "version": "0.1.0",
  "status": "draft",
  "name": "某大学本科毕业论文格式规范",
  "artifact_type": "document",
  "scope": "undergraduate_thesis",
  "locale": "zh-CN",
  "description": "用于本科论文格式检查",
  "document_constraints": [],
  "content_blocks": [],
  "rules": [],
  "exceptions": [],
  "sources": [],
  "pending_confirmations": [],
  "metadata": {
    "created_by": "system",
    "created_at": "2026-03-31T00:00:00Z"
  }
}
```

## 4. 顶层字段定义

- `spec_id`
  全局稳定 ID，不含版本。
- `version`
  语义化版本，建议 `major.minor.patch`。
- `status`
  枚举：`draft | reviewed | published | archived`。
- `name`
  面向人的名称。
- `artifact_type`
  当前建议：`document`。后续可扩展 `slide`、`sheet`、`webpage`、`image_layout`。
- `scope`
  规则适用范围，如 `undergraduate_thesis`、`journal_manuscript`。
- `locale`
  默认语言环境。
- `description`
  补充说明。
- `document_constraints`
  文档级约束，如纸张、页边距、页码。
- `content_blocks`
  逻辑区块定义，如封面、摘要、正文、参考文献。
- `rules`
  可执行规则列表。
- `exceptions`
  例外规则。
- `sources`
  来源文件与来源片段。
- `pending_confirmations`
  抽取时无法自动确认的候选项。
- `metadata`
  非执行信息。

## 5. `document_constraints`

用于约束整个 artifact 或文档级属性。

示例：

```json
[
  {
    "id": "page-margin",
    "type": "document_constraint",
    "selector": "document",
    "properties": {
      "page_margin_top_cm": 2.5,
      "page_margin_bottom_cm": 2.5,
      "page_margin_left_cm": 3.0,
      "page_margin_right_cm": 2.5
    },
    "severity": "major"
  }
]
```

## 6. `content_blocks`

用于定义文档中的逻辑分区，方便 selector 解析与报告聚合。

示例：

```json
[
  {
    "id": "cover",
    "type": "content_block",
    "name": "封面",
    "selector": "cover"
  },
  {
    "id": "body",
    "type": "content_block",
    "name": "正文",
    "selector": "body"
  },
  {
    "id": "references",
    "type": "content_block",
    "name": "参考文献",
    "selector": "references"
  }
]
```

## 7. `rules`

### 7.1 Rule 结构

```json
{
  "id": "body-line-spacing",
  "type": "style_rule",
  "selector": "body.paragraph",
  "applies_to": "paragraph",
  "properties": {
    "font_family_zh": "宋体",
    "font_size_pt": 12,
    "line_spacing_mode": "exact",
    "line_spacing_pt": 20,
    "first_line_indent_chars": 2
  },
  "severity": "major",
  "message_template": "正文段落格式不符合要求。",
  "source_refs": ["src-template-body-style"],
  "confidence": 0.96,
  "enabled": true
}
```

### 7.2 Rule 字段定义

- `id`
  当前 spec 内唯一。
- `type`
  建议首批枚举：
  `style_rule | layout_rule | structure_rule | numbering_rule | caption_rule`
- `selector`
  目标对象定位语法。
- `applies_to`
  枚举：`document | section | paragraph | run | table | figure | caption | entry`
- `properties`
  需要比较的属性集合。
- `severity`
  枚举：`critical | major | minor | info`
- `message_template`
  默认错误文案模板。
- `source_refs`
  指向 `sources[].id`。
- `confidence`
  规则可信度，范围 `0-1`。
- `enabled`
  是否启用。

## 8. `selector`

MVP 采用轻量路径式 selector，后续可扩展到更通用谓词式 selector。

### 8.1 MVP 允许值

- `document`
- `cover`
- `abstract.zh.body`
- `toc.entry.level1`
- `body.heading.level1`
- `body.heading.level2`
- `body.paragraph`
- `figure.caption`
- `table.caption`
- `references.entry`

### 8.2 长期扩展形态

- `block[type=paragraph]`
- `block[role=caption]`
- `section[name=body].paragraph`
- `table.cell`
- `layout.page.margin.top`

### 8.3 selector 约束

- selector 只描述“目标对象”，不内嵌业务判断
- selector 的解析必须是确定性的
- 复杂条件后续以 `where` 子句扩展，不先塞入字符串里

## 9. `properties`

### 9.1 MVP 首批属性

- `font_family_zh`
- `font_family_en`
- `font_size_pt`
- `bold`
- `italic`
- `alignment`
- `line_spacing_mode`
- `line_spacing_pt`
- `space_before_pt`
- `space_after_pt`
- `first_line_indent_chars`
- `left_indent_pt`
- `right_indent_pt`
- `page_margin_top_cm`
- `page_margin_bottom_cm`
- `page_margin_left_cm`
- `page_margin_right_cm`
- `caption_position`
- `numbering_pattern`

### 9.2 单位约定

- 字号：`pt`
- 行距：`pt`
- 段前段后：`pt`
- 缩进：`pt`
- 页边距：`cm`
- 置信度：`0-1`

### 9.3 枚举约定

- `alignment`
  `left | center | right | justify`
- `line_spacing_mode`
  `exact | multiple | at_least | single`
- `caption_position`
  `above | below`

## 10. `exceptions`

用于表达例外情况，不应在首版做复杂执行，但 schema 先保留。

示例：

```json
[
  {
    "id": "body-first-paragraph-exception",
    "rule_ref": "body-line-spacing",
    "selector": "body.paragraph:first",
    "override_properties": {
      "first_line_indent_chars": 0
    },
    "reason": "正文首段不缩进"
  }
]
```

## 11. `sources`

每条规则必须尽可能可追溯。

示例：

```json
[
  {
    "id": "src-template-body-style",
    "source_type": "template_docx",
    "file_ref": "template.docx",
    "anchor": {
      "style_name": "正文"
    },
    "excerpt": "模板样式：正文"
  }
]
```

字段建议：

- `id`
- `source_type`
  `template_docx | guideline_pdf | guideline_text | sample_docx | manual_override`
- `file_ref`
- `anchor`
  如样式名、段落 ID、页码、文本片段位置
- `excerpt`
  可选简短摘录

## 12. `pending_confirmations`

用于承接 AI 或规则抽取中的不确定项。

示例：

```json
[
  {
    "id": "pc-001",
    "selector": "table.caption",
    "candidate_property": "font_size_pt",
    "candidate_value": 9,
    "reason": "模板与规范文本存在冲突",
    "source_refs": ["src-template-caption", "src-guideline-caption"],
    "confidence": 0.62
  }
]
```

## 13. Schema 版本策略

- `patch`
  不改变字段语义，仅修正文案或元数据
- `minor`
  新增可选字段或新增 rule type
- `major`
  改变字段语义、单位或 selector 解释逻辑

任何一次检查结果都必须绑定：

- `spec_id`
- `version`

## 14. 验证规则

schema 校验必须至少保证：

- 顶层必填字段存在
- 所有 rule `id` 唯一
- `source_refs` 必须能在 `sources` 中解析
- 数值型字段单位合法
- 枚举值合法
- `confidence` 在 `0-1`

## 15. MVP 最小子集

MVP 实现时，只要求落地以下部分：

- 顶层 `Spec`
- `rules`
- `sources`
- `pending_confirmations`
- 10 个左右高频属性
- 轻量 selector 语法

`exceptions` 和复杂 block 关系可以先保留字段，不要求首版完整执行。

