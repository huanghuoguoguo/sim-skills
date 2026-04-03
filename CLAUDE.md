# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

This repository is a skill-based document formatting checker.

The system follows an **Agent + generic tools** architecture:

- **Tool scripts (Python)** provide fine-grained, generic capabilities: parsing, querying, batch comparison, statistics
- **Agent** reads rules from any source, orchestrates tools, handles semantic reasoning, and produces final output
- **SKILL.md** guides the Agent's planning and quality standards

Tools are generic and document-type-agnostic. The Agent decides what to check, the tools execute.

## Working Rules

- Agent reads the relevant SKILL.md, then autonomously plans and calls tool scripts
- Default output artifacts should be written in the current working directory unless the user explicitly asks for temporary files
- Shared utilities live in `.claude/skills/__libs__/utils.py`
- `evaluate-spec` may call small diagnostic scripts; these are internal gates, not user-facing upstream artifacts

## Core Commands

```bash
# Parse Word document to structured facts
python3 .claude/skills/parse-word/scripts/run.py <file.docx> [--output facts.json]

# Query matching paragraphs by keyword
python3 .claude/skills/query-word-text/scripts/run.py <file.docx> --keyword "宋体"

# Query normalized style properties
python3 .claude/skills/query-word-style/scripts/run.py <file.docx> --style "Heading 1"

# Render a page for visual review
python3 .claude/skills/render-word-page/scripts/run.py <file.docx> --page 1 --output page1.png

# Batch check: view supported check types
python3 .claude/skills/batch-check/scripts/run.py --schema

# Batch check: compare facts against check instructions
python3 .claude/skills/batch-check/scripts/run.py <facts.json|file.docx> <checks.json> [--output result.json]

# Paragraph stats: filter and compute distributions
python3 .claude/skills/paragraph-stats/scripts/run.py <facts.json|file.docx> [--style-hint normal] [--min-length 20] [--require-body-shape]

# Diagnose obvious spec conflicts / missing sections
python3 .claude/skills/evaluate-spec/scripts/check_conflicts.py <spec.md>
python3 .claude/skills/evaluate-spec/scripts/check_structure.py <spec.md>

# Compare body rules against paragraph evidence
python3 .claude/skills/evaluate-spec/scripts/check_body_consistency.py --evidence <evidence.json> --checks <checks.json>

# Compare two Word documents
python3 .claude/skills/compare-docs/scripts/run.py <reference.docx> <target.docx> [--output diff.json] [--report diff_report.md]

# Extract text/tables from PDF
python3 .claude/skills/read-pdf/scripts/run.py <file.pdf> [--pages 1-5] [--tables] [--all] [--output result.json]

# Validate Word document XML structure
python3 .claude/skills/validate-word/scripts/run.py <file.docx> [--auto-repair] [-v]

# Inspect raw XML of Word document
python3 .claude/skills/inspect-word-xml/scripts/run.py <file.docx> [--output-dir unpacked/] [--show word/document.xml] [--list]
```

## Skill Layout

```text
.claude/skills/
├── batch-check/                # tool: deterministic property comparison engine
│   └── scripts/run.py          #   --schema for self-describing capabilities
├── paragraph-stats/            # tool: paragraph filtering + distribution stats
│   └── scripts/run.py
├── parse-word/                 # tool: docx/dotm -> structured facts (DocumentIR)
├── query-word-text/            # tool: keyword -> matching paragraphs
├── query-word-style/           # tool: style query -> normalized properties
├── render-word-page/           # tool: page -> image
├── read-text/                  # tool: text file/docx text reader
├── read-pdf/                   # tool: PDF text/table extraction
├── validate-word/              # tool: XSD schema validation + auto-repair
├── inspect-word-xml/           # tool: unpack docx to raw XML for debugging
├── check-thesis/               # workflow guidance: rules + document -> check report
├── visual-check/               # workflow guidance: vision-based visual verification
├── extract-spec/               # workflow guidance: reference files -> spec.md
├── evaluate-spec/              # quality gate on spec.md
│   └── scripts/
│       ├── check_conflicts.py  # obvious contradictions in rules
│       ├── check_body_consistency.py # compare body rules with paragraph evidence
│       └── check_structure.py  # missing common sections
├── compare-docs/               # workflow: document diff
├── __libs__/                   # shared Python utilities
│   ├── utils.py                # resolve_path, write_json_output, setup_word_scripts_path
│   ├── spec_rules.py           # font-size resolution, heading parsing
│   ├── thesis_profiles.py      # profile loading for evaluate-spec
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
  -> calls generic tool scripts for facts and batch comparison
  -> Agent reasons over results, handles semantic rules
  -> outputs artifacts (spec.md / report)
```

Two independent tasks (can be used separately):

```text
Upstream: reference files -> Agent + tools -> spec.md -> user review
Downstream: rules (any format) + document -> Agent + tools -> check report
```

## Checking Approach

The system uses a mixed Python/Agent approach:

- **Python** (`batch-check`): Agent constructs check instructions, Python executes deterministic comparison across all paragraphs (font, font size, line spacing, margins, indentation, alignment, captions)
- **Agent**: Semantic rules requiring context understanding (abstract format, references, TOC structure)
- **Agent constructs check instructions directly** — no intermediate spec translation step. Run `batch-check --schema` to see supported check types.

## Key Modules

- `.claude/skills/batch-check/scripts/run.py` - generic property comparison engine with self-describing schema
- `.claude/skills/paragraph-stats/scripts/run.py` - paragraph filtering and distribution statistics
- `.claude/skills/word/scripts/docx_parser.py` - low-level Word parser (Chinese/English font separation, header/footer extraction)
- `.claude/skills/word/scripts/docx_parser_models.py` - parser dataclasses (ParagraphFact, StyleFact, HeaderFooterFact)
- `.claude/skills/__libs__/utils.py` - shared utilities (resolve_path, write_json_output, write_text_output, setup_word_scripts_path)
- `.claude/skills/__libs__/spec_rules.py` - shared spec parsing helpers (font-size resolution, heading parsing)

## Engineering Boundaries

- Supports: `.docx`, `.dotm`
- Does not support: `.doc`, `.pdf` as the main checking target
- Page-level visual inspection is optional and depends on model/tool support
- Auto-fix is not implemented
