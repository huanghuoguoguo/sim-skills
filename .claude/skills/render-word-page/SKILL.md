---
name: render-word-page
description: 将 Word 文档指定页渲染成图片，用于支持视觉能力的模型做版式复核。
---

# render-word-page

这是一个 capability skill，负责把 `.docx` / `.dotm` 的某一页渲染成 PNG。

适用场景：

- 文本说明和样式定义冲突
- 需要人工或多模态模型核对版式观感

命令：

```bash
python3 .claude/skills/render-word-page/scripts/run.py <file_path> --page <page_num> --output <image.png>
```
