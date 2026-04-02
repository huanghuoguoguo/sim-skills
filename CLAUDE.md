# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

This repository is a skill-based document formatting checker for Chinese thesis-style Word documents.

The system is organized as a fine-grained skill graph:

- primitive skills expose deterministic capabilities
- analysis skills help synthesize rule fragments
- gate skills validate structure and coverage
- workflow skills orchestrate the full task

The current target scenario is `.docx` / `.dotm` thesis formatting.

## Working Rules

- Prefer the fine-grained skills under `.claude/skills/` over older direct references to `word/scripts/*`
- Default output artifacts should be written in the current working directory unless the user explicitly asks for temporary files
- Use `validate-spec` before treating a generated `spec.json` as final
- Prefer outputting a `spec/` folder with `spec.json` and `spec.md`

## Core Commands

```bash
# Parse Word document to DocumentIR
python3 .claude/skills/parse-word/scripts/run.py <file.docx> [--output facts.json]

# Query matching paragraphs by keyword
python3 .claude/skills/query-word-text/scripts/run.py <file.docx> --keyword "宋体"

# Query normalized style properties
python3 .claude/skills/query-word-style/scripts/run.py <file.docx> --style "Heading 1"

# Render a page for visual review
python3 .claude/skills/render-word-page/scripts/run.py <file.docx> --page 1 --output page1.png

# Validate spec for downstream consumption
python3 .claude/skills/validate-spec/scripts/validate.py <spec.json> [--strict]

# Check thesis against spec
python3 .claude/skills/check-thesis/scripts/run.py <thesis.docx> <spec.json> [--output report.json]

# Validate report structure
python3 .claude/skills/validate-report/scripts/validate.py <report.json>

# Compare two Word documents
python3 .claude/skills/compare-docs/scripts/run.py <reference.docx> <target.docx> [--output diff.json]

# Agent-based check for skipped rules
python3 .claude/skills/agent-check-report/scripts/run.py <facts.json> <spec.json> <report.json> [--output agent_report.json]
```

## Skill Layout

```text
.claude/skills/
├── parse-word/                 # primitive: docx/dotm -> DocumentIR
├── query-word-text/            # primitive: keyword -> matching paragraphs
├── query-word-style/           # primitive: style query -> normalized style properties
├── render-word-page/           # primitive: page -> image
├── read-text/                  # primitive: text file/docx text reader
├── extract-spec/               # workflow: reference files -> spec.md
├── evaluate-spec/              # workflow: review spec.md coverage and executability
├── check-thesis/               # workflow: spec.md + thesis -> report
├── compare-docs/               # workflow/analysis: document diff
├── parse-word/                 # capability: parse docx/dotm to structured facts
├── query-word-text/            # capability: keyword text lookup
├── query-word-style/           # capability: style lookup with resolved properties
├── render-word-page/           # capability: render page image for visual review
└── word/                       # internal shared parser implementation
```

## Architecture

```text
user goal
  -> workflow skill
  -> primitive / analysis / gate skills
  -> artifacts
```

Typical artifact flow:

```text
Word file
  -> DocumentIR
  -> spec.json
  -> spec.md
  -> report.json / report.md
```

## Skill Usage Guidance

### For spec extraction

Preferred sequence:

1. `parse-word`
2. `query-word-text`
3. `query-word-style`
4. `render-word-page` only when visual conflict resolution is needed
5. write `spec.json`
6. write `spec.md`
7. `validate-spec`

Notes:

- Do not trust a generated spec until `validate-spec` passes
- Keep `spec.json` simple; move explanations and uncertainty into `spec.md`
- When structure and visual evidence conflict, prefer programmatic facts first, then text clues, then visual inspection

### For thesis checking

Preferred sequence:

1. `parse-word`
2. `evaluate-spec`
3. `check-thesis`

Notes:

- `check-thesis` consumes `spec.md`, emits JSON + Markdown report, and separates Python checks from Agent/manual follow-up
- Reports should be reviewed as artifacts in the working directory when the user wants manual verification

## Key Modules

- `.claude/skills/word/scripts/docx_parser.py` - low-level Word parser (Chinese/English font separation, header/footer extraction)
- `.claude/skills/word/scripts/docx_parser_models.py` - parser dataclasses (ParagraphFact, StyleFact, HeaderFooterFact)
- `.claude/skills/query-word-style/scripts/run.py` - normalized style query wrapper
- `.claude/skills/check-thesis/scripts/translate_spec.py` - `spec.md -> checks` translator
- `.claude/skills/check-thesis/scripts/batch_check.py` - deterministic batch checker
- `.claude/skills/check-thesis/scripts/run.py` - workflow wrapper that combines Python checks with Agent/manual follow-up

## Spec Expectations

The thesis-facing artifact is `spec.md`, not `spec.json`.

## Mixed Checking Mode

The system uses a mixed Python/Agent checking approach:

- **Python checker** (`check-thesis`): Fast, deterministic checks for supported selectors
  - `body.paragraph`, `body.heading.*`, `figure.caption`, `table.caption`
- **Agent checker** (`agent-check-report`): Semantic matching for complex selectors
  - `frontmatter.abstract.zh.*`, `frontmatter.keywords.en.*`
  - `frontmatter.toc.*`, `backmatter.references.*`
  - `frontmatter.title_page.*`

`check-thesis` outputs `skipped_rules` list which `agent-check-report` consumes.

## Engineering Boundaries

- Supports: `.docx`, `.dotm`
- Does not support: `.doc`, `.pdf` as the main checking target
- Page-level visual inspection is optional and depends on model/tool support
- Auto-fix is not implemented
