---
name: query-word-text
description: "Use this skill to search for paragraphs in a Word document by keyword. Triggers: when you need to locate specific content like '摘要', '宋体', '参考文献', formatting instructions, or any text pattern inside a .docx file. Returns matching paragraphs with index, style, and context. Do NOT use for style property queries — use query-word-style instead. Do NOT use for full document parsing — use parse-word instead."
---

# query-word-text

这是共享 capability skill，负责从 Word 文档中按关键词提取相关段落。

适用场景：

- 查“格式要求”“宋体”“字号”“摘要”等说明文字
- 为 `extract-spec` 提供说明文档线索
- 为 `check-thesis` 辅助定位摘要、目录、参考文献等区域

命令：

```bash
python3 -m sim_docs query-text <file_path> --keyword <keyword> [--output <output.json>]
```
