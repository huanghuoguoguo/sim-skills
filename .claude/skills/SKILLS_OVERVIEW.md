# Skills Overview

This document provides a navigation map for all skills in `.claude/skills/`.

## Purpose

Skills are the building blocks for document formatting workflows. They follow an **Agent + generic tools** architecture:
- **Capability skills** provide fine-grained, generic tools (parse, query, check)
- **Workflow skills** orchestrate capabilities for specific use cases (extract spec, check thesis)
- **Meta skills** manage the change lifecycle itself (OpenSpec workflow)

## Skill Categories

| Category | Skills | Purpose |
|----------|--------|---------|
| **Core Parsing** | `parse-word` | Foundation: docx/dotm → structured facts (JSON) |
| **Query/Stats** | `query-word-text`, `query-word-style`, `paragraph-stats` | Search and analyze parsed content |
| **Validation** | `batch-check`, `validate-word` | Compare against rules or OOXML schemas |
| **Debugging** | `inspect-word-xml` | Raw XML inspection for edge cases |
| **Visual** | `render-word-page`, `visual-check` | Page rendering and vision-based verification |
| **Other Docs** | `read-pdf`, `read-text` | PDF and plain text file reading |
| **Comparison** | `compare-docs` | Document diffing (reference vs target) |
| **Workflow** | `extract-spec`, `check-thesis`, `evaluate-spec` | Document formatting workflows |
| **OpenSpec** | `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, `openspec-explore` | Change lifecycle management |
| **Utility** | `peek-thinking` | Model debugging and thinking observation |

## Subagent Architecture

Workflow skills (`extract-spec`) now use a **Unified Extractor + Main Agent Validation** architecture:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  Main Agent (调度者 + 验证者)                           │
│                                                                         │
│  责任：                                                                  │
│  1. 调度 Unified Extractor Agent 执行提取                               │
│  2. 验证提取结果质量（可调用工具抽样检查）                               │
│  3. 分类处理问题（确定性错误/灰区问题/缺失上下文）                       │
│  4. 自迭代闭环（发现问题→重试→验证）                                    │
│  5. 合并输出到最终 spec.md                                              │
│                                                                         │
│  允许的验证行为：                                                        │
│  ✓ 读取 extraction_result.json                                          │
│  ✓ 调用 stats/query-style/query-text 抽样检查                          │
│  ✓ 执行确定性质量规则                                                   │
│  ✓ 标注问题                                                              │
│                                                                         │
│  禁止的执行行为：                                                        │
│  ✗ 解析原始文档                                                         │
│  ✗ 从零提取规则内容                                                     │
│  ✗ 自己推断缺失值                                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Agent tool 调用
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Unified Extractor Agent                             │
│                                                                         │
│  Prompt 模板文件：                                                       │
│  - unified-extractor-prompt.md (所有 section 提取，内部验证)            │
│  - quality-rules.md           (确定性质量规则定义)                      │
│                                                                         │
│  内部执行：                                                              │
│  - 三源验证（style + stats + text）                                     │
│  - 常识检查（西文字体≠中文字体）                                         │
│  - 输出 extraction_result.json                                          │
│                                                                         │
│  输出格式（标准化）：                                                    │
│  - status: "DONE" | "NEEDS_CONTEXT"                                    │
│  - output: 所有 section 提取数据                                        │
│  - cross_validation: 各 section 验证记录                                │
│  - tool_errors: 工具错误列表                                            │
│  - common_sense_check: "pass" | "needs_revision"                       │
└─────────────────────────────────────────────────────────────────────────┘
```

**关键设计：验证边界（IRON LAW 修订）**

| 方面 | 旧架构 | 新架构 |
|------|--------|--------|
| 任务执行 | 9个并行 subagent | 1个 Unified Extractor |
| Token消耗 | ~180k | ~40k |
| 验证者 | 无（主Agent形式检查） | 主Agent（可调用工具验证） |
| 自迭代 | 无（用户发现问题） | 有（最多2次重试） |
| 流程控制 | SKILL.md 调度协议 | SKILL.md 验证协议 |

**问题分类处理：**

| 问题类型 | 处理方式 |
|----------|----------|
| 确定性错误（cross_validation缺失） | 重试 Extractor（最多2次） |
| 灰区问题（西文字体为中文字体） | 标注"⚠️ 待确认"，不推断正确值 |
| 缺失上下文（无文字说明） | 询问用户，重新 dispatch |

## Standardized Subagent Output Format

所有 subagent 输出必须包含以下字段：

```json
{
  "status": "DONE" | "BLOCKED" | "NEEDS_CONTEXT",
  "output": {
    // 具体任务输出内容
    // font-extractor: { "font_rule": {...} }
    // evaluator: { "evaluation_result": "pass", "issues": [] }
    // rule-checker: { "check_results": [...], "coverage_status": {...} }
  },
  "cross_validation": {
    "sources": ["style_definition", "actual_paragraphs", "text_instructions"],
    "style_definition": { "east_asia": "...", "ascii": "..." },
    "actual_paragraphs": { "east_asia": {...}, "ascii": {...} },
    "text_instructions": { "found": true, "declaration": "..." },
    "conflicts": [],
    "resolution": "text_instructions override" | "style_definition confirmed" | "unresolved"
  },
  "tool_errors": [
    // 必须报告所有工具错误，不能跳过
    // {"tool": "query-word-text", "error": "无匹配段落", "keyword": "西文"}
  ],
  "common_sense_check": "pass" | "needs_revision" | "error"
}
```

**字段说明：**

| 字段 | 必需 | 说明 |
|------|------|------|
| `status` | ✅ | 任务执行状态：DONE（完成）、BLOCKED（阻塞）、NEEDS_CONTEXT（需要更多信息） |
| `output` | ✅ | 具体任务输出内容 |
| `cross_validation` | ✅ | 三源交叉验证记录（font/layout/heading subagent 必需） |
| `tool_errors` | ✅ | 工具错误列表，必须报告，不能为空就跳过 |
| `common_sense_check` | ✅ | 常识检查结果：pass、needs_revision 或 error |

**cross_validation 结构（针对提取类 subagent）：**

```json
{
  "sources": ["style_definition", "actual_paragraphs", "text_instructions"],
  "style_definition": { "east_asia": "宋体", "ascii": "宋体" },
  "actual_paragraphs": {
    "east_asia": { "value": "宋体", "count": 50 },
    "ascii": { "value": "宋体", "count": 50 }
  },
  "text_instructions": {
    "found": true,
    "declaration": "西文使用 Times New Roman"
  },
  "conflicts": [
    { "type": "style_vs_text", "style_ascii": "宋体", "text_ascii": "Times New Roman" }
  ],
  "resolution": "text_instructions override"
}
```

**tool_errors 结构：**

```json
[
  {
    "tool": "query-word-text",
    "error": "无匹配段落",
    "keyword": "西文",
    "action": "尝试其他关键词"
  }
]
```

**主 Agent 评估逻辑：**

```
if output.cross_validation.sources.length < 3:
    reject("缺少三源验证")

if output.tool_errors.length > 0:
    report("工具错误：{output.tool_errors}")

if output.common_sense_check == "needs_revision":
    reject("常识检查失败")
```

## Skill Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          META SKILLS (OpenSpec)                         │
│  openspec-propose → openspec-apply-change → openspec-archive-change    │
│                         openspec-explore (thinking mode)                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ drives
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW SKILLS                                 │
│                                                                         │
│   extract-spec ──────► evaluate-spec ──────► check-thesis              │
│   (upstream: rules)    (quality gate)       (downstream: compliance)    │
└                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ orchestrates
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAPABILITY SKILLS                                │
│                                                                         │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│   │  parse-word  │──│ query-word-* │──│ batch-check  │                 │
│   │  (parse)     │  │ (query)      │  │ (compare)    │                 │
│   └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                         │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│   │ paragraph-   │  │ validate-    │  │ inspect-     │                 │
│   │ stats        │  │ word         │  │ word-xml     │                 │
│   └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                         │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│   │ render-word- │  │ read-pdf     │  │ read-text    │                 │
│   │ page         │  │              │  │              │                 │
│   └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                         │
│   ┌──────────────┐                                                     │
│   │ compare-docs │  (standalone comparison)                            │
│   └──────────────┘                                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ visual supplement
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        VISUAL SKILLS                                    │
│                                                                         │
│   visual-check (orchestrates render-word-page + Agent vision)          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## User-invocable vs Internal

| Skill | Type | Trigger Pattern |
|-------|------|-----------------|
| `parse-word` | Capability | Agent needs document facts |
| `query-word-text` | Capability | Agent searches by keyword |
| `query-word-style` | Capability | Agent queries style properties |
| `paragraph-stats` | Capability | Agent analyzes paragraph distributions |
| `batch-check` | Capability | Agent runs property comparisons |
| `validate-word` | Capability | Agent validates XML structure |
| `inspect-word-xml` | Capability (debug) | Parser misses info, need raw XML |
| `render-word-page` | Capability | Agent needs visual verification |
| `visual-check` | Workflow | Vision-based rule verification |
| `read-pdf` | Capability | User provides PDF for rules/specs |
| `read-text` | Capability | Agent reads .txt/.md content |
| `compare-docs` | Capability | User wants document diff |
| `extract-spec` | Workflow | User provides templates → rules extraction |
| `check-thesis` | Workflow | User provides doc + rules → compliance check |
| `evaluate-spec` | Workflow (gate) | After extract-spec, before user review |
| `openspec-propose` | Meta | `/opsx:propose` or `/openspec-propose` |
| `openspec-apply-change` | Meta | `/opsx:apply` |
| `openspec-archive-change` | Meta | `/opsx:archive` |
| `openspec-explore` | Meta | `/opsx:explore` |
| `peek-thinking` | Utility | User wants to observe model thinking |

**Key distinction:**
- **Capability skills** are generic tools — invoked by Agent, rarely directly by users
- **Workflow skills** are user-facing entry points — triggered by user providing inputs
- **Meta skills** are invoked via slash commands (`/opsx:*`)

## Quick Reference

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `parse-word` | Parse .docx/.dotm → JSON facts | Agent needs structured document data |
| `query-word-text` | Search paragraphs by keyword | "find '摘要'", "locate '宋体'" |
| `query-word-style` | Get resolved style properties | "what font does Heading 1 use?" |
| `paragraph-stats` | Filter + analyze paragraphs | "show body text font distribution" |
| `batch-check` | Compare facts vs expected rules | "check font=宋体, size=12pt" |
| `validate-word` | Validate OOXML schema compliance | "is this docx structurally valid?" |
| `inspect-word-xml` | View raw XML for debugging | "python-docx missed something" |
| `render-word-page` | Render page as PNG | "visual verification needed" |
| `visual-check` | Vision-based rule checking | "check page number position" |
| `read-pdf` | Extract PDF text/tables | "rules are in a PDF" |
| `read-text` | Read .txt/.md/.docx text | "read the spec document" |
| `compare-docs` | Diff two Word documents | "what changed between these?" |
| `extract-spec` | Extract rules → spec.md | "here's the template, extract rules" |
| `check-thesis` | Check doc against rules | "check this thesis against format rules" |
| `evaluate-spec` | Evaluate spec.md quality | "is this spec complete?" |
| `openspec-propose` | Create change proposal | `/opsx:propose <name>` |
| `openspec-apply-change` | Implement change tasks | `/opsx:apply` |
| `openspec-archive-change` | Archive completed change | `/opsx:archive` |
| `openspec-explore` | Explore/thinking mode | `/opsx:explore` |
| `peek-thinking` | Observe model thinking | "watch how this model thinks" |

## Naming Convention

Skills use **hyphen-case** (lowercase with hyphens): `parse-word`, `batch-check`, `openspec-propose`.

**Pattern:**
- `<verb>-<noun>` for capabilities: `parse-word`, `query-word-text`, `read-pdf`
- `<noun>-<noun>` for comparisons: `batch-check`, `compare-docs`
- `<prefix>-<action>` for grouped skills: `openspec-propose`, `query-word-*`

**Minor inconsistency:** `batch-check` uses verb-noun, `compare-docs` uses noun-noun. Both are valid comparison patterns.

## When to Create New Skills

Consider creating a new skill when:
1. **New document type** — e.g., `.pptx`, `.xlsx` parsing
2. **New capability** — distinct tool not covered by existing skills
3. **New workflow** — composite orchestration of existing capabilities

Avoid creating new skills when:
- The capability can be added to an existing skill's tool
- It's just a configuration variant of an existing workflow

**New skill checklist:**
- Clear trigger pattern in SKILL.md frontmatter
- Single focused purpose (not multiple unrelated capabilities)
- Dependency on existing capability skills (if workflow)
- CLI command documented in SKILL.md