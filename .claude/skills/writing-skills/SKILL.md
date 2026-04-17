---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment
---

# Writing Skills

## Overview

**Writing skills IS Test-Driven Development applied to process documentation.**

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

## The Iron Law

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

This applies to NEW skills AND EDITS to existing skills.

Write skill before testing? Delete it. Start over.
Edit skill without testing? Same violation.

**No exceptions:**
- Not for "simple additions"
- Not for "just adding a section"
- Not for "documentation updates"
- Don't keep untested changes as "reference"
- Don't "adapt" while running tests
- Delete means delete

## Skill Directory Structure

```
.claude/skills/
├── SKILLS_OVERVIEW.md      # Navigation map (required)
├── skill-name/
│   ├── SKILL.md            # Main reference (required)
│   └── supporting-file.*   # Only if needed
└── __libs__/               # Shared utilities
    ├── utils.py
    ├── spec_rules.py
    └── ...
```

**Flat namespace** - all skills in one searchable namespace.

## SKILL.md Structure

**Frontmatter (YAML):**
- `name`: Use letters, numbers, and hyphens only
- `description`: Third-person, describes ONLY when to use (NOT what it does)
- Max 1024 characters total

```markdown
---
name: skill-name-with-hyphens
description: Use when [specific triggering conditions and symptoms]
---

# Skill Name

## Overview
Core principle in 1-2 sentences.

## When to Use
Bullet list with SYMPTOMS and use cases.
When NOT to use.

## The Iron Law (if applicable)
NO X WITHOUT Y

## Red Flags - STOP
Self-check triggers.

## Common Rationalizations
| Excuse | Reality |

## Quick Reference
Table for scanning common operations.

## Implementation
Inline code or command examples.

## Common Mistakes
What goes wrong + fixes.
```

## CSO (Claude Search Optimization)

### Description Rules

**CRITICAL: Description = When to Use, NOT What the Skill Does**

```yaml
# ❌ BAD: Summarizes workflow - Claude may follow this instead of reading skill
description: Use when extracting rules - parse template, query styles, write spec.md

# ✅ GOOD: Just triggering conditions, no workflow summary
description: Use when user provides templates or formatting guides and wants rules extracted
```

### Keyword Coverage

Use words Claude would search for:
- Error messages: "Hook timed out", "unresolved"
- Symptoms: "missing", "inconsistent", "font mismatch"
- Tools: `python3 -m sim_docs`, CLI commands
- Chinese terms: "宋体", "黑体", "摘要", "目录"

### Token Efficiency

**Target word counts:**
- Frequently-loaded skills: <200 words total
- Other skills: <500 words

**Techniques:**
- Move details to `--help` or separate files
- Use cross-references instead of repeating
- Compress examples

## Red Flags Pattern

Every discipline-enforcing skill should have:

```markdown
## Red Flags - STOP

If you catch yourself thinking:
- "The template shows X so it must be X"
- "This command failed, I'll skip it"
- "Quick check is enough"
- ...

**ALL of these mean: STOP. Re-verify.**
```

## Rationalization Table Pattern

Capture excuses from testing:

```markdown
## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Template paragraph shows 宋体/宋体" | 中文论文西文通常是 Times New Roman，检查文字说明 |
| "Style definition says 宋体" | 样式定义常不准确，必须用 paragraph-stats 交叉验证 |
| "Command failed, skip it" | 失败必须报告给用户，不能静默忽略 |
| "I didn't see the text instructions" | 必须用 query-text 搜索关键词 |
```

## Gate Function Pattern

Use pseudo-code to force step-by-step execution:

```markdown
## The Gate Function

BEFORE writing any rule to spec.md:
1. CHECK: Is this a font claim?
2. IF YES: Is east_asia font used as ascii font?
   - IF 宋体/黑体/楷体 as ascii → FLAG as "常识冲突"
3. VERIFY: Does template's text instructions say otherwise?
4. ONLY THEN: Write the rule with confidence level
```

## Skill Chain Pattern

```markdown
**REQUIRED:** Use extract-spec for rule extraction
**REQUIRED:** Use evaluate-spec for quality check after extraction
**REQUIRED:** Use paragraph-stats for body text verification
```

## Common Sense Checks (Project-Specific)

These are domain-specific red flags that apply to our document checking skills:

### Font Common Sense

```markdown
## Font Common Sense - MUST VERIFY

中文字体不应作为西文字体：
- 宋体、黑体、楷体、仿宋 = 中文专用
- 西文字体通常是：Times New Roman、Arial、Calibri

**如果看到"宋体/宋体"（east_asia/ascii 都是宋体）：**
1. 先检查模板内嵌的文字说明（query-text 搜索"字体"、"Times"、"西文"）
2. 文字说明优先级 > 样式定义 > 实际段落属性
3. 如果文字说明说"西文 Times New Roman" → 标注为"样式与说明不一致"
```

### Style vs Actual Consistency

```markdown
## Style Definition ≠ Actual Usage

中文论文模板常见问题：
- Normal 样式定义可能不准确
- 直接格式覆盖样式定义是常见做法

**必须交叉验证：**
1. query-style 获取样式定义
2. paragraph-stats 获取实际段落属性分布
3. 如果不一致，优先采用实际段落值
4. 在 spec.md 中标注冲突来源
```

### Tool Error Handling

```markdown
## Tool Errors - MUST REPORT

任何 sim_docs 命令失败都必须：
1. 记录错误消息
2. 分析失败原因
3. 告知用户"工具调用失败，可能影响提取"
4. 不能静默跳过或忽略

**常见错误：**
- `ModuleNotFoundError: fitz` → PyMuPDF 未安装，render 功能不可用
- `ValueError: Unsupported file type` → 文件格式不支持
```

## Testing Skills

### RED Phase - Baseline

Run pressure scenario WITHOUT the skill:
1. Create realistic test case (e.g., a thesis template)
2. Run extraction WITHOUT skill guidance
3. Document exact failures and rationalizations (verbatim)

### GREEN Phase - Write Skill

Write skill addressing those specific failures:
- Add red flags for each rationalization
- Add gate function for each skip point
- Re-test with skill present

### REFACTOR Phase - Close Loopholes

Agent found new excuse? Add to rationalization table. Re-test.

## Skill Creation Checklist

**RED Phase:**
- [ ] Create test scenario with real file
- [ ] Run WITHOUT skill - document failures verbatim
- [ ] Identify patterns in rationalizations

**GREEN Phase:**
- [ ] Name uses only letters, numbers, hyphens
- [ ] Description = triggering conditions only (no workflow)
- [ ] Clear overview with core principle
- [ ] Address specific baseline failures
- [ ] Red flags section
- [ ] Rationalization table
- [ ] Quick reference table

**REFACTOR Phase:**
- [ ] Identify new rationalizations from testing
- [ ] Add explicit counters
- [ ] Re-test until bulletproof

**Deployment:**
- [ ] Update SKILLS_OVERVIEW.md with new skill
- [ ] Commit and push

## Cross-Referencing Skills

Use skill name only, with explicit requirement markers:

```markdown
# ✅ Good
**REQUIRED:** Use paragraph-stats for body text verification
**REQUIRED:** Use evaluate-spec after extraction

# ❌ Bad
See skills/paragraph-stats/SKILL.md (unclear if required)
@paragraph-stats/SKILL.md (force-loads, burns context)
```

## Flowchart Usage

Use flowcharts ONLY for:
- Non-obvious decision points
- Process loops where agent might stop too early

**Never for:**
- Reference material → Tables
- Code examples → Markdown blocks
- Linear instructions → Numbered lists

## The Bottom Line

**Creating skills IS TDD for process documentation.**

Same Iron Law: No skill without failing test first.
Same cycle: RED → GREEN → REFACTOR.
Same benefits: Better quality, fewer surprises, bulletproof results.