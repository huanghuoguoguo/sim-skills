---
name: render-word-page
description: "Use this skill to render a specific page of a Word document as a PNG image. Triggers: when text-based facts are insufficient to resolve a formatting conflict and visual verification is needed, or when the user explicitly asks to see a page. Do NOT use as the default inspection path — prefer structured tools (parse-word, query-word-style, paragraph-stats) first. Only use for visual arbitration when structural data is ambiguous."
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
python3 -m sim_docs render <file_path> --page <page_num> --output <image.png>
```
