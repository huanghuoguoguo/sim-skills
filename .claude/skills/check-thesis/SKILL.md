---
name: check-thesis
description: 基于 spec.json 检查论文格式合规性。作为 workflow skill 编排解析、比对和报告验收。
---

# check-thesis

检查论文文档是否符合给定的格式规范，输出问题列表和 Markdown 报告。

## 设计说明

本 skill 是格式检查的 workflow 层，负责：

- 调用 `parse-word` 获取结构事实
- 根据 spec 执行规则比对
- 产出 `report.json` 和 Markdown 报告
- 调用 `validate-report` 做最终验收

### 依赖关系

`check-thesis` -> `parse-word` -> rule matching -> `validate-report`

当需要解析论文时，优先使用 `parse-word`，不再直接依赖 `word` 聚合 skill。

## 使用指南

当用户需要检查论文格式时：

### 步骤 1：准备输入

- **论文文件**：找到待检查的 `.docx` 文件
- **Spec 文件**：确认已有 `spec.json`（没有则先调用 `extract-spec` 提取）

### 步骤 2：执行检查

```bash
python3 .claude/skills/check-thesis/scripts/run.py <thesis_path> <spec_json_path>
```

### 步骤 3：处理输出并验收

输出包含：
- `issues`: 问题列表（位置、期望值、实际值）
- `issues_by_severity`: 按严重程度分类的统计
- 同时生成 `<thesis_name>_check_report.md` 可读报告

如果输出到 JSON 文件，随后调用：

```bash
python3 .claude/skills/validate-report/scripts/validate.py <report.json>
```

推荐把 `report.json` 和 Markdown 报告都写到当前工作目录，便于用户人工复核，不要默认写入临时目录。

## 命令格式

```bash
python3 .claude/skills/check-thesis/scripts/run.py <thesis_path> <spec_json_path> [--output <output.json>]
```

**参数说明**：
- `thesis_path`: 待检查论文路径（支持 glob 通配符）
- `spec_json_path`: Spec JSON 文件路径
- `--output`: JSON 结果输出路径（默认输出到 stdout）

## 输出示例

```json
{
  "thesis": "论文.docx",
  "spec": "规范名称",
  "issue_count": 10,
  "issues_by_severity": { "critical": 0, "major": 10, "minor": 0, "info": 0 },
  "issues": [
    {
      "rule_id": "rule-body-paragraph",
      "severity": "major",
      "location": { "paragraph_index": 5, "text_preview": "..." },
      "expected": { "font_size_pt": 10.5 },
      "actual": { "font_size_pt": 12.0 },
      "message": "正文格式不符合要求...",
      "fixable": true
    }
  ]
}
```

## 相关文件

- 执行脚本：`.claude/skills/check-thesis/scripts/run.py`
- 解析能力：`.claude/skills/parse-word/scripts/run.py`
- 报告验收：`.claude/skills/validate-report/scripts/validate.py`
