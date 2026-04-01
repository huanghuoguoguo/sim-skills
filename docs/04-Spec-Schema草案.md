# Spec Schema v0.1 草案

## 1. 目标

定义一份简单、可消费、可维护的 `spec.json`。

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

## 3. 顶层对象

```json
{
  "spec_id": "demo-university-undergrad",
  "version": "0.1.0",
  "name": "某大学本科毕业论文格式规范",
  "scope": "undergraduate_thesis",
  "source_files": ["template.docx"],
  "layout": {
    "page_margins": {
      "top_cm": 2.54,
      "bottom_cm": 2.54,
      "left_cm": 3.0,
      "right_cm": 2.5
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
  适用范围，例如 `undergraduate_thesis`。
- `source_files`
  提取所依据的模板或成品文件。
- `layout`
  页面布局的基础信息。
- `rules`
  当前程序可以直接消费的规则列表。

## 5. `rules`

### 5.1 Rule 结构

```json
{
  "id": "body-style",
  "selector": "body.paragraph",
  "properties": {
    "font_family_zh": "宋体",
    "font_size_pt": 12,
    "line_spacing_pt": 20,
    "first_line_indent_pt": 24
  },
  "severity": "major"
}
```

### 5.2 Rule 字段定义

- `id`
  当前 spec 内唯一。
- `selector`
  目标对象定位语法。
- `properties`
  需要比较的属性集合。
- `severity`
  可选，枚举：`critical | major | minor | info`

## 6. `selector`

当前只建议在 `spec.json` 中放入程序真正能消费的 selector。

v0.1 推荐范围：

- `body.paragraph`
- `body.heading.level1`
- `body.heading.level2`
- `body.heading.level3`
- `figure.caption`
- `table.caption`

其他说明性规则：

- 不要求进 `spec.json`
- 优先写进 `spec.md`

## 7. `properties`

### 7.1 当前推荐属性

| 字段 | 单位 | 说明 |
|------|------|------|
| `font_family_zh` | - | 中文字体 |
| `font_family_en` | - | 英文字体 |
| `font_size_pt` | pt | 字号 |
| `bold` | boolean | 加粗 |
| `italic` | boolean | 斜体 |
| `alignment` | - | 对齐方式 |
| `line_spacing_pt` | pt | 行距 |
| `space_before_pt` | pt | 段前距 |
| `space_after_pt` | pt | 段后距 |
| `first_line_indent_pt` | pt | 首行缩进 |
| `first_line_indent_chars` | 字符 | 首行缩进 |

### 7.2 不建议进入 `spec.json` 的内容

这些更适合写进 `spec.md`：

- 大段说明文字
- 依据和证据原文
- 编号规则说明
- 数量要求
- 当前程序还不支持的 section 规则
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

`validate-spec` 至少保证：

- 顶层字段存在
- `rules` 结构合法
- 最小规则覆盖足够
- `rules` 中的 selector / property 当前程序可以消费

## 10. MVP 最小子集

MVP 只要求：

- 一个简单 `spec.json`
- 一个同目录的 `spec.md`
- `rules` 中包含最小可消费规则
- 先把“可消费”做稳，再逐步扩展
