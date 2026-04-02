---
name: query-word-text
description: 在 Word 文档中按关键词检索段落，用于查找格式说明、规范提示和语义线索。
---

# query-word-text

这是共享 capability skill，负责从 Word 文档中按关键词提取相关段落。

适用场景：

- 查“格式要求”“宋体”“字号”“摘要”等说明文字
- 为 `extract-spec` 提供说明文档线索
- 为 `check-thesis` 辅助定位摘要、目录、参考文献等区域

命令：

```bash
python3 .claude/skills/query-word-text/scripts/run.py <file_path> --keyword <keyword> [--output <output.json>]
```
