---
name: agent-check-report
description: 基于 LLM 的格式检查技能，对 Python 程序跳过的规则进行智能判断。
---

# agent-check-report

这个 skill 负责：

**使用 LLM 的语义理解能力，对 `check-thesis` 跳过的规则进行智能格式检查。**

## 适用场景

当 `check-thesis` 输出 `skipped_rules` 时，这些规则通常是：
- `frontmatter.abstract.zh.*` - 中文摘要相关
- `frontmatter.abstract.en.*` - 英文摘要相关
- `frontmatter.keywords.*` - 关键词相关
- `frontmatter.toc.*` - 目录相关
- `backmatter.references.*` - 参考文献相关
- `frontmatter.title_page.*` - 封面相关

Python 程序无法识别这些 selector，但 LLM 可以通过语义分析 facts.json 中的段落信息进行判断。

## 输入

- `thesis.docx` - 论文文件（或直接使用已有的 `facts.json`）
- `spec.json` - 格式规范
- `check-thesis` 输出的 `report.json`（包含 `skipped_rules`）

## 输出

- `agent_report.json` - 增强的检查报告，包含对 skipped_rules 的判断结果

## 工作流程

### 1. 读取输入

```bash
# 如果没有 facts.json，先解析论文
python3 .claude/skills/parse-word/scripts/run.py <thesis.docx> --output facts.json
```

### 2. 分析 skipped_rules

对于每条 skipped rule：

1. 从 `spec.json` 获取规则的 `selector` 和 `properties`
2. 从 `facts.json` 中查找匹配的段落
   - 根据 selector 语义匹配（如 `abstract.zh` 匹配包含"摘要"的段落）
   - 根据 style_name 匹配（如 `Abstract`、`摘要` 等样式）
3. 比对段落 properties 与规则要求
4. 输出判断结果

### 3. 输出增强报告

```json
{
  "original_report": {...},
  "agent_checks": [
    {
      "rule_id": "abstract-zh-content",
      "selector": "frontmatter.abstract.zh.content",
      "status": "pass|fail|uncertain",
      "matched_paragraphs": [{"index": 10, "text": "..."}],
      "expected": {"font_family_east_asia": "宋体", ...},
      "actual": {"font_family_east_asia": "宋体", ...},
      "message": "中文摘要内容格式符合要求",
      "confidence": 0.95
    }
  ],
  "summary": {
    "total_skipped": 13,
    "checked_pass": 10,
    "checked_fail": 2,
    "uncertain": 1
  }
}
```

## 命令格式

```bash
python3 .claude/skills/agent-check-report/scripts/run.py <facts.json> <spec.json> <report.json> [--output agent_report.json]
```

## Selector 匹配策略

| Selector | 匹配策略 |
|----------|----------|
| `frontmatter.abstract.zh.*` | style_name 含"摘要"或 text 含"摘要"且位于文档前部 |
| `frontmatter.abstract.en.*` | style_name 含"Abstract"或 text 含"Abstract" |
| `frontmatter.keywords.zh.*` | text 含"关键词" |
| `frontmatter.keywords.en.*` | text 含"Key words" |
| `frontmatter.toc.*` | style_name 含"TOC"或"目录" |
| `backmatter.references.*` | style_name 含"Reference"或"参考文献"，或 text 含"[1]"等引用标记 |
| `frontmatter.title_page.*` | 文档前 10 段，包含论文题目、作者等信息 |

## 与 check-thesis 的区别

| 特性 | check-thesis | agent-check-report |
|------|-------------|-------------------|
| 执行方式 | Python 程序硬编码判断 | LLM 语义分析 + 规则匹配 |
| 速度 | 快 | 较慢 |
| 准确性 | 确定性规则准确 | 模糊规则更智能 |
| 适用 selector | 有限的预定义列表 | 任意语义化 selector |
