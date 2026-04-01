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
- Use gate skills before treating a generated `spec.json` or `report.json` as final

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

# Validate spec structure
python3 .claude/skills/validate-spec-structure/scripts/validate.py <spec.json>

# Validate spec coverage
python3 .claude/skills/validate-spec-coverage/scripts/validate.py <spec.json> --profile thesis-basic

# Compatibility entry for spec validation
python3 .claude/skills/validate-spec/scripts/validate.py <spec.json>

# Check thesis against spec
python3 .claude/skills/check-thesis/scripts/run.py <thesis.docx> <spec.json> [--output report.json]

# Validate report structure
python3 .claude/skills/validate-report/scripts/validate.py <report.json>

# Compare two Word documents
python3 .claude/skills/compare-docs/scripts/run.py <reference.docx> <target.docx> [--output diff.json]
```

## Skill Layout

```text
.claude/skills/
├── parse-word/                 # primitive: docx/dotm -> DocumentIR
├── query-word-text/            # primitive: keyword -> matching paragraphs
├── query-word-style/           # primitive: style query -> normalized style properties
├── render-word-page/           # primitive: page -> image
├── read-text/                  # primitive: text file/docx text reader
├── infer-spec-fragment/        # analysis: selector-level rule fragment guidance
├── merge-spec-fragments/       # analysis: merge fragments into spec draft
├── validate-spec-structure/    # gate: schema and field shape checks
├── validate-spec-coverage/     # gate: selector/layout coverage checks
├── validate-report/            # gate: report structure checks
├── extract-spec/               # workflow: orchestrates spec extraction
├── check-thesis/               # workflow: orchestrates thesis checking
├── compare-docs/               # workflow/analysis: document diff
├── validate-spec/              # compatibility entrypoint
└── word/                       # compatibility container for legacy low-level scripts
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
  -> spec fragment(s)
  -> spec.json
  -> report.json / report.md
```

## Skill Usage Guidance

### For spec extraction

Preferred sequence:

1. `parse-word`
2. `query-word-text`
3. `query-word-style`
4. `render-word-page` only when visual conflict resolution is needed
5. `infer-spec-fragment`
6. `merge-spec-fragments`
7. `validate-spec-structure`
8. `validate-spec-coverage`

Notes:

- Do not trust a generated spec until both gate checks pass
- When structure and visual evidence conflict, prefer programmatic facts first, then text clues, then visual inspection
- Keep uncertain fields explicit in the output instead of silently guessing

### For thesis checking

Preferred sequence:

1. `parse-word`
2. `check-thesis`
3. `validate-report`

Notes:

- `check-thesis` can emit `report.json` plus a Markdown report
- Reports should be reviewed as artifacts in the working directory when the user wants manual verification

## Key Modules

- `.claude/skills/word/scripts/docx_parser.py` - low-level Word parser
- `.claude/skills/word/scripts/docx_parser_models.py` - parser dataclasses
- `.claude/skills/query-word-style/scripts/run.py` - normalized style query wrapper
- `.claude/skills/__libs__/spec_validation.py` - shared gate validation logic
- `.claude/skills/check-thesis/scripts/run.py` - rule checking implementation

## Spec Expectations

At minimum, a thesis-facing spec should usually contain:

- `spec_id`
- `name`
- `version`
- `rules`
- `layout.page_margins` or equivalent page margin coverage

For the `thesis-basic` coverage profile, the expected selectors are:

- `body.paragraph`
- `body.heading.level1`
- `body.heading.level2`
- `body.heading.level3`

## Engineering Boundaries

- Supports: `.docx`, `.dotm`
- Does not support: `.doc`, `.pdf` as the main checking target
- Page-level visual inspection is optional and depends on model/tool support
- Auto-fix is not implemented
