---
name: render-word-page
description: 将 Word 文档指定页渲染成图片，用于版式冲突仲裁和视觉复核。
---

# render-word-page

这是共享 capability skill，负责把 `.docx` / `.dotm` 的某一页渲染成 PNG。

适用场景：

- 文本说明和样式定义冲突
- 需要核对页面上的实际版式表现

约束：

- 只在常规结构事实不足以裁决时使用
- 不要把它当成默认路径，优先使用结构化工具

命令：

```bash
python3 .claude/skills/render-word-page/scripts/run.py <file_path> --page <page_num> --output <image.png>
```
