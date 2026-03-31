# Artifact IR 与 DocumentIR 草案

## 1. 目标

定义 parser 输出的统一中间表示，用于：

- 屏蔽不同 artifact 类型的底层格式差异
- 为 `Fact Extraction` 和 `Comparator / Rule Engine` 提供稳定输入
- 为报告中的定位、追溯和调试提供依据

本草案分两层：

- `Artifact IR`：通用抽象
- `DocumentIR`：当前 `.docx` 场景下的具体实现

## 2. 设计原则

- parser 输出事实，不直接输出判断结果
- 原始值与归一化值尽量同时保留
- 所有可比较对象都要有稳定 ID
- 单位统一，避免后续比较时重复换算
- 能从 IR 回溯到源位置

## 3. 顶层结构

```json
{
  "artifact_id": "artifact-001",
  "artifact_type": "docx",
  "ir_type": "document",
  "schema_version": "0.1.0",
  "metadata": {},
  "layout": {},
  "styles": [],
  "blocks": [],
  "relations": [],
  "source_map": {}
}
```

## 4. 顶层字段定义

- `artifact_id`
  当前解析任务中的稳定 ID。
- `artifact_type`
  输入格式，如 `docx`、`pdf_text`、`html`。
- `ir_type`
  当前建议：`document`。
- `schema_version`
  IR 本身的版本。
- `metadata`
  来源文件、页数估计、标题等信息。
- `layout`
  页面级与全局布局信息。
- `styles`
  解析到的样式定义与继承关系。
- `blocks`
  归一化内容块列表。
- `relations`
  块之间的从属、引用、顺序关系。
- `source_map`
  从 IR 对象回溯到源位置的映射。

## 5. `metadata`

示例：

```json
{
  "filename": "thesis.docx",
  "title": "某大学本科毕业论文",
  "language": "zh-CN",
  "estimated_page_count": 42
}
```

## 6. `layout`

文档级布局与页面设置。

示例：

```json
{
  "page_size": {
    "width_cm": 21.0,
    "height_cm": 29.7
  },
  "page_margins": {
    "top_cm": 2.5,
    "bottom_cm": 2.5,
    "left_cm": 3.0,
    "right_cm": 2.5
  },
  "header_distance_cm": 1.5,
  "footer_distance_cm": 1.75
}
```

## 7. `styles`

保留样式定义，供规则抽取和调试使用。

示例：

```json
[
  {
    "id": "style-正文",
    "name": "正文",
    "style_type": "paragraph",
    "based_on": null,
    "properties": {
      "font_family_zh": "宋体",
      "font_size_pt": 12,
      "line_spacing_mode": "exact",
      "line_spacing_pt": 20
    }
  }
]
```

字段建议：

- `id`
- `name`
- `style_type`
  `paragraph | character | table | numbering`
- `based_on`
- `properties`

## 8. `blocks`

`blocks` 是最核心的执行对象。每个 block 都应该可被 selector 命中。

### 8.1 Block 通用结构

```json
{
  "id": "p-001",
  "block_type": "paragraph",
  "role": "body.paragraph",
  "order": 1,
  "style_ref": "style-正文",
  "text": "这是正文第一段。",
  "properties": {},
  "children": []
}
```

字段建议：

- `id`
  全局唯一。
- `block_type`
  `section | paragraph | run | table | row | cell | figure | caption | toc_entry`
- `role`
  归一化语义角色，如 `body.heading.level1`。
- `order`
  文档内稳定顺序。
- `style_ref`
  引用 `styles[].id`。
- `text`
  当前 block 文本。
- `properties`
  已归一化属性。
- `children`
  子节点 ID 或内联子块。

## 9. DocumentIR 的 block 细化

### 9.1 Section Block

用于表达封面、摘要、目录、正文、参考文献等逻辑区块。

```json
{
  "id": "sec-body",
  "block_type": "section",
  "role": "body",
  "order": 3,
  "properties": {
    "title": "正文"
  },
  "children": ["p-101", "p-102"]
}
```

### 9.2 Paragraph Block

```json
{
  "id": "p-101",
  "block_type": "paragraph",
  "role": "body.paragraph",
  "order": 101,
  "style_ref": "style-正文",
  "text": "这是正文段落。",
  "properties": {
    "alignment": "justify",
    "line_spacing_mode": "exact",
    "line_spacing_pt": 20,
    "space_before_pt": 0,
    "space_after_pt": 0,
    "first_line_indent_chars": 2
  },
  "children": ["r-101-1", "r-101-2"]
}
```

### 9.3 Run Block

```json
{
  "id": "r-101-1",
  "block_type": "run",
  "role": "body.run",
  "order": 101001,
  "text": "这是",
  "properties": {
    "font_family_zh": "宋体",
    "font_size_pt": 12,
    "bold": false,
    "italic": false
  }
}
```

### 9.4 Caption Block

```json
{
  "id": "cap-figure-1",
  "block_type": "caption",
  "role": "figure.caption",
  "order": 220,
  "text": "图 1-1 系统架构图",
  "properties": {
    "caption_kind": "figure",
    "caption_position": "below",
    "alignment": "center",
    "font_family_zh": "宋体",
    "font_size_pt": 9
  }
}
```

### 9.5 Table / Cell Block

首版不必把表格每个单元格都做全量检查，但结构先保留。

```json
{
  "id": "tbl-001",
  "block_type": "table",
  "role": "body.table",
  "order": 210,
  "properties": {
    "row_count": 4,
    "column_count": 3
  },
  "children": ["cell-1-1", "cell-1-2"]
}
```

## 10. `relations`

用于表达跨 block 关系。

示例：

```json
[
  {
    "type": "caption_of",
    "from": "cap-figure-1",
    "to": "fig-001"
  },
  {
    "type": "belongs_to_section",
    "from": "p-101",
    "to": "sec-body"
  }
]
```

常用关系：

- `belongs_to_section`
- `caption_of`
- `follows`
- `references`

## 11. `source_map`

用于把 IR 节点回溯到原始输入，便于调试和报告。

示例：

```json
{
  "p-101": {
    "xml_part": "word/document.xml",
    "xpath": "/w:document/w:body/w:p[101]"
  },
  "style-正文": {
    "xml_part": "word/styles.xml",
    "xpath": "/w:styles/w:style[@w:styleId='BodyText']"
  }
}
```

## 12. Fact 提取边界

`Fact` 不应直接塞进 IR 顶层，而应由 `Fact Extraction` 从 IR 计算得到。

原因：

- IR 保持通用与可回溯
- Fact 可按不同 checker 需求投影
- 避免 parser 直接承载业务规则

### 12.1 Fact 示例

```json
{
  "fact_id": "fact-p-101-line-spacing",
  "subject_id": "p-101",
  "subject_type": "paragraph",
  "selector_role": "body.paragraph",
  "property": "line_spacing_pt",
  "value": 20,
  "unit": "pt"
}
```

## 13. 单位与归一化规则

- 页面尺寸、页边距：统一转为 `cm`
- 字号、行距、段前段后：统一转为 `pt`
- 布尔属性：统一 `true/false`
- 空值与缺省值分开表示，不要混用
- 文本原文保留，归一化值单独存储在 `properties`

## 14. 命名与 ID 规则

- section：`sec-*`
- paragraph：`p-*`
- run：`r-*`
- table：`tbl-*`
- cell：`cell-*`
- figure：`fig-*`
- caption：`cap-*`
- style：`style-*`

要求：

- 在单次解析结果中全局唯一
- 与文档顺序一致，便于调试
- 不依赖用户原始样式名作为唯一标识

## 15. MVP 最小子集

MVP parser 只要求稳定输出：

- `metadata`
- `layout`
- `styles`
- `section / paragraph / run / caption / table` 级别的 `blocks`
- `relations`
- `source_map`

MVP 不要求：

- 精确页码定位
- 全量表格单元格样式
- 复杂图形对象结构
- PDF 或 HTML 的完整 IR

## 16. 解析器边界

parser 负责：

- 读取输入格式
- 提取结构
- 做单位归一化
- 输出稳定 ID

parser 不负责：

- 判断是否违规
- 推断学校规则
- 生成问题描述
- 合并业务级例外逻辑

