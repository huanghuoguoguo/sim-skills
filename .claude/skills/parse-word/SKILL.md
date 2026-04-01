---
name: parse-word
description: 解析 .docx/.dotm 并输出标准化 DocumentIR。用于任何需要读取 Word 文档结构事实的流程。
---

# parse-word

这是一个 capability skill，负责把 `.docx` 或 `.dotm` 解析成稳定的 `DocumentIR`。

适用场景：

- 需要段落、样式、layout 等结构事实
- 需要为 `extract-spec`、`check-thesis`、`compare-docs` 提供统一输入

命令：

```bash
python3 .claude/skills/parse-word/scripts/run.py <file_path> [--output <output.json>]
```

输出重点：

- `metadata`
- `layout`
- `paragraphs`
- `styles`
