---
name: evaluate-spec
description: "Use this skill to evaluate a spec.md for quality before user review or downstream checking. Triggers: after extract-spec produces a spec.md, or when user wants to validate an existing spec. Checks coverage (page setup, body, headings, captions, abstract, references), specificity, consistency, and traceability. Output: pass / needs_revision / blocked_user_input. Do NOT use for checking a document against rules — use check-thesis for that. Do NOT use for extracting rules — use extract-spec."
---

# evaluate-spec

评估 `spec.md` 的质量，不负责把规则重新结构化。

## 角色：调度者 + 评估者

**主 Agent 不直接执行检查**，而是：
1. 调度 evaluator subagent 执行程序化检查
2. 评估 subagent 输出的完整性
3. 核实检查覆盖所有必要维度

---

## 执行流程

### Step 1: 调度 evaluator subagent

使用 Agent tool 调用：

```
Agent tool:
  description: "评估 spec.md 质量"
  prompt: |
    [使用 evaluator-prompt.md 模板]
    
    spec.md 文件：{spec_path}
    
    # 加载 profile schema
    from thesis_profiles import load_profile, get_section_rules_for_structure_check
    profile = load_profile()
    section_rules = get_section_rules_for_structure_check(profile)
```

**⚠️ evaluator subagent 需要接收 profile schema：**
- evaluator 使用 `spec-check --mode structure` 时，传入 `section_rules` 参数
- `section_rules` 从 `profile.spec_schema.sections` 构建（仅 required sections）

### Step 2: 评估 subagent 输出（主 Agent 责任）

#### 2.1 检查 status 字段

| status | 处理 |
|--------|------|
| `DONE` | 检查是否真的通过所有检查 |
| `BLOCKED` | 报告阻塞原因（通常是 common-sense check 失败） |
| `NEEDS_CONTEXT` | 提示用户提供更多信息 |

#### 2.2 检查 common_sense_check 字段

**⚠️ 关键检查：**
- `common_sense_check` 必须是 `"pass"`
- 如果是 `"needs_revision"`，整个评估失败，必须退回修正 spec.md

#### 2.3 检查 cross_validation 字段

验证所有检查都已执行：
- `cross_validation.common_sense` 必须存在
- `cross_validation.structure` 必须存在
- `cross_validation.conflicts` 必须存在

**区分 required vs optional missing sections：**
- `missing_sections` 应仅包含 `required: true` 的 sections
- `optional_sections_missing` 作为信息性报告（不影响评估结果）

#### 2.4 检查 tool_errors 字段

- `tool_errors` 非空 → 报告工具错误，评估结果可能不可靠

### Step 3: 处理评估结果

**如果 evaluator 返回 BLOCKED（common-sense check 失败）：**

1. 报告失败原因
2. 列出 spec.md 中需要修正的行
3. 建议修正方案
4. 等待用户修正后重新评估

**如果 evaluator 返回 DONE 但有 issues：**

1. 报告 issues 列表（缺失章节、内部冲突）
2. 建议修正方案
3. 标记为 `needs_revision`

### Step 4: 输出最终评估结果

```
评估结果：pass / needs_revision / blocked_user_input

Profile schema: {profile_name}

检查通过项：
- common-sense check: ✅
- structure check: ✅ (required sections)
- conflicts check: ✅

缺失的 Required Sections：
- [列出 missing_required_sections]

缺失的 Optional Sections (仅信息性):
- [列出 optional_sections_missing]

存在问题：
- [列出 issues]

工具错误：
- [列出 tool_errors]
```

---

## 评估层检查清单

| 检查项 | 通过条件 | 失败后果 |
|--------|----------|----------|
| common_sense_check = pass | ✅ | ❌ 整体评估失败 |
| cross_validation.common_sense 存在 | ✅ | ❌ 流程错误，重新 dispatch |
| cross_validation.structure 存在 | ✅ | ⚠️ 报告缺失 |
| cross_validation.conflicts 存在 | ✅ | ⚠️ 报告缺失 |
| tool_errors 为空 | ✅ | ⚠️ 报告异常 |

---

## ⚡ IRON LAW: Common-Sense Check 必须先通过

**主 Agent 必须核实 evaluator 的 common_sense_check 结果。**

如果 evaluator 返回 `common_sense_check = needs_revision`：
- 不能输出 `pass`
- 不能跳过修正
- 必须报告冲突详情并要求修正 spec.md

---

## Subagent Prompt 模板位置

- `evaluator-prompt.md`