---
name: extract-spec
description: "Use this skill to extract formatting rules from reference materials and produce a spec.md for user review. Triggers: when user provides a template (.docx/.dotm), a sample thesis, or a formatting guide document, and wants rules extracted. Output: a human-readable spec.md covering page setup, body text, headings, captions, abstract, references, TOC, headers/footers. Do NOT use for checking a document — use check-thesis instead. Do NOT use if rules are already written in a spec.md."
---

# extract-spec

从分散的参考材料收敛成一份自然语言规则文档 `spec.md`。

## 角色：调度者 + 评估者

**主 Agent 不直接执行任务**，而是：
1. 调度 subagent 执行具体提取任务
2. 评估 subagent 输出的完整性和正确性
3. 合并 subagent 输出到最终 spec.md

---

## 输入

- 模板文件：`.docx` / `.dotm` 或成品论文
- 说明文档：写明格式规则的文本

---

## 执行流程

### Step 1: 解析文档（主 Agent 执行）

```bash
python3 -m sim_docs parse <file.docx> --output facts.json
```

### Step 2: 调度 Subagent 并行提取

使用 Agent tool 调用：

**font-extractor subagent:**
```
Agent tool:
  description: "提取字体规则"
  prompt: |
    [使用 font-extractor-prompt.md 模板]
    
    输入文件：{file_path}
    facts 文件：{facts_path}
    目标样式：Normal, Heading 1, Heading 2, Heading 3, Heading 4, Caption
```

**layout-extractor subagent:**
```
Agent tool:
  description: "提取页面设置"
  prompt: |
    [使用 layout-extractor-prompt.md 模板]
    
    输入文件：{file_path}
    facts 文件：{facts_path}
```

**heading-extractor subagent:**
```
Agent tool:
  description: "提取标题规则"
  prompt: |
    [使用 heading-extractor-prompt.md 模板]
    
    输入文件：{file_path}
    facts 文件：{facts_path}
```

### Step 3: 评估 Subagent 输出（主 Agent 责任）

收集所有 subagent 返回后，执行评估层逻辑：

#### 3.1 检查 status 字段

| status | 处理 |
|--------|------|
| `DONE` | 继续评估 |
| `BLOCKED` | 报告阻塞原因，等待用户指导 |
| `NEEDS_CONTEXT` | 提示用户提供更多信息，重新 dispatch |

#### 3.2 检查 cross_validation 字段

**拒绝条件：**
- `cross_validation` 缺失 → 拒绝输出，标记为流程错误
- `cross_validation.sources` 不包含 `"paragraph_stats"` → 拒绝，要求重做
- `cross_validation.conflicts` 非空但无 resolution → 标记为"待确认项"

#### 3.3 检查 tool_errors 字段

**拒绝条件：**
- `tool_errors` 非空 → 报告流程异常，列出错误详情
- 不能忽略工具错误继续输出

#### 3.4 检查 common_sense_check 字段

**处理方式（根据 subagent 输出判断）：**

| subagent 输出 | 处理方式 |
|---------------|----------|
| `common_sense_check = pass` | ✅ 继续合并 |
| `common_sense_check = needs_revision` + 输出带 `⚠️ 待确认` 标注 | ✅ 合并输出，用户看到标注后自行修正 |
| `common_sense_check = needs_revision` + 输出为 null 或无标注 | ❌ 拒绝，询问用户后重新 dispatch |

**正确流程示例：**

```
font-extractor 输出：
{
  "status": "DONE",
  "output": {
    "font_rule": {
      "ascii_font": "⚠️ 待确认（模板使用 宋体）"
    }
  },
  "common_sense_check": "needs_revision"
}

主 Agent 评估：
  ✅ 输出带标注 → 合并输出
  
spec.md 结果：
  西文字体：⚠️ 待确认（模板使用 宋体）
  
用户看到标注后自行修正为正确值。
```

**错误流程示例：**

```
font-extractor 输出：
{
  "status": "NEEDS_CONTEXT",
  "output": { "font_rule": null },
  "common_sense_check": "needs_revision"
}

主 Agent 评估：
  ❌ 输出为 null → 拒绝
  → 询问用户："模板西文字体为宋体，正确应为？"
  → 重新 dispatch 带用户确认值
```

### Step 4: 处理拒绝情况（关键：处理循环）

如果任何 subagent 输出被拒绝，**主 Agent 不能自己填补缺失内容**，必须执行处理循环：

```
                        ┌───────────┐
                        │  拒绝检测 │
                        └──────┬────┘
                               │
                               ▼
               ┌───────────────────────────────────┐
               │          拒绝原因分类              │
               └───────────────────────────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ 流程错误    │         │ 常识冲突    │         │ 缺上下文    │
│ cross_valid │         │ common_sense│         │ NEEDS_CONTEXT│
│ 缺失        │         │ = needs_rev │         │             │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│重新 dispatch│         │ 询问用户    │         │ 询问用户    │
│带强制指令   │         │ 获取正确值  │         │获取缺失上下文│
└─────────────┘         └──────┬──────┘         └──────┬──────┘
                               │                       │
                               ▼                       ▼
                        ┌─────────────┐         ┌─────────────┐
                        │重新 dispatch│         │重新 dispatch│
                        │带用户确认值 │         │带补充上下文 │
                        └──────┬──────┘         └──────┬──────┘
                               │                       │
                               └───────────────┬───────┘
                                               │
                                               ▼
                                        (循环到 Step 3)
```

#### 4.1 拒绝原因 → 处理方式

| 拒绝原因 | 正确处理 | 禁止行为 |
|----------|----------|----------|
| `cross_validation` 缺失 | **重新 dispatch** subagent，指令中强调"必须调用 paragraph-stats 验证" | ❌ 主 Agent 自己调用 paragraph-stats |
| `cross_validation.sources` 缺少 paragraph_stats | **重新 dispatch**，强调"必须执行三源验证" | ❌ 主 Agent 自己验证 |
| `tool_errors` 非空 | **报告给用户**，列出错误详情，等待用户确认工具问题后继续 | ❌ 隐瞒错误继续输出 |
| `common_sense_check = needs_revision` + 输出带标注 | ✅ **合并输出**（用户看到标注后自行修正） | ❌ 主 Agent 自己修正标注内容 |
| `common_sense_check = needs_revision` + 输出为 null | **询问用户**，获取正确值后 **重新 dispatch** | ❌ 主 Agent 自己推断值 |
| `status` = `NEEDS_CONTEXT` | **询问用户**，获取后 **重新 dispatch** 带补充信息 | ❌ 主 Agent 自己填补缺失内容 |

#### 4.2 处理循环示例

**场景：font-extractor 返回 common_sense_check = needs_revision**

```
font-extractor 输出：
{
  "status": "DONE",
  "common_sense_check": "needs_revision",
  "common_sense_issues": ["ASCII font '宋体' 是中文字体"]
}

主 Agent 评估：
  ❌ common_sense_check ≠ pass → 拒绝
  
主 Agent 正确操作：
  1. 报告："font-extractor 检测到西文字体为中文字体（宋体）"
  2. 询问用户："模板中西文字体应使用什么？Times New Roman？"
  3. 用户回复："Times New Roman"
  4. 重新 dispatch font-extractor：
     prompt: "...西文字体已确认：Times New Roman..."
  
主 Agent 禁止操作：
  ❌ 自己写："西文字体：⚠️ 待确认"
  ❌ 自己写："西文字体：Times New Roman（推断）"
  ❌ 直接合并输出，跳过处理循环
```

**场景：font-extractor 返回 status = NEEDS_CONTEXT**

```
font-extractor 输出：
{
  "status": "NEEDS_CONTEXT",
  "cross_validation": {
    "text_instructions": {"found": false}
  }
}

主 Agent 正确操作：
  1. 报告："模板缺少明确的正文字体文字说明"
  2. 询问用户："是否有学校格式要求文档？或正文字体应使用什么？"
  3. 用户回复："学校要求正文宋体小四号，西文 Times New Roman"
  4. 重新 dispatch font-extractor 带用户确认值
  
主 Agent 禁止操作：
  ❌ 自己推断："正文宋体（推断）"
  ❌ 自己写："西文字体：Times New Roman（来自英文摘要规则）"
```

#### 4.3 处理循环最多 2 次

如果重新 dispatch 2 次后仍被拒绝：
- 标记为"待用户确认项"
- 继续合并其他通过的部分
- 在 spec.md 中列出未解决的问题

---

### Step 5: 合并输出（通过评估后）

将各 subagent 输出合并为 spec.md：

```markdown
# [论文格式规范]

## 页面设置
[使用 layout-extractor 输出]

## 正文
[使用 font-extractor 的 Normal 样式输出]

## 标题
[使用 heading-extractor 输出]

## 待确认项
[汇总 cross_validation.conflicts 中未解决的项]

## 工具错误记录
[汇总 tool_errors]
```

**合并原则：**
- 只拼接 subagent 输出，**不填补缺失内容**
- 缺失部分标注为"待确认"或"未提取"
- 不让主 Agent 做任何推断或猜测

---

## 评估层检查清单

主 Agent 必须执行以下检查：

| 检查项 | 通过条件 | 处理方式 |
|--------|----------|----------|
| cross_validation 存在 | ✅ | ❌ 缺失 → 重新 dispatch |
| cross_validation.sources 包含 paragraph_stats | ✅ | ❌ 缺失 → 重新 dispatch |
| tool_errors 为空数组 | ✅ | ⚠️ 非空 → 报告异常，等待用户确认 |
| common_sense_check = pass | ✅ | ⚠️ needs_revision + 带标注 → 合并输出 |
| common_sense_check = needs_revision + 无标注 | ❌ | ❌ 询问用户后重新 dispatch |
| status = DONE | ✅ | ❌ NEEDS_CONTEXT → 询问用户后重新 dispatch |

---

## 拒绝输出示例

```
❌ font-extractor 输出被拒绝

原因：
- cross_validation.sources 缺失 "paragraph_stats"
- common_sense_check = "needs_revision" (西文字体为宋体)

建议：
1. 重新 dispatch font-extractor，确保调用 paragraph-stats
2. 搜索文字说明确认西文字体要求
```

---

## Subagent Prompt 模板位置

- `font-extractor-prompt.md`
- `layout-extractor-prompt.md`
- `heading-extractor-prompt.md`

---

## ⚡ IRON LAW: 主 Agent 不执行任务

主 Agent 只负责：
- 调度 subagent
- 评估 subagent 输出
- 合并输出（拼接，不填补）
- 询问用户获取上下文
- 重新 dispatch 带修正指令

**禁止主 Agent 直接调用工具：**
- ❌ `query-word-style`
- ❌ `paragraph-stats`
- ❌ `query-word-text`
- ❌ 任何解析或查询工具

**禁止主 Agent 自己填补内容：**
- ❌ 自己推断缺失的字体值
- ❌ 自己写"待确认"的具体内容
- ❌ 自己决定如何处理 common_sense 问题
- ❌ 绕过 NEEDS_CONTEXT 直接写输出

**当 subagent 返回"做不到"时：**
- 必须询问用户
- 或重新 dispatch 明确指令
- 不能自己动手做