---
name: query-word-style
description: 查询 Word 文档中的样式定义和默认属性。适合核对“正文”“标题”等真实样式配置。
---

# query-word-style

这是一个 capability skill，负责检索样式层面的真实默认值。

适用场景：

- 核对 `正文`、`标题 1` 等样式配置
- 为 spec 提取提供样式依据
- 输出会优先给出**归一化后的 schema 友好属性**，并保留 `raw_properties`

命令：

```bash
python3 .claude/skills/query-word-style/scripts/run.py <file_path> --style <style_name>
```
