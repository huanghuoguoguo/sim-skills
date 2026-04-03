---
name: compare-docs
description: "Use this skill to compare formatting differences between two Word documents. Triggers: when user provides a reference .docx/.dotm and a target .docx/.dotm and wants to see what formatting properties differ (page layout, margins, paragraph styles, fonts, spacing). Output: JSON diff list + Markdown report. Do NOT use for rule-based compliance checking — use check-thesis for that. Do NOT use for .doc or .pdf files."
---

# compare-docs

比对两份 Word 文档的格式差异，输出差异列表和 Markdown 报告。

## 设计说明

本 skill 是文档比对的业务逻辑层，**不包含文档解析代码**，而是通过调用底层解析能力获取两份文档的数据。

### 依赖关系

```
compare-docs (业务逻辑)
    ↓
parse-word (共享解析能力)
```

当需要解析文档时，优先使用 `parse-word`，不要把 `word` 当成业务入口。

## 使用指南

当用户需要比对两份文档格式时：

### 步骤 1：找到两份文档

- **参考文档**：作为基准的 `.docx` 或 `.dotm` 文件
- **目标文档**：待比对的 `.docx` 或 `.dotm` 文件

### 步骤 2：调用技能

```bash
python3 .claude/skills/compare-docs/scripts/run.py <reference_path> <target_path>
```

### 步骤 3：处理输出

输出包含：
- `diffs`: 差异列表（类型、方面、参考值、目标值）
- 同时生成 `<target_name>_diff_report.md` 可读报告

## 命令格式

```bash
python3 .claude/skills/compare-docs/scripts/run.py <reference_path> <target_path> [--output <output.json>]
```

**参数说明**：
- `reference_path`: 参考文档路径（支持 glob 通配符）
- `target_path`: 目标文档路径（支持 glob 通配符）
- `--output`: JSON 结果输出路径（默认输出到 stdout）

## 输出示例

```json
{
  "reference": "ref.docx",
  "target": "target.docx",
  "diff_count": 5,
  "diffs": [
    {
      "type": "structure",
      "aspect": "paragraph_count",
      "reference": 100,
      "target": 98,
      "message": "段落数量不一致：参考=100, 目标=98"
    },
    {
      "type": "layout",
      "aspect": "page_margins.top_cm",
      "reference": 2.54,
      "target": 3.0,
      "message": "上边距：参考=2.54, 目标=3.0"
    }
  ]
}
```

## 相关文件

- 执行脚本：`.claude/skills/compare-docs/scripts/run.py`
- 解析能力：`.claude/skills/parse-word/scripts/run.py`
