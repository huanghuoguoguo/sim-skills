---
name: paragraph-stats
description: "Use this skill to filter paragraphs by style/content and compute property distributions. Triggers: when you need to know what fonts, sizes, line spacings, or indentations are actually used by a class of paragraphs (e.g., body text, headings). Essential for cross-validating style definitions against actual paragraph properties. Input: facts JSON or .docx, with optional filters (--style-hint, --min-length, --require-body-shape). Output: style/font/size/spacing distributions and sample paragraphs. Do NOT use for single-style property lookup — use query-word-style for that."
---

# paragraph-stats

通用段落筛选 + 属性分布统计工具。

输入文档事实，按条件过滤段落，输出字号、行距、缩进、字体等属性的分布统计。不假设文档类型，所有过滤条件通过参数传入。

## 命令

```bash
python3 -m sim_docs stats <facts.json|file.docx> [options]
```

## 参数

| 参数 | 说明 |
|------|------|
| `--style-hint HINT` | 只保留匹配的样式名（可重复） |
| `--exclude-text TEXT` | 排除包含该文本的段落（可重复） |
| `--heading-prefix REGEX` | 排除匹配的标题前缀（可重复） |
| `--heading-keyword KW` | 排除以该关键词开头的段落（可重复） |
| `--instruction-hint HINT` | 排除说明性文字（可重复） |
| `--min-length N` | 最短段落字符数（默认 0） |
| `--require-body-shape` | 只保留两端对齐或有首行缩进的段落 |
| `--sample-limit N` | 最多返回的样例数（默认 8） |
| `--output PATH` | 输出文件路径 |

所有过滤参数都是可选的。不传任何过滤参数时，返回所有非空段落的统计。

## 输出结构

```json
{
  "input": "file.docx",
  "filters": {"style_hints": [...], "min_length": 20, ...},
  "summary": {
    "candidate_count": 150,
    "style_distribution": [{"value": "Normal", "count": 140}],
    "font_size_distribution": [{"value": 12.0, "count": 135}],
    "line_spacing_distribution": [{"value": "multiple:1.5", "count": 130}],
    "first_line_indent_distribution": [{"value": 21.0, "count": 128}],
    "east_asia_font_distribution": [{"value": "宋体", "count": 120}],
    "ascii_font_distribution": [{"value": "Times New Roman", "count": 90}],
    "candidate_examples": [...]
  }
}
```
