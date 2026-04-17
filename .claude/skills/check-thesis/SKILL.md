---
name: check-thesis
description: "Use this skill to check a .docx document against formatting rules and produce a Markdown report. Triggers: when user provides a Word document and formatting rules (from spec.md, PDF, plain text, or verbal description) and wants a compliance check. Uses batch-check for deterministic rules (font, size, spacing, margins) and Agent reasoning for semantic rules (abstract, references, TOC). Do NOT use for extracting rules — use extract-spec instead. Do NOT use for .doc or .pdf as the main check target."
---

# check-thesis

检查文档是否符合给定的格式规则，输出 Markdown 检查报告。

## 角色：调度者 + 评估者

**主 Agent 不直接执行检查**，而是：
1. 调度 rule-checker subagent 执行确定性规则检查
2. 调度 semantic-checker subagent 执行语义规则检查
3. 评估 subagent 输出的覆盖性
4. 合并检查结果为 Markdown 报告

---

## 输入

- 待检查文档：`.docx`
- 格式规则：spec.md 或其他来源

---

## 执行流程

### Step 1: 解析文档（主 Agent 执行）

```bash
python3 -m sim_docs parse <file.docx> --output facts.json
```

### Step 2: 调度 Subagent 并行检查

**rule-checker subagent:**
```
Agent tool:
  description: "执行确定性规则检查"
  prompt: |
    [使用 rule-checker-prompt.md 模板]
    
    文档 facts：{facts_path}
    spec.md：{spec_path}
```

**semantic-checker subagent:**
```
Agent tool:
  description: "执行语义规则检查"
  prompt: |
    [使用 semantic-checker-prompt.md 模板]
    
    文档 facts：{facts_path}
    spec.md：{spec_path}
```

### Step 3: 评估 Subagent 输出（主 Agent 责任）

#### 3.1 检查 status 字段

| status | 处理 |
|--------|------|
| `DONE` | 继续评估 |
| `NEEDS_CONTEXT` | 报告需要人工确认的项 |

#### 3.2 检查 coverage_status（rule-checker）

**⚠️ 关键检查：**
- `coverage_status.checked` 必须覆盖 spec.md 中所有确定性规则
- `coverage_status.skipped` 必须有合理理由（如文档不包含此类段落）
- `coverage_status.errors` 非空 → 报告错误，可能需要修正 style_aliases

#### 3.3 检查 completeness_traceback

验证所有原始规则都有检查状态：
- 不能有规则既不在 checked 也不在 skipped

#### 3.4 检查 needs_human_review（semantic-checker）

- 记录需要人工确认的语义规则
- 不能假设"应该没问题"就跳过

### Step 4: 处理覆盖性问题

如果 rule-checker 报告 coverage 不完整：

1. 检查是否 style_aliases 有误
2. 建议补充缺失的样式名
3. 重新 dispatch rule-checker

### Step 5: 合并输出为 Markdown 报告

```markdown
# 论文格式检查报告

## 确定性规则检查

### 通过项
[rule-checker coverage_status.checked 中 pass 的项]

### 不通过项
[rule-checker coverage_status.checked 中 fail 的项]

### 不适用
[rule-checker coverage_status.skipped 的项]

## 语义规则检查

### Agent 判断
[semantic-checker output.semantic_results]

### 待人工确认
[semantic-checker output.needs_human_review]

## 完整性核对

| 原始规则 | 检查状态 | 来源 |
|---------|---------|------|
| 正文字体 | ✅ pass | batch-check |
| 封面格式 | ⚠️ 待人工确认 | semantic |

## 工具错误记录
[汇总 tool_errors]
```

---

## 评估层检查清单

| 检查项 | 通过条件 | 失败后果 |
|--------|----------|----------|
| coverage_status.checked 覆盖所有确定性规则 | ✅ | ❌ 重新 dispatch |
| completeness_traceback = done | ✅ | ❌ 报告遗漏 |
| tool_errors 为空 | ✅ | ⚠️ 报告异常 |
| needs_human_review 已列出 | ✅ | ⚠️ 补充列表 |

---

## ⚡ IRON LAW: 所有规则必须有检查状态

**主 Agent 必须核实 completeness_traceback 结果。**

每条原始规则必须有状态：
- ✅ 已检查（pass 或 fail）
- ⚠️ 不适用（文档不包含）
- ⏳ 待人工确认（语义规则）

**禁止：**
- 有规则无状态
- 有规则被跳过无理由
- 假设"应该没问题"就标记 pass

---

## Subagent Prompt 模板位置

- `rule-checker-prompt.md`
- `semantic-checker-prompt.md`