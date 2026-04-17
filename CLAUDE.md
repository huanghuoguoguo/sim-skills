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

### Unified CLI (sim-docs)

The recommended way to interact with document tools is via the unified `sim-docs` CLI:

```bash
# Parse Word document to structured facts
python3 -m sim_docs parse <file.docx> [--output facts.json]

# Query matching paragraphs by keyword
python3 -m sim_docs query-text <file.docx> --keyword "宋体"

# Query normalized style properties
python3 -m sim_docs query-style <file.docx> --style "Heading 1"

# Render a page for visual review
python3 -m sim_docs render <file.docx> --page 1 --output page1.png

# Batch check: view supported check types
python3 -m sim_docs check --schema

# Batch check: compare facts against check instructions
python3 -m sim_docs check <file.docx> <checks.json> [--output result.json]

# Paragraph stats: filter and compute distributions
python3 -m sim_docs stats <file.docx> [--style-hint normal] [--min-length 20] [--require-body-shape]

# Compare two Word documents
python3 -m sim_docs compare <reference.docx> <target.docx> [--output diff.json] [--report diff_report.md]

# Extract text/tables from PDF
python3 -m sim_docs read-pdf <file.pdf> [--pages 1-5] [--tables] [--all]

# Read text from .txt/.md/.docx files
python3 -m sim_docs read-text <file.txt>

# Validate Word document XML structure
python3 -m sim_docs validate <file.docx> [--auto-repair] [-v]

# Inspect raw XML of Word document
python3 -m sim_docs inspect <file.docx> [--output-dir unpacked/] [--show word/document.xml] [--list]

# Evaluate spec.md quality
python3 -m sim_docs spec-check --mode conflicts <spec.md>
python3 -m sim_docs spec-check --mode structure <spec.md>
python3 -m sim_docs spec-check --mode body-consistency --evidence <evidence.json> --checks <checks.json>
```

## Skill Layout

> **Navigation:** See `.claude/skills/SKILLS_OVERVIEW.md` for a complete skill hierarchy and quick reference.

```text
sim_docs/                       # Unified document service layer
├── __init__.py                 # Package exports
├── cli.py                      # CLI entry point (python3 -m sim_docs)
├── service.py                  # DocumentService facade
├── cache.py                    # LRU cache for parsed documents
├── docx_parser.py              # Low-level Word parser (CJK/ASCII font separation)
├── docx_parser_models.py       # Parser dataclasses (ParagraphFact, StyleFact)
├── check_engine.py             # Batch check logic
├── stats_engine.py             # Paragraph statistics logic
├── pdf_engine.py               # PDF extraction logic
├── inspect_engine.py           # XML inspection logic
├── compare_engine.py           # Document comparison logic
├── validate_engine.py          # XSD validation logic
├── spec_engine.py              # Spec evaluation logic
├── adapters/
│   └── word.py                 # Adapter to docx_parser
└── tests/
    ├── test_cache.py           # Cache tests
    ├── test_spec_engine.py     # Spec engine tests
    └── test_stats_engine.py    # Stats engine tests

.claude/skills/
├── batch-check/SKILL.md        # workflow: property comparison
├── paragraph-stats/SKILL.md    # workflow: paragraph statistics
├── parse-word/SKILL.md         # workflow: docx parsing
├── query-word-text/SKILL.md    # workflow: keyword search
├── query-word-style/SKILL.md   # workflow: style query
├── render-word-page/SKILL.md   # workflow: page rendering
├── read-text/SKILL.md          # workflow: text file reading
├── read-pdf/SKILL.md           # workflow: PDF extraction
├── validate-word/SKILL.md      # workflow: XML validation
├── inspect-word-xml/SKILL.md   # workflow: XML inspection
├── compare-docs/SKILL.md       # workflow: document comparison
├── evaluate-spec/SKILL.md      # workflow: spec quality evaluation
├── check-thesis/SKILL.md       # workflow: thesis checking
├── visual-check/SKILL.md       # workflow: visual verification
├── extract-spec/SKILL.md       # workflow: spec extraction
├── __libs__/                   # shared Python utilities
│   ├── utils.py                # resolve_path, write_json_output, setup_word_scripts_path
│   ├── spec_rules.py           # font-size resolution, heading parsing
│   ├── thesis_profiles.py      # profile loading for evaluate-spec
│   └── text_sources.py         # text source reader
└── validate-word/scripts/      # XSD schemas for validation
    ├── schemas/                # OOXML XSD schema files
    └── validators/             # validator modules
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

- `sim_docs/service.py` - DocumentService facade with caching
- `sim_docs/cli.py` - Unified CLI entry point (`python3 -m sim_docs`)
- `sim_docs/cache.py` - LRU cache for parsed documents
- `sim_docs/check_engine.py` - Batch property comparison engine
- `sim_docs/stats_engine.py` - Paragraph filtering and distribution statistics
- `sim_docs/pdf_engine.py` - PDF text/table extraction
- `sim_docs/inspect_engine.py` - XML unpacking and inspection
- `sim_docs/compare_engine.py` - Document comparison engine
- `sim_docs/validate_engine.py` - XSD schema validation
- `sim_docs/spec_engine.py` - Spec evaluation (conflicts, structure, body-consistency)
- `sim_docs/adapters/word.py` - Adapter to docx_parser
- `sim_docs/docx_parser.py` - low-level Word parser (Chinese/English font separation, header/footer extraction)
- `sim_docs/docx_parser_models.py` - parser dataclasses (ParagraphFact, StyleFact, HeaderFooterFact)
- `.claude/skills/__libs__/utils.py` - shared utilities (resolve_path, write_json_output, write_text_output, setup_word_scripts_path)
- `.claude/skills/__libs__/spec_rules.py` - shared spec parsing helpers (font-size resolution, heading parsing)
- `.claude/skills/__libs__/thesis_profiles.py` - thesis profile configuration (spec_schema, required sections, extractor mapping)

## Thesis Profile Schema

The `thesis_profiles.py` defines a **spec_schema** that specifies what a thesis spec must contain:

```python
DEFAULT_THESIS_PROFILE = {
    "spec_schema": {
        "sections": {
            "页面设置": {"required": True, "extractor": "layout"},
            "正文": {"required": True, "extractor": "font", "target_styles": ["Normal"]},
            "标题": {"required": True, "extractor": "heading", "levels": [1, 2, 3, 4]},
            "摘要": {"required": True, "extractor": "abstract"},
            "关键词": {"required": True, "extractor": "keyword"},
            "图表Caption": {"required": True, "extractor": "caption"},
            "参考文献": {"required": True, "extractor": "reference"},
            "页眉页脚": {"required": True, "extractor": "header_footer"},
            "目录": {"required": True, "extractor": "toc"},
            # Optional sections
            "封面": {"required": False, "extractor": "cover"},
            "附录": {"required": False, "extractor": "appendix"},
            "致谢": {"required": False, "extractor": "acknowledgment"},
        }
    }
}
```

Key functions in `thesis_profiles.py`:
- `load_profile(profile_json, overrides)` - Load default profile with school-specific overrides
- `get_required_sections(profile)` - Extract list of required section names
- `get_section_config(profile, section_name)` - Get extractor and properties for a section
- `get_section_rules_for_structure_check(profile)` - Build section_rules for spec_engine.check_structure()

## Engineering Boundaries

- Supports: `.docx`, `.dotm`
- Does not support: `.doc`, `.pdf` as the main checking target
- Page-level visual inspection is optional and depends on model/tool support
- Auto-fix is not implemented
