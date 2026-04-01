---
name: extract-spec
description: 从 Word 模板提取格式规则的 workflow skill。编排细粒度 capability skills、视觉核验和 gate skills，最终生成 spec.json。
---

# extract-spec

作为大模型（Claude），你现在的任务是编排多个 skills，自主提取格式规范并生成 `spec.json`。

目标不是把流程写死在一个脚本里，而是按 artifact 和验收门形成闭环。

## 阶段 1：全局数据提取 (Programmatic Context)

1. 第一时间调用 `parse-word` 获取完整 `DocumentIR`：
   `python3 .claude/skills/parse-word/scripts/run.py <file> [--output facts.json]`
2. 主动调用 `query-word-text` 搜索格式说明文字：
   `python3 .claude/skills/query-word-text/scripts/run.py <file> --keyword "格式要求"`
3. 主动调用 `query-word-style` 查询真实样式默认值：
   `python3 .claude/skills/query-word-style/scripts/run.py <file> --style "正文"`
4. 对 `body.paragraph`、`body.heading.level1/2/3`、`figure.caption`、`table.caption` 等关键 selector，按需调用 `infer-spec-fragment` 形成局部规则候选。

## 阶段 2：多模态视觉对抗校验 (Visual Verification)

当你对页面结构、页眉页脚、具体缩进等感到疑惑，或者发现“文字说明 / 样式定义 / 实际版面”互相冲突时：

1. 调用 `render-word-page` 生成截图：
   `python3 .claude/skills/render-word-page/scripts/run.py <file> --page <页码> --output temp_view.png`
2. 如果当前模型支持视觉，用视觉能力复核页面布局。
3. 如果当前模型不支持视觉，不要阻塞流程；继续走纯程序化路径，并显式标记不确定项。

推荐裁决顺序：

1. 程序化事实
2. 文本规范线索
3. 视觉核验
4. gate 验收反馈

## 阶段 3：草拟 Spec JSON 报告 (Synthesize & Draft)

1. 调用 `merge-spec-fragments` 或直接按该 skill 的契约合并 fragment。
2. 生成草稿版 `spec.json`。
3. 默认把产物写到**当前工作目录**下，使用清晰、可审阅的文件名，例如 `school-thesis-spec.json`。
4. 不要默认写到 `/tmp`，除非用户明确要求只做临时产物。
5. 如果存在冲突，不要静默覆盖；在输出中显式保留来源或待确认项。

## 阶段 4：调用验收技能（Closed-loop Validation）

你必须执行双重 gate 验收，而不是只做一次模糊自查：

```bash
python3 .claude/skills/validate-spec-structure/scripts/validate.py <your_spec.json>
python3 .claude/skills/validate-spec-coverage/scripts/validate.py <your_spec.json> --profile thesis-basic
```

兼容场景下，也可以调用旧入口：

```bash
python3 .claude/skills/validate-spec/scripts/validate.py <your_spec.json>
```

如果 gate 失败：

- 结构失败：回到 fragment 合并或 JSON 草拟阶段
- 覆盖失败：回到文本检索、样式查询或视觉核验阶段补取证据

绝对不要在 gate 失败时直接交付。
