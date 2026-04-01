---
name: extract-spec
description: 从 Word 模板提取格式规则的 Agent 工作流入口。结合了底层解析数据与多模态视觉对比，最终生成符合标准的 JSON 结构。
---

# extract-spec

作为大模型（Claude），你现在的任务是自主提取格式规范并生成 Spec JSON。请彻底摒弃死板的脚本执行，采用以下**Agentic Workflow**：

## 阶段 1：全局数据提取 (Programmatic Context)

1. 第一时间读取目标文件（如 `template.dotm` 或 `.docx`）的全局结构。
2. 使用 `python3 .claude/skills/word/scripts/parse.py <file>` 获取完整的段落属性和文档结构。
3. 主动使用 `python3 .claude/skills/word/scripts/query_text.py <file> --keyword "格式要求"` 或者搜索 "宋体", "字号", "正文", "模板" 等关键字，提取包含要求说明的原始文本段落。
4. 主动使用 `python3 .claude/skills/word/scripts/query_style.py <file> --style "正文"` 等查询底层真实的样式的默认值配置。

## 阶段 2：多模态视觉对抗校验 (Visual Verification)

对于许多复杂的排版要求，仅靠底层 XML 会丢失大量信息。当你对页面结构、页眉页脚、具体缩进等感到疑惑，或看到文本描述与底层 XML 不一致时：

1. **生成观测样本（截图）**：
   使用多模态辅助工具 `python3 .claude/skills/word/scripts/render_page.py <file> --page <页码> --output temp_view.png` 截取你关心的页码（强烈建议截取第一页封面和第五页正文区）。
2. **多模态阅卷**：使用你能使用的方式“看”这张图片，核实真实的排版到底长什么样。
3. **矛盾裁决**：当文字指南、XML 样式和实际视觉截图出现矛盾时，应以文字描述和真切的截图观感为主！

## 阶段 3：草拟 Spec JSON 报告 (Synthesize & Draft)

你需要亲自生成并写入草稿版的 `spec.json`。此时，要求你尽可能保证数据结构的完整性。

## 阶段 4：调用验收技能（Closed-loop Validation）

为了防止你遗漏重要字段或输出残缺的 JSON，你必须执行严格的**多粒度架构闭环验收**：

调用全新的验收技能 `validate-spec`（或者你直接执行该技能里的校验脚本）：
```bash
python3 .claude/skills/validate-spec/scripts/validate.py <your_spec.json>
```

**【接收反馈与补偿提取】**：
如果 `validate.py` 报错提示你“缺少 `body.paragraph`”或者“缺少 `layout.page_margins`”，这说明**这份论文的字段提取没有形成闭环**。
此时，**绝对不允许就此交差**！你需要老老实实地回到阶段1或阶段2，针对缺少的 `body.paragraph` 进行重新提取推断，然后把它补全到 JSON 里，直到重新运行 `validate.py` 不再有遗漏报错为止！
