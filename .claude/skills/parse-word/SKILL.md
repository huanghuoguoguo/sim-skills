---
name: parse-word
description: "Use this skill to parse .docx or .dotm files into structured facts (DocumentIR). Triggers: when any other skill or workflow needs paragraph properties, style definitions, page layout, or header/footer content from a Word document. Produces JSON output with metadata, layout, paragraphs (with font, font_size, alignment, line_spacing, indentation), styles, headers, and footers. Do NOT use for .doc or .pdf files. Do NOT use for editing or creating documents — this is read-only extraction."
---

# parse-word

这是共享 capability skill，负责把 `.docx` 或 `.dotm` 解析成稳定的结构化事实。

适用场景：

- `extract-spec` 需要抽取模板和成品论文中的事实
- `check-thesis` 需要拿到论文的段落、样式和页面设置
- 其他工具需要统一的文档解析基础

命令：

```bash
python3 .claude/skills/parse-word/scripts/run.py <file_path> [--output <output.json>]
```

输出重点：

- `metadata`
- `layout`
- `paragraphs`
- `styles`
- `headers` / `footers` 等附加结构事实（如果解析器提供）
