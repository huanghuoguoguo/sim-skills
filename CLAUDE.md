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

## CLI Reference

> **Full CLI documentation**: See [CLI_REFERENCE.md](CLI_REFERENCE.md) for complete command reference, parameters, output formats, and examples.

Quick reference:

```bash
# Parse Word document to structured facts
python3 -m sim_docs parse <file.docx> [--output facts.json]

# Query matching paragraphs by keyword
python3 -m sim_docs query-text <file.docx> --keyword "宋体"

# Query normalized style properties
python3 -m sim_docs query-style <file.docx> --style "Heading 1"

# Paragraph stats: filter and compute distributions
python3 -m sim_docs stats <file.docx> [--style-hint normal] [--min-length 20]

# Batch check: compare facts against check instructions
python3 -m sim_docs check <file.docx> <checks.json> [--output result.json]

# Render a page for visual review
python3 -m sim_docs render <file.docx> --page 1 --output page1.png

# Compare two Word documents
python3 -m sim_docs compare <reference.docx> <target.docx> [--report diff.md]

# Validate Word document XML structure
python3 -m sim_docs validate <file.docx> [--auto-repair]

# Extract text/tables from PDF
python3 -m sim_docs read-pdf <file.pdf> [--pages 1-5] [--tables]
```

Run `python3 -m sim_docs --help` for all commands.

## Skill Layout

> **Navigation**: 5 workflow skills. CLI tools documented in [CLI_REFERENCE.md](CLI_REFERENCE.md).

```text
.claude/skills/                      # 5 workflow skills (orchestration + judgment)
├── check-thesis/SKILL.md           # workflow: thesis format checking
├── extract-spec/SKILL.md           # workflow: spec extraction from templates
├── evaluate-spec/SKILL.md          # workflow: spec quality evaluation
├── visual-check/SKILL.md           # workflow: vision-based verification
├── openspec/SKILL.md               # meta: change lifecycle (propose/apply/archive)
├── __libs__/                       # shared Python utilities
│   ├── utils.py                    # resolve_path, write_json_output
│   ├── spec_rules.py               # font-size resolution, heading parsing
│   ├── thesis_profiles.py          # profile loading for evaluate-spec
│   └── text_sources.py             # text source reader
└── validate-word/scripts/          # XSD schemas for validation
    └── schemas/                    # OOXML XSD schema files

.claude/commands/opsx/               # OpenSpec slash commands
├── propose.md                       # /opsx:propose
├── apply.md                         # /opsx:apply
├── archive.md                       # /opsx:archive
├── explore.md                       # /opsx:explore
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

- `sim_docs/api.py` - Namespace facade (api.word, api.analysis, api.pdf, api.text, api.spec)
- `sim_docs/service.py` - Deprecated DocumentService wrapper (use api instead)
- `sim_docs/cli/main.py` - CLI entry point with explicit COMMANDS registry (`python3 -m sim_docs`)
- `sim_docs/core/cache.py` - LRU cache for parsed documents
- `sim_docs/core/helpers.py` - normalized(), values_close()
- `sim_docs/analysis/checks.py` - Batch property comparison engine
- `sim_docs/analysis/stats.py` - Paragraph filtering and distribution statistics
- `sim_docs/pdf/extract.py` - PDF text/table extraction
- `sim_docs/word/inspect.py` - XML unpacking and inspection
- `sim_docs/word/compare.py` - Document comparison engine
- `sim_docs/word/validate/` - XSD schema validation (vendored schemas)
- `sim_docs/spec/engine.py` - Spec evaluation (conflicts, structure, body-consistency)
- `sim_docs/spec/profiles.py` - Thesis profile configuration (spec_schema, required sections)
- `sim_docs/word/parser.py` - Low-level Word parser (CJK/ASCII font separation, header/footer)
- `sim_docs/word/models.py` - Parser dataclasses (ParagraphFact, StyleFact, HeaderFooterFact)

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
