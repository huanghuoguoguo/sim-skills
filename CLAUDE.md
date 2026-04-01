# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Document formatting compliance checker for Chinese undergraduate theses. Extracts format rules from Word templates (.docx/.dotm) and checks thesis documents against those rules.

## Core Commands

```bash
# Install dependencies (optional - skills run standalone)
pip install -e .

# Parse Word document to structured JSON
python3 .claude/skills/word/scripts/parse.py <file.docx> [--output out.json]

# Extract format rules from template
python3 .claude/skills/extract-spec/scripts/run.py <template.docx> [--output spec.json]

# Check thesis against spec
python3 .claude/skills/check-thesis/scripts/run.py <thesis.docx> <spec.json>

# Compare two Word documents
python3 .claude/skills/compare-docs/scripts/run.py <reference.docx> <target.docx>
```

## Architecture

```
.claude/skills/
├── word/           # Base parser: docx -> DocumentIR (paragraphs, styles, layout)
├── extract-spec/   # Rule extraction: template styles -> Spec JSON
├── check-thesis/   # Format checker: thesis + spec -> issues + report
├── compare-docs/   # Document diff: ref + target -> diffs
└── read-text/      # Text file reader utility
```

**Dependency graph:**
```
extract-spec, check-thesis, compare-docs  →  word (parser)
```

All business-logic skills import `parse_word_document` and models from `word/scripts/`.

## Key Modules

- `word/scripts/docx_parser.py` - Core parser: extracts paragraphs, styles, layout properties
- `word/scripts/docx_parser_models.py` - Data models: `ParagraphFact`, `StyleFact`, `WordDocumentFacts`
- `extract-spec/scripts/run.py` - Rule extraction with AI review for common thesis requirements
- `check-thesis/scripts/run.py` - Rule checker with severity levels (critical/major/minor/info)

## Spec JSON Structure

```json
{
  "spec_id": "spec-xxx",
  "version": "0.1.0-draft",
  "rules": [
    {
      "id": "rule-body-paragraph",
      "selector": "body.paragraph",
      "properties": {"font_family_zh": "宋体", "font_size_pt": 10.5},
      "severity": "major"
    }
  ],
  "pending_confirmations": [...]
}
```

## Selectors

- `body.paragraph` - Body text (Normal/正文 style)
- `body.heading.level1/2/3` - Headings
- `abstract.body` - Abstract section
- `toc.entry` - Table of contents
- `figure.caption` - Figure/table captions
- `references.entry` - Bibliography

## Engineering Boundaries

- Supports: `.docx`, `.dotm` (auto-converted to `.docx` for parsing)
- Does not support: `.doc` (legacy binary), `.pdf`
- Page-level features (actual page numbers, cross-page elements) not supported
- Auto-fix not implemented
