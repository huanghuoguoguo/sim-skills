# Spec Schema v0.1 草案

## 1. 目标

定义 `Spec` 的最小稳定结构，用于：

- 表达模板或规范的结构化规则
- 驱动 `schema + document -> 合规检查`
- 为后续扩展保留演进空间

本版不是"最全 schema"，而是 MVP 可执行的最小子集。

## 2. 设计原则

- schema-first：所有 AI 输出必须落在 schema 内
- engine-friendly：字段能被程序稳定执行
- versioned：允许规则迭代而不破坏历史结果
- docx-first：先服务 `.docx`，但命名不绑死在 Word

## 3. v0.1 收敛结论

v0.1 只稳定 3 类对象：

- `Spec`
- `Rule`
- `metadata`

## 4. 顶层对象

```json
{
  "spec_id": "demo-university-undergrad",
  "version": "0.1.0",
  "name": "某大学本科毕业论文格式规范",
  "scope": "undergraduate_thesis",
  "rules": [],
  "metadata": {
    "created_by": "system",
    "created_at": "2026-03-31T00:00:00Z",
    "source_files": ["template.docx"]
  }
}
```

## 5. 顶层字段定义

- `spec_id`
  全局稳定 ID，不含版本。
- `version`
  语义化版本，建议 `major.minor.patch`。
- `name`
  面向人的名称。
- `scope`
  规则适用范围，如 `undergraduate_thesis`。
- `rules`
  可执行规则列表。
- `metadata`
  非执行信息，包含来源文件、创建时间等。

## 6. `rules`

### 6.1 Rule 结构

```json
{
  "id": "body-style",
  "selector": "body.paragraph",
  "applies_to": "paragraph",
  "properties": {
    "font_family_zh": "宋体",
    "font_size_pt": 12,
    "line_spacing_pt": 20,
    "first_line_indent_chars": 2
  },
  "severity": "major"
}
```

### 6.2 Rule 字段定义

- `id`
  当前 spec 内唯一。
- `selector`
  目标对象定位语法。
- `applies_to`
  枚举：`paragraph | heading | caption | document`
- `properties`
  需要比较的属性集合。
- `severity`
  枚举：`critical | major | minor | info`

## 7. `selector`

MVP 采用轻量路径式 selector。

### 7.1 v0.1 允许值

- `document`
- `body.paragraph`
- `body.heading.level1`
- `body.heading.level2`
- `body.heading.level3`
- `figure.caption`
- `table.caption`

### 7.2 selector 约束

- selector 只描述目标对象，不内嵌复杂条件
- selector 的解析必须是确定性的

## 8. `properties`

### 8.1 v0.1 首批属性

| 字段 | 单位 | 说明 |
|------|------|------|
| `font_family_zh` | - | 中文字体 |
| `font_family_en` | - | 英文字体 |
| `font_size_pt` | pt | 字号 |
| `bold` | boolean | 加粗 |
| `italic` | boolean | 斜体 |
| `alignment` | - | 对齐方式 |
| `line_spacing_pt` | pt | 行距（固定值） |
| `space_before_pt` | pt | 段前距 |
| `space_after_pt` | pt | 段后距 |
| `first_line_indent_chars` | 字符 | 首行缩进 |
| `page_margin_top_cm` | cm | 上页边距 |
| `page_margin_bottom_cm` | cm | 下页边距 |
| `page_margin_left_cm` | cm | 左页边距 |
| `page_margin_right_cm` | cm | 右页边距 |

### 8.2 单位约定

- 字号：`pt`
- 行距：`pt`
- 段前段后：`pt`
- 缩进：`pt` 或 `chars`
- 页边距：`cm`

### 8.3 枚举约定

- `alignment`
  `left | center | right | justify`

## 9. Schema 版本策略

- `patch`
  不改变字段语义，仅修正文案或元数据
- `minor`
  新增可选字段或新增 rule type
- `major`
  改变字段语义、单位或 selector 解释逻辑

任何一次检查结果都必须绑定：
- `spec_id`
- `version`

## 10. 验证规则

schema 校验必须至少保证：

- 顶层必填字段存在
- 所有 rule `id` 唯一
- 数值型字段单位合法
- 枚举值合法

## 11. MVP 最小子集

MVP 实现时，只要求落地以下部分：

- 顶层 `Spec`
- `rules`
- 10 到 15 个高频属性
- 轻量 selector 语法

这版 schema 的目的是保证 parser、checker、extractor 先能对齐同一套结构。
