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