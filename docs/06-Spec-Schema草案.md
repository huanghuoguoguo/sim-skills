# Spec Schema v0.1 草案

## 1. 目标

定义系统中 `Spec` 的最小稳定结构，用于：

- 表达模板或规范的结构化规则
- 驱动 `spec -> artifact` 合规检查
- 为后续 `artifact -> artifact` 差异比对保留演进空间

本版不是“最全 schema”，而是 MVP 可执行的最小子集。

## 2. 设计原则

- schema-first：所有 AI 输出必须落在 schema 内
- engine-friendly：字段能被程序稳定执行
- source-aware：每条规则都能追溯来源
- uncertainty-aware：支持待确认项与置信度
- versioned：允许规则迭代而不破坏历史结果
- docx-first, engine-generic：先服务 `.docx`，但命名不绑死在 Word

## 3. v0.1 收敛结论

v0.1 只稳定 4 类对象：

- `Spec`
- `Rule`
- `Source`
- `PendingConfirmation`

本版明确做以下收敛：

- 文档级约束不单独建 `document_constraints`，统一写成 `selector = document` 的规则
- 逻辑区块不单独建 `content_blocks`，由 `DocumentIR` 中的 `role` 与 `selector` 对齐
- `exceptions` 不进入首版执行闭环
- selector 不引入 `where`、`:first` 之类复杂条件

## 4. 实现降级策略

为了避免 MVP 陷入工程沼泽，schema 在代码中的首版实现允许进一步降级：

- `selector` 在运行时先作为路由键使用，例如直接映射到 `get_body_paragraphs()` 这类固定函数
- 不要求先实现通用 selector DSL 解析器
- 规则只覆盖 5 到 10 条高频检查，不追求“通用规则系统”一步到位
- 当规则依赖页面真实渲染结果时，允许返回 `N/A` 或暂不纳入首版

## 5. 顶层对象

```json
{
  "spec_id": "demo-university-undergrad",
  "version": "0.1.0",
  "status": "draft",
  "name": "某大学本科毕业论文格式规范",
  "artifact_type": "document",
  "scope": "undergraduate_thesis",
  "rules": [],
  "sources": [],
  "pending_confirmations": [],
  "metadata": {
    "created_by": "system",
    "created_at": "2026-03-31T00:00:00Z"
  }
}
```

## 6. 顶层字段定义

- `spec_id`
  全局稳定 ID，不含版本。
- `version`
  语义化版本，建议 `major.minor.patch`。
- `status`
  枚举：`draft | reviewed | published | archived`。
- `name`
  面向人的名称。
- `artifact_type`
  v0.1 固定为 `document`。
- `scope`
  规则适用范围，如 `undergraduate_thesis`。
- `rules`
  可执行规则列表。
- `sources`
  来源文件与来源片段。
- `pending_confirmations`
  抽取时无法自动确认的候选项。
- `metadata`
  非执行信息。

## 7. `rules`

### 7.1 Rule 结构

```json
{
  "id": "body-style",
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
  "enabled": true,
  "source_refs": ["src-template-body-style"],
  "confidence": 0.96,
  "message_template": "正文段落格式不符合要求。"
}
```

### 7.2 Rule 字段定义

- `id`
  当前 spec 内唯一。
- `type`
  v0.1 建议枚举：
  `style_rule | layout_rule | structure_rule | caption_rule`
- `selector`
  目标对象定位语法。
- `applies_to`
  枚举：`document | section | paragraph | run | table | caption | entry`
- `properties`
  需要比较的属性集合。
- `severity`
  枚举：`critical | major | minor | info`
- `enabled`
  是否启用。
- `source_refs`
  指向 `sources[].id`，建议必填；人工补录场景可允许空数组。
- `confidence`
  规则可信度，范围 `0-1`，人工确认后的发布版可省略。
- `message_template`
  默认错误文案模板，可选。

### 7.3 设计约束

- 一个 rule 只表达一组同 selector、同 applies_to 的约束
- 文档级约束也走 rule，不再单列顶层对象
- 规则只表达“要求值”，不表达例外逻辑

## 8. `selector`

MVP 采用轻量路径式 selector，后续再扩展更通用语法。

### 8.1 v0.1 允许值

- `document`
- `cover`
- `abstract.zh.body`
- `body.heading.level1`
- `body.heading.level2`
- `body.paragraph`
- `figure.caption`
- `table.caption`
- `references.entry`

### 8.2 selector 约束

- selector 只描述目标对象，不内嵌业务判断
- selector 的解析必须是确定性的
- v0.1 不支持 `where`、`:first`、复杂布尔条件

## 9. `properties`

### 9.1 v0.1 首批属性

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

## 10. `sources`

每条规则必须尽可能可追溯。

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

## 11. `pending_confirmations`

用于承接 AI 或规则抽取中的不确定项。

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

字段建议：

- `id`
- `selector`
- `candidate_property`
- `candidate_value`
- `reason`
- `source_refs`
- `confidence`

## 12. 延后到 v0.2 之后的能力

- `exceptions`
- 独立的 `content_blocks`
- 独立的 `document_constraints`
- 复杂 selector 条件与 rule override
- rule group、rule inheritance、条件启停

这些能力不是不做，而是不该阻塞 `spec -> artifact` 的首版闭环。

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
- 10 到 15 个高频属性
- 轻量 selector 语法

这版 schema 的目的不是一次抽象完，而是保证 parser、checker、spec builder 先能对齐同一套结构。
