---
name: word
description: "Internal low-level Word parser library. Do NOT call directly from workflows — use the higher-level capability skills instead: parse-word (full document parsing), query-word-text (keyword search), query-word-style (style property query), render-word-page (page rendering). This module provides shared implementation code (docx_parser.py, docx_parser_models.py) consumed by those skills."
---

# word

这是底层共享能力，不是主要 workflow skill。

## 定位

- 承载 `word/scripts/*` 下的解析器和模型
- 给 `parse-word`、`query-word-text`、`query-word-style`、`render-word-page` 提供共享实现

新的工作流不要直接把 `word` 当成业务入口；优先调用更清晰的 capability skills：

- `parse-word`
- `query-word-text`
- `query-word-style`
- `render-word-page`

## 调试入口

```bash
python3 .claude/skills/word/scripts/parse.py <file_path>
```

## 供其他脚本复用

在 Python 脚本中导入：

```python
from pathlib import Path
import sys

word_scripts = Path(__file__).parent.parent.parent / "word" / "scripts"
if str(word_scripts) not in sys.path:
    sys.path.insert(0, str(word_scripts))

# 导入解析器和模型
from docx_parser import parse_word_document
from docx_parser_models import WordDocumentFacts
```
