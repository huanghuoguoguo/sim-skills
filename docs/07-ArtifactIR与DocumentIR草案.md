# Artifact IR 与 DocumentIR v0.1 草案

## 1. 目标

定义 parser 输出的最小稳定中间表示，用于：

- 屏蔽 `.docx` 底层格式差异
- 为 `Fact Extraction` 和 `Comparator / Rule Engine` 提供稳定输入
- 为报告中的定位、追溯和调试提供依据

v0.1 的实际落点是 `DocumentIR`。`Artifact IR` 只保留为命名层抽象，不额外追求泛化设计。

## 2. 设计原则

- parser 输出事实，不直接输出判断结果
- 原始样式与实际生效格式尽量同时保留
- 所有可比较对象都要有稳定 ID
- 单位统一，避免后续比较时重复换算
- 能从 IR 回溯到源位置
- 无法可靠判断的页面级信息应显式留空，而不是伪造结果

## 3. v0.1 收敛结论

v0.1 只稳定 4 类对象：

- `DocumentIR`
- `Style`
- `Block`
- `Relation`

本版明确做以下收敛：

- `properties` 保存“实际生效的归一化值”
- `style_ref` 保存样式来源，不用它代替实际格式
- `role` 允许启发式推断，但要保留 `role_source` 与 `role_confidence`
- 不承诺精确页码、物理坐标、断页结果

## 4. 实现降级策略

为了避免在 parser 阶段重写半个 Word 渲染引擎，v0.1 在代码实现上允许以下降级：

- 不追求完整样式级联求值，只保留样式引用、direct formatting 与可稳定读取的实际值
- `properties` 只填“低成本可稳定获得”的归一化属性
- `source_map` 以用户可定位为目标，不要求首版能回溯到底层 XML xpath
- 当格式是否违规依赖复杂继承或页面渲染时，允许交由 checker 做保守判断或直接留空

## 5. 顶层结构

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

## 6. 顶层字段定义

- `artifact_id`
  当前解析任务中的稳定 ID。
- `artifact_type`
  v0.1 固定为 `docx`。
- `ir_type`
  固定为 `document`。
- `schema_version`
  IR 本身的版本。
- `metadata`
  来源文件、标题、语言等信息。
- `layout`
  文档级页面设置。
- `styles`
  解析到的样式定义与继承关系。
- `blocks`
  归一化内容块列表。
- `relations`
  块之间的从属、引用、顺序关系。
- `source_map`
  从 IR 对象回溯到源位置的映射。

## 7. `metadata` 与 `layout`

示例：

```json
{
  "metadata": {
    "filename": "thesis.docx",
    "title": "某大学本科毕业论文",
    "language": "zh-CN",
    "estimated_page_count": 42
  },
  "layout": {
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
}
```

说明：

- `estimated_page_count` 可以有，但不代表精确分页
- v0.1 不给 block 绑定真实页码

## 8. `styles`

保留样式定义，供规则抽取和调试使用。

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

## 9. `blocks`

`blocks` 是最核心的执行对象。每个 block 都应该可被 selector 命中。

### 9.1 Block 通用结构

```json
{
  "id": "p-001",
  "block_type": "paragraph",
  "role": "body.paragraph",
  "role_source": "style",
  "role_confidence": 0.97,
  "order": 1,
  "style_ref": "style-正文",
  "text": "这是正文第一段。",
  "properties": {},
  "property_sources": {},
  "children": []
}
```

字段建议：

- `id`
  全局唯一。
- `block_type`
  `section | paragraph | run | table | figure | caption | toc_entry`
- `role`
  归一化语义角色，如 `body.heading.level1`。
- `role_source`
  `style | outline | text_pattern | heuristic | inherited | structure | unknown`
- `role_confidence`
  角色识别置信度，范围 `0-1`。
- `order`
  文档内稳定顺序。
- `style_ref`
  引用 `styles[].id`，没有则为 `null`。
- `text`
  当前 block 文本。
- `properties`
  实际生效的归一化属性。
- `property_sources`
  属性来源，如 `style | direct | inherited | heuristic | unknown`。
- `children`
  子节点 ID。

### 9.2 Section Block

```json
{
  "id": "sec-body",
  "block_type": "section",
  "role": "body",
  "role_source": "heuristic",
  "role_confidence": 0.88,
  "order": 3,
  "properties": {
    "title": "正文"
  },
  "children": ["p-101", "p-102"]
}
```

### 9.3 Paragraph Block

```json
{
  "id": "p-101",
  "block_type": "paragraph",
  "role": "body.paragraph",
  "role_source": "style",
  "role_confidence": 0.97,
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
  "property_sources": {
    "alignment": "style",
    "line_spacing_pt": "style",
    "first_line_indent_chars": "direct"
  },
  "children": ["r-101-1", "r-101-2"]
}
```

### 9.4 Run Block

```json
{
  "id": "r-101-1",
  "block_type": "run",
  "role": "body.run",
  "role_source": "inherited",
  "role_confidence": 1.0,
  "order": 101001,
  "text": "这是",
  "properties": {
    "font_family_zh": "宋体",
    "font_size_pt": 12,
    "bold": false,
    "italic": false
  },
  "property_sources": {
    "font_family_zh": "style",
    "bold": "direct"
  }
}
```

### 9.5 Caption Block

```json
{
  "id": "cap-figure-1",
  "block_type": "caption",
  "role": "figure.caption",
  "role_source": "text_pattern",
  "role_confidence": 0.91,
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

### 9.6 Table Block

首版不必把表格每个单元格都做全量检查，但结构先保留。

```json
{
  "id": "tbl-001",
  "block_type": "table",
  "role": "body.table",
  "role_source": "structure",
  "role_confidence": 1.0,
  "order": 210,
  "properties": {
    "row_count": 4,
    "column_count": 3
  }
}
```

## 10. `relations`

用于表达跨 block 关系。

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

## 11. `source_map`

用于把 IR 节点回溯到原始输入，便于调试和报告。

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

## 13. 单位、ID 与归一化规则

- 页面尺寸、页边距：统一转为 `cm`
- 字号、行距、段前段后：统一转为 `pt`
- 布尔属性：统一 `true/false`
- 空值与缺省值分开表示，不要混用
- 文本原文保留，归一化值单独存储在 `properties`

ID 建议：

- section：`sec-*`
- paragraph：`p-*`
- run：`r-*`
- table：`tbl-*`
- figure：`fig-*`
- caption：`cap-*`
- style：`style-*`

要求：

- 在单次解析结果中全局唯一
- 与文档顺序一致，便于调试
- 不依赖用户原始样式名作为唯一标识

## 14. Parser Spike 需要先验证的难点

在写完整 parser 前，先做一个最小 spike，专门验证以下问题：

- 样式与 direct formatting 并存时，能否同时保留 `style_ref` 与实际生效属性
- 用户未正确套用标题样式时，能否通过文本模式或启发式识别 `body.heading.level1`
- 题注未使用专用样式时，能否通过文本模式识别 `figure.caption` 与 `table.caption`
- 对无法可靠计算的页面级规则，能否显式输出 `N/A` 而不是误判

## 15. MVP 最小子集与非目标

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

parser 负责：

- 读取输入格式
- 提取结构
- 做单位归一化
- 输出稳定 ID
- 保留样式来源与实际生效值

parser 不负责：

- 判断是否违规
- 推断学校规则
- 生成问题描述
- 合并业务级例外逻辑
