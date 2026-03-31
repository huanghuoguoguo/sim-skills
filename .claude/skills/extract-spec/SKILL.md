---
name: extract-spec
description: 从 Word 模板或规范文件中提取格式规则草案，内置 AI 校对。
---

# extract-spec

从 Word 文档（.docx / .dotm）中提取格式规则，输出结构化 Spec JSON。

## 设计说明

本 skill 是规则提取的业务逻辑层，**不包含文档解析代码**，而是通过调用底层的 Word 解析服务获取文档数据。

### 依赖关系

```
extract-spec (业务逻辑)
    ↓
word (解析服务)
```

当需要解析 Word 文档时，应确保 `word` skill 的解析器可用。

## 使用指南

当用户需要从模板提取格式规范时：

### 步骤 1：找到模板文件

从用户指定位置或项目目录中查找 Word 模板文件：
- 扩展名：`.docx` 或 `.dotm`
- 典型位置：`fixtures/templates/`、用户指定的目录

### 步骤 2：调用技能

```bash
python3 .claude/skills/extract-spec/scripts/run.py <template_path> [--output <output.json>]
```

### 步骤 3：处理输出

输出包含：
- `rules`: 提取的规则列表
- `pending_confirmations`: AI 生成的待确认项（需要用户确认）
- `metadata`: 提取元数据

## 命令格式

```bash
python3 .claude/skills/extract-spec/scripts/run.py <template_path> [guidelines ...] [--output <output.json>]
```

**参数说明**：
- `template_path`: 模板文件路径（支持 glob 通配符，如 `*.dotm`）
- `guidelines`: 可选的规范文本文件列表
- `--output`: 输出文件路径（默认输出到 stdout）

## 输出示例

```json
{
  "spec_id": "spec-xxx",
  "version": "0.1.0-draft",
  "rules": [
    {
      "id": "rule-body-paragraph",
      "selector": "body.paragraph",
      "properties": { "font_family_zh": "宋体", "font_size_pt": 10.5 },
      "confidence": 0.95
    }
  ],
  "pending_confirmations": [
    {
      "rule_id": "rule-body-paragraph",
      "question": "正文是否要求首行缩进 2 字符？",
      "suggestion": "中文论文通常要求首行缩进 2 字符",
      "confidence": "high"
    }
  ]
}
```

## 相关文件

- 执行脚本：`.claude/skills/extract-spec/scripts/run.py`
- 依赖服务：`.claude/skills/word/scripts/parse.py`（Word 文档解析）
