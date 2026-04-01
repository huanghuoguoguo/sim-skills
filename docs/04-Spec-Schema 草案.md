# Spec Schema v0.2

## 1. 目标

定义一份简单、可维护、可消费的 `spec.json`。

约束很明确：

- `spec.json` 给程序和下游 agent 消费
- 人类可读说明不强塞进 JSON
- 说明、依据、疑问、待确认项放到同目录下的 `spec.md`

也就是说，最终交付物是一个简单的 spec 包：

```text
spec/
└── <spec-id>/
    ├── spec.json
    └── spec.md
```

## 2. 设计原则

- simple-first：先保证简单和可维护
- machine-consumable：JSON 只保留机器真正要消费的内容
- human-readable：解释和依据放到 Markdown
- versioned：允许规则迭代
- agentic-friendly：验证默认宽松，允许任意 selector/property

## 3. 顶层对象

```json
{
  "spec_id": "tjut-thesis",
  "version": "1.0.0",
  "name": "天津理工大学硕士学位论文格式规范",
  "scope": "master_thesis",
  "source_files": ["template.dotm"],
  "layout": {
    "page_size": {"width_cm": 21.0, "height_cm": 29.7},
    "page_margins": {
      "top_cm": 2.54,
      "bottom_cm": 2.54,
      "left_cm": 3.57,
      "right_cm": 2.77
    }
  },
  "rules": []
}
```

## 4. 顶层字段定义

- `spec_id`
  全局稳定 ID，不含版本。
- `version`
  语义化版本。
- `name`
  面向人的名称。
- `scope`
  适用范围，例如 `master_thesis`。
- `source_files`
  提取所依据的模板或成品文件。
- `layout`
  页面布局的基础信息（可选）。
- `rules`
  当前程序可以直接消费的规则列表。

## 5. `rules`

### 5.1 Rule 结构

```json
{
  "id": "body-paragraph",
  "selector": "body.paragraph",
  "properties": {
    "font_family_east_asia": "宋体",
    "font_family_ascii": "Times New Roman",
    "font_size_pt": 10.5,
    "alignment": "justify",
    "line_spacing_pt": 18.0,
    "first_line_indent_pt": 24.0
  },
  "severity": "major"
}
```

### 5.2 Rule 字段定义

- `id`
  当前 spec 内唯一。
- `selector`
  目标对象定位语法（不再限制预定义列表）。
- `properties`
  需要比较的属性集合。
- `severity`
  可选，枚举：`critical | major | minor | info`

## 6. `selector`

### 6.1 支持的 Selector（Python 检查器）

以下 selector 由 Python 程序直接检查：

- `body.paragraph`
- `body.heading.level1` ~ `level4`
- `figure.caption`
- `table.caption`

### 6.2 语义化 Selector（Agent 检查器）

以下 selector 由 `agent-check-report` 通过语义匹配检查：

- `frontmatter.title_page.*` - 封面
- `frontmatter.abstract.zh.*` - 中文摘要
- `frontmatter.abstract.en.*` - 英文摘要
- `frontmatter.keywords.zh.*` - 中文关键词
- `frontmatter.keywords.en.*` - 英文关键词
- `frontmatter.toc.*` - 目录
- `backmatter.references.*` - 参考文献
- `backmatter.acknowledgements.*` - 致谢
- `backmatter.appendix.*` - 附录

### 6.3 Selector 语法说明

v0.2 不再限制 selector 的具体值，允许：

- 任意嵌套结构（如 `frontmatter.abstract.zh.content`）
- 自定义扩展（如 `body.equation.numbered`）

无法被 Python 检查器识别的 selector 会自动进入 `skipped_rules`，由 Agent 检查。

## 7. `properties`

### 7.1 支持的属性

| 字段 | 单位 | 说明 |
|------|------|------|
| `font_family` | - | 字体（向后兼容） |
| `font_family_east_asia` | - | 中文字体 |
| `font_family_ascii` | - | 英文字体 |
| `font_size_pt` | pt | 字号 |
| `bold` | boolean | 加粗 |
| `italic` | boolean | 斜体 |
| `alignment` | - | 对齐方式 (left/center/right/justify) |
| `line_spacing_mode` | - | 行距模式 (single/multiple/exact/at_least) |
| `line_spacing_value` | - | 行距值 |
| `line_spacing_pt` | pt | 行距 |
| `space_before_pt` | pt | 段前距 |
| `space_after_pt` | pt | 段后距 |
| `first_line_indent_pt` | pt | 首行缩进 |
| `first_line_indent_chars` | 字符 | 首行缩进（字符数） |
| `page_margin_top_cm` | cm | 上页边距 |
| `page_margin_bottom_cm` | cm | 下页边距 |
| `page_margin_left_cm` | cm | 左页边距 |
| `page_margin_right_cm` | cm | 右页边距 |

### 7.2 不建议进入 `spec.json` 的内容

这些更适合写进 `spec.md`：

- 大段说明文字
- 依据和证据原文
- 编号规则说明
- 数量要求（如"参考文献不少于 50 篇"）
- 模糊或待确认项

## 8. `spec.md`

`spec.md` 是人类可读层。

建议包含：

- 页面设置摘要
- 正文/标题/图表题注等规则的人类说明
- 提取依据
- 当前不确定项
- 当前未进入 `spec.json` 的补充规则

用户如果要人工修改，优先改 `spec.md`，再让 agent 同步更新 `spec.json`。

## 9. 验证规则

`validate-spec` 验证：

- 顶层字段存在（spec_id, name, version, rules）
- `rules` 结构合法（每个 rule 有 id, selector, properties）
- 基本类型正确

v0.2 变更：

- 默认 `--strict=false`，不限制 selector/property 的具体值
- 使用 `--strict` 标志时，检查预定义的 selector 和 property 支持列表

## 10. 混合检查模式

```
check-thesis
    ↓
Python 检查支持的 selector
    ↓
输出 issues + skipped_rules
    ↓
agent-check-report
    ↓
语义匹配 skipped_rules
    ↓
输出 agent_checks
```

这种模式保证：

- 确定性规则由 Python 快速检查
- 语义化规则由 Agent 智能判断
- 两种检查结果格式一致，便于下游消费

## 11. MVP 最小子集

MVP 只要求：

- 一个简单 `spec.json`
- 一个同目录的 `spec.md`
- `rules` 中包含最小可消费规则
- 先把"可消费"做稳，再逐步扩展
