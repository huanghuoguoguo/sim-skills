# Skills Overview

This document provides a navigation map for workflow skills in `.claude/skills/`.

## Philosophy

**Skills are for workflow orchestration, not CLI documentation.**

- **CLI tools** → documented in [CLI_REFERENCE.md](../CLI_REFERENCE.md)
- **Workflow skills** → orchestrate multi-step processes requiring judgment

Skills follow the **Agent + generic tools** architecture:
- Agent reads rules, plans steps, handles semantic reasoning
- CLI tools execute deterministic operations
- SKILL.md guides the Agent's workflow and quality standards

## Skills (5)

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `check-thesis` | Check thesis against format rules | User provides doc + rules |
| `extract-spec` | Extract rules from templates → spec.md | User provides template files |
| `evaluate-spec` | Evaluate spec.md quality | After extract-spec, before review |
| `visual-check` | Vision-based rule verification | Agent needs visual check |
| `openspec` | Change lifecycle management | `/openspec propose/apply/archive` |

## Skill Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                      META SKILL                             │
│                      openspec                               │
│           (propose → apply → archive, explore)              │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ drives
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   WORKFLOW SKILLS                           │
│                                                             │
│   extract-spec ───► evaluate-spec ───► check-thesis        │
│   (upstream)       (quality gate)      (downstream)         │
│                                                             │
│                         visual-check                        │
│                         (supplement)                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ orchestrates
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLI TOOLS                                │
│             (see CLI_REFERENCE.md)                          │
│                                                             │
│   parse, query-text, query-style, stats, check,             │
│   render, compare, read-pdf, read-text, validate, inspect   │
└─────────────────────────────────────────────────────────────┘
```

## Workflow Descriptions

### extract-spec

**Input**: Reference materials (templates, instruction documents)

**Output**: `spec.md` (formatting rules)

**Process**:
1. Parse reference documents via CLI tools
2. Extract formatting requirements (font, size, spacing, margins)
3. Produce structured spec.md for user review

### evaluate-spec

**Input**: `spec.md`

**Output**: Quality report (conflicts, missing sections, consistency)

**Process**:
1. Check for contradictory rules
2. Verify required sections present
3. Cross-validate against document evidence

### check-thesis

**Input**: Thesis document + format rules (spec.md or raw rules)

**Output**: Compliance report

**Process**:
1. Parse thesis document
2. Run batch-check for deterministic rules (Python)
3. Handle semantic rules (Agent judgment)
4. Produce Markdown report

### visual-check

**Input**: Document + rules requiring visual verification

**Output**: Visual check results

**Process**:
1. Render key pages as PNG
2. Agent visually checks (page numbers, headers, TOC, cover)
3. Report pass/fail with confidence level

### openspec

**Input**: Change name or description

**Output**: Change artifacts (proposal, design, tasks)

**Process**:
- `propose`: Create change with all artifacts
- `apply`: Implement tasks
- `archive`: Finalize change

## When to Use Each Skill

| User Request | Skill | CLI Alternative |
|--------------|-------|-----------------|
| "Extract rules from this template" | `extract-spec` | Manual: parse + query-text + stats |
| "Check if this spec is complete" | `evaluate-spec` | Manual: spec-check --mode conflicts |
| "Check this thesis against format rules" | `check-thesis` | Manual: parse + stats + check + reasoning |
| "Verify page number position visually" | `visual-check` | Manual: render + human inspection |
| "Create a change for X" | `/openspec propose` | Manual: openspec CLI |

## Key Principle

**Skills minimize context, not maximize it.**

- Only 5 skills, each for genuine workflow orchestration
- CLI documentation in CLI_REFERENCE.md, not scattered across skill files
- Agent reads skill only when needed, reads CLI_REFERENCE.md for tool usage