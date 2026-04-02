# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

This repository is a skill-based document formatting checker for Chinese thesis-style Word documents.

The system follows an **Agent + tool scripts** architecture:

- **Skill (SKILL.md)** guides the Agent's planning and quality standards
- **Tool scripts (Python)** handle deterministic work: parsing, querying, batch checking
- **Agent** orchestrates tools, handles semantic reasoning, and produces final output

The current target scenario is `.docx` / `.dotm` thesis formatting.

## Working Rules

- Agent reads the relevant SKILL.md, then autonomously plans and calls tool scripts
- Default output artifacts should be written in the current working directory unless the user explicitly asks for temporary files
- The upstream artifact is `spec.md` (natural language rules), not `spec.json`
- Shared utilities live in `.claude/skills/__libs__/utils.py`
- `evaluate-spec` may call small diagnostic scripts; these are internal gates, not user-facing upstream artifacts

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

# Check thesis against spec.md
python3 .claude/skills/check-thesis/scripts/run.py <thesis.docx> <spec.md> [--output report.json]

# Translate spec.md to check instructions (standalone)
python3 .claude/skills/check-thesis/scripts/translate_spec.py <spec.md> [--output checks.json]

# Diagnose obvious spec conflicts / missing sections
python3 .claude/skills/evaluate-spec/scripts/check_conflicts.py <spec.md>
python3 .claude/skills/evaluate-spec/scripts/check_structure.py <spec.md>

# Compare two Word documents
python3 .claude/skills/compare-docs/scripts/run.py <reference.docx> <target.docx> [--output diff.json]
```

## Skill Layout

```text
.claude/skills/
├── extract-spec/               # workflow: reference files -> spec.md
├── check-thesis/               # workflow: spec.md + thesis -> report
│   └── scripts/
│       ├── run.py              # workflow wrapper
│       ├── translate_spec.py   # spec.md -> structured checks
│       ├── batch_check.py      # deterministic batch checker
│       └── summarize_results.py # grouped diagnostics for user/Agent consumption
├── evaluate-spec/              # quality gate on top of spec.md
│   └── scripts/
│       ├── check_conflicts.py  # obvious contradictions in natural-language rules
│       └── check_structure.py  # missing common thesis sections
├── compare-docs/               # workflow: document diff
├── parse-word/                 # tool: docx/dotm -> DocumentIR
├── query-word-text/            # tool: keyword -> matching paragraphs
├── query-word-style/           # tool: style query -> normalized properties
├── render-word-page/           # tool: page -> image
├── read-text/                  # tool: text file/docx text reader
├── __libs__/                   # shared Python utilities
│   ├── utils.py                # resolve_path, write_json_output, setup_word_scripts_path
│   ├── spec_rules.py           # shared spec parsing helpers
│   └── text_sources.py         # text source reader
└── word/                       # internal shared parser implementation
    └── scripts/
        ├── docx_parser.py      # low-level Word parser
        └── docx_parser_models.py
```

## Architecture

```text
user request
  -> Agent reads SKILL.md
  -> Agent plans autonomously
  -> calls tool scripts (Python) for facts and checks
  -> Agent reasons over results
  -> outputs artifacts (spec.md / report)
```

Two workflows:

```text
Upstream: reference files -> Agent + tools -> spec.md -> user review
Downstream: thesis + spec.md -> Agent + tools -> check report
```

## Skill Usage Guidance

### For spec extraction

Agent reads `extract-spec/SKILL.md` and autonomously:

1. Identifies file types (template / exemplar / description)
2. Calls `parse-word`, `query-word-text`, `query-word-style` to extract facts
3. Calls `render-word-page` only when visual conflict resolution is needed
4. Synthesizes rules into `spec.md`
5. Uses `evaluate-spec` to self-assess completeness

Notes:

- `spec.md` is the sole upstream artifact — no `spec.json`
- When structure and visual evidence conflict, prefer programmatic facts first, then text clues, then visual inspection

### For thesis checking

Agent reads `check-thesis/SKILL.md` and autonomously:

1. Reads `spec.md` rules
2. Calls `parse-word` to get document facts
3. Uses `translate_spec.py` + `batch_check.py` for deterministic rules (Python)
4. Handles semantic rules (abstract, references, TOC) via Agent reasoning
5. Outputs Markdown report with source annotations

## Key Modules

- `.claude/skills/word/scripts/docx_parser.py` - low-level Word parser (Chinese/English font separation, header/footer extraction)
- `.claude/skills/word/scripts/docx_parser_models.py` - parser dataclasses (ParagraphFact, StyleFact, HeaderFooterFact)
- `.claude/skills/__libs__/utils.py` - shared utilities (resolve_path, write_json_output, write_text_output, setup_word_scripts_path)
- `.claude/skills/__libs__/spec_rules.py` - shared spec parsing helpers (font-size resolution, heading parsing)
- `.claude/skills/check-thesis/scripts/translate_spec.py` - `spec.md -> checks` translator
- `.claude/skills/check-thesis/scripts/batch_check.py` - deterministic batch checker
- `.claude/skills/check-thesis/scripts/summarize_results.py` - compact grouped failures for report / Agent payload
- `.claude/skills/check-thesis/scripts/run.py` - workflow wrapper combining Python + Agent results and writing artifacts

## Mixed Checking Mode

The system uses a mixed Python/Agent approach for thesis checking:

- **Python** (`translate_spec.py` + `batch_check.py`): Deterministic checks for font, font size, line spacing, margins, indentation, alignment, heading styles, captions
- **Agent**: Semantic rules requiring context understanding (abstract format, references, TOC structure)
- **Manual**: Rules that `translate_spec.py` cannot parse are flagged for human review

`translate_spec.py` categorizes each spec.md rule into one of three buckets: `checks` (Python), `semantic_rules` (Agent), or `manual_rules` (human).

## Engineering Boundaries

- Supports: `.docx`, `.dotm`
- Does not support: `.doc`, `.pdf` as the main checking target
- Page-level visual inspection is optional and depends on model/tool support
- Auto-fix is not implemented
