---
name: batch-check
description: "Use this skill to compare document facts against expected formatting rules. Triggers: when checking font, font_size, alignment, line_spacing, margins, indentation, page_size, or captions against expected values. Input: facts JSON (or .docx) + check instructions JSON. Output: per-check pass/fail/unresolved results. Run with --schema to see all supported check types. Do NOT use for semantic rules (abstract format, references, TOC) — those require Agent judgment."
---

# batch-check

通用的确定性属性比对工具。输入是文档事实 + 检查指令列表，输出是逐条比对结果。

不关心规则从哪来，不关心文档是什么类型——只做"给定事实和期望，逐条比对"。

## 命令

```bash
# 查看支持的 check 类型和字段
python3 -m sim_docs check --schema

# 执行比对
python3 -m sim_docs check <facts.json|file.docx> <checks.json> [--output result.json]
```

- `facts`: parse-word 输出的 JSON，或直接传 .docx/.dotm（内部自动解析）
- `checks`: 检查指令 JSON 文件，格式为 `[...]` 或 `{"checks": [...]}`

## 支持的 check 类型

运行 `--schema` 获取完整定义。摘要：

| type | 比对目标 | expected 格式 |
|------|----------|---------------|
| `font` | 字体族 | 字符串，scope 可选 east_asia/ascii |
| `font_size` | 字号 | 数值（pt） |
| `alignment` | 对齐方式 | left/center/right/justify/distribute |
| `line_spacing` | 行距 | `{"mode": "multiple|exact|at_least", "value": N}` |
| `spacing_before` | 段前间距 | 数值（pt） |
| `spacing_after` | 段后间距 | 数值（pt） |
| `first_line_indent` | 首行缩进 | 数值（pt） |
| `margin` | 页边距 | 数值（cm），需指定 side |
| `page_size` | 纸张大小 | "A4" |

## 段落选择器（selector）

- `style:<name>` — 按样式名匹配，结合 `style_aliases` 做模糊匹配
- `caption:figure` / `caption:table` — 按 `style_aliases` 或 `caption_prefix_patterns` 匹配题注
- `document:layout` — 文档级属性（margin、page_size 自动使用）

## 输出结构

```json
{
  "summary": {"total": 10, "pass": 8, "fail": 1, "unresolved": 1},
  "results": [
    {
      "id": "check-1",
      "type": "font_size",
      "status": "pass | fail | unresolved",
      "expected": "小四（12pt）",
      "actual": "300 ok",
      "matched_count": 300,
      "issues": []
    }
  ],
  "issues": []
}
```

输入校验失败时返回 `{"errors": [...]}` 并不执行任何比对。

## 进阶参考

完整 check 指令示例、中文字号映射表、Troubleshooting 指南见 [REFERENCE.md](REFERENCE.md)。
