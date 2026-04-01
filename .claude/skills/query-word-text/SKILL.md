---
name: query-word-text
description: 在 Word 文档中按关键词检索原始文本段落。适合查找格式说明、规范提示和特定术语。
---

# query-word-text

这是一个 capability skill，负责从 Word 文档中按关键词提取相关段落。

适用场景：

- 查“格式要求”“宋体”“字号”“摘要”等说明文字
- 为 `extract-spec` 提供文字线索

命令：

```bash
python3 .claude/skills/query-word-text/scripts/run.py <file_path> --keyword <keyword>
```
