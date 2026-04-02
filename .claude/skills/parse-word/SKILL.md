---
name: parse-word
description: 解析 .docx/.dotm 并输出结构化事实，用于规则提取和论文检查的共享基础能力。
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
