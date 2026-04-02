---
name: query-word-style
description: 查询 Word 文档中的样式最终属性值，适合核对正文、标题等真实样式配置。
---

# query-word-style

这是共享 capability skill，负责检索样式层面的最终解析值。

适用场景：

- 核对 `正文`、`标题 1` 等样式配置
- 为 `extract-spec` 提供样式依据
- 当模板里存在继承链时，确认最终生效的属性值

关键要求：

- 优先返回最终解析后的值，而不是“未设置”
- 样式解析应遵循继承链：直接格式 > 当前样式 > 父样式 > 文档默认
- 保留原始属性作为补充证据

命令：

```bash
python3 .claude/skills/query-word-style/scripts/run.py <file_path> --style <style_name>
```
