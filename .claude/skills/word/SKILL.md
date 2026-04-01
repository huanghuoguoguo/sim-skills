---
name: word
description: 兼容聚合 skill。内部仍承载 Word 解析脚本，但新 workflow 应优先使用 parse-word、query-word-text、query-word-style、render-word-page。
---

# Word Document Service

**兼容聚合服务** - 仍然承载底层脚本，但新的 workflow 不应再直接把它当作唯一入口。

## 设计说明

本 skill 是纯粹的解析服务，不包含任何业务逻辑，专注于：
1. 解析 `.docx` 或 `.dotm` 文件
2. 输出标准化的 DocumentIR（Document Intermediate Representation）

### 推荐替代 skills

```
word/scripts/*
 ├── parse-word
 ├── query-word-text
 ├── query-word-style
 └── render-word-page
```

保留 `word` 的原因是兼容已有脚本路径和现有 skill 说明。

## 使用指南

### 直接调用（调试或独立使用）

```bash
# 解析文档，输出到 stdout
python3 .claude/skills/word/scripts/parse.py <file_path>

# 输出到文件
python3 .claude/skills/word/scripts/parse.py <file_path> --output <output.json>
```

### 被其他 Skill 调用（推荐方式）

在其他 skill 的 Python 脚本中导入解析器：

```python
# 添加 word/scripts 到 sys.path
from pathlib import Path
import sys

word_scripts = Path(__file__).parent.parent.parent / "word" / "scripts"
if str(word_scripts) not in sys.path:
    sys.path.insert(0, str(word_scripts))

# 导入解析器和模型
from docx_parser import parse_word_document
from docx_parser_models import ParagraphFact, StyleFact, WordDocumentFacts

# 使用
facts = parse_word_document("document.docx")
paragraphs = facts.paragraphs
styles = facts.styles
```

## 命令格式

```bash
python3 .claude/skills/word/scripts/parse.py <file_path> [--output <output.json>]
```

**参数说明**：
- `file_path`: Word 文档路径（支持 glob 通配符，如 `*.docx`）
- `--output`: 输出文件路径（默认输出到 stdout）

## 输出结构 (DocumentIR)

```json
{
  "format": "docx",
  "metadata": {
    "filename": "论文.docx",
    "paragraph_count": 500
  },
  "layout": {
    "page_size": { "width_cm": 21.0, "height_cm": 29.7 },
    "page_margins": { "top_cm": 2.54, "bottom_cm": 2.54 }
  },
  "paragraphs": [
    {
      "id": "p-1",
      "index": 0,
      "text": "段落文本",
      "style_name": "Normal",
      "style_id": "a0",
      "properties": {
        "font_family": "宋体",
        "font_size_pt": 10.5,
        "alignment": "left"
      }
    }
  ],
  "styles": [
    {
      "name": "Normal",
      "style_id": "a0",
      "properties": { "font_family": "宋体", "font_size_pt": 10.5 }
    }
  ]
}
```

## 相关文件

- 执行脚本：`.claude/skills/word/scripts/parse.py`
- 解析器：`.claude/skills/word/scripts/docx_parser.py`
- 数据模型：`.claude/skills/word/scripts/docx_parser_models.py`
