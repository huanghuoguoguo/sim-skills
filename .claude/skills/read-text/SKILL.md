---
name: read-text
description: "Use this skill to read plain text content from .txt, .md, or .docx files. Triggers: when you need the raw text content of a file for processing, or when another skill needs text input from a document. Output: JSON with text content and line count. Do NOT use for structured Word document parsing (style properties, layout) — use parse-word instead. Do NOT use for keyword search — use query-word-text instead."
---

# read-text

读取文本文件并输出 JSON 格式的内容。

## 能力说明

本技能提供文本文件读取能力：

1. 读取 `.txt`、`.md` 或 `.docx` 文件
2. 输出纯文本内容和行数统计
3. 统一输出格式，便于后续处理

## 使用指南

当用户需要读取文本文件内容时：

1. **找到文件**：从用户指定位置或项目目录中查找文本文件
2. **调用技能**：使用下方命令格式执行
3. **处理输出**：从 JSON 中获取 `text` 字段

## 命令格式

```bash
python3 -m sim_docs read-text <file_path>
```

**参数说明**：
- `file_path`: 文件路径（支持 glob 通配符）

## 输出结构

```json
{
  "input": "file.txt",
  "text": "文件内容...",
  "line_count": 100
}
```

## 相关文件

- CLI 入口：`sim_docs/cli.py`
- 依赖库：`.claude/skills/__libs__/text_sources.py`（文本读取）
