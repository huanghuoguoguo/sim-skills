# sim_docs - Unified Document Service

A unified service layer for document parsing, querying, checking, and rendering with built-in caching support.

## Installation

The package is part of the sim-skills project. No separate installation required.

## CLI Usage

```bash
# Parse Word document to structured facts
python3 -m sim_docs parse thesis.docx --output facts.json

# Query style properties
python3 -m sim_docs query-style thesis.docx --style "Heading 1"

# Query paragraphs by keyword
python3 -m sim_docs query-text thesis.docx --keyword "宋体"

# Batch check document properties
python3 -m sim_docs check thesis.docx checks.json --output result.json

# Get paragraph statistics
python3 -m sim_docs stats thesis.docx --min-length 20 --require-body-shape

# Render a page to image
python3 -m sim_docs render thesis.docx --page 1 --output page1.png

# Validate document XML structure
python3 -m sim_docs validate thesis.docx --auto-repair

# Inspect raw XML
python3 -m sim_docs inspect thesis.docx --show word/document.xml --list

# Compare two documents
python3 -m sim_docs compare reference.docx target.docx --report diff_report.md

# Read text from files
python3 -m sim_docs read-text file.txt
python3 -m sim_docs read-pdf file.pdf --pages 1-5 --all

# Evaluate spec.md quality
python3 -m sim_docs spec-check --mode conflicts spec.md
python3 -m sim_docs spec-check --mode structure spec.md
python3 -m sim_docs spec-check --mode body-consistency --evidence evidence.json --checks checks.json
```

## Python API Usage

```python
from sim_docs import DocumentService

# Create service instance
service = DocumentService()

# Parse document (cached)
facts = service.parse("thesis.docx")

# Query styles
styles = service.query_style("thesis.docx", "Heading 1")

# Query text
paragraphs = service.query_text("thesis.docx", "宋体")

# Batch check
result = service.batch_check("thesis.docx", [
    {"type": "font", "selector": "style:Normal", "expected": "宋体"},
    {"type": "font_size", "selector": "style:Heading 1", "expected": 16},
])

# Get statistics
stats = service.stats("thesis.docx", min_length=20, require_body_shape=True)

# Render page
output_path = service.render("thesis.docx", page=1, output="page1.png")

# Validate document
validation = service.validate("thesis.docx", auto_repair=True)

# Compare documents
diff = service.compare_docs("reference.docx", "target.docx")

# Evaluate spec.md
conflicts = service.spec_check_conflicts("spec.md")
structure = service.spec_check_structure("spec.md")
body = service.spec_check_body_consistency(evidence, checks)

# Cache management
stats = service.cache_stats()  # {"hits": 5, "misses": 2, "size": 3, "max_size": 32}
service.clear_cache()  # Clear all cached entries
```

## Caching

The DocumentService uses an in-memory LRU cache to avoid redundant parsing:

- **Cache size**: Default 32 documents, configurable via `DocumentService(cache_size=N)`
- **Invalidation**: Automatic when source file is modified
- **Statistics**: Access via `service.cache_stats()`
- **Clear**: Call `service.clear_cache()` to reset

## Supported Formats

- `.docx` - Word documents
- `.dotm` - Word templates
- `.docm` - Macro-enabled Word documents
- `.txt`, `.md` - Text files (read-text)
- `.pdf` - PDF files (read-pdf)

## Architecture

```
sim_docs/
├── __init__.py          # Package exports
├── cli.py               # CLI entry point
├── service.py           # DocumentService facade
├── cache.py             # LRU cache implementation
├── docx_parser.py       # Core Word parser
├── docx_parser_models.py # Parser dataclasses
├── check_engine.py      # Batch check logic
├── stats_engine.py      # Paragraph statistics logic
├── pdf_engine.py        # PDF extraction logic
├── inspect_engine.py    # XML inspection logic
├── compare_engine.py    # Document comparison logic
├── validate_engine.py   # XSD validation logic
├── spec_engine.py       # Spec evaluation logic
└── adapters/
    └── word.py          # Adapter interface
```

The service layer provides:

1. **Unified interface** - Single entry point for all document operations
2. **Caching** - Avoid redundant parsing within a session
3. **Clean API** - Python API for direct use in skills and scripts

## Engines

Each engine provides specialized functionality:

- **check_engine.py** - Batch property comparison with self-describing schema (`run_batch_check`)
- **stats_engine.py** - Paragraph filtering and distribution statistics (`filter_and_compute_stats`)
- **pdf_engine.py** - PDF text and table extraction (`extract_pdf`)
- **inspect_engine.py** - Unpack and inspect Word XML (`inspect_document`)
- **compare_engine.py** - Compare two documents for differences (`compare_documents`, `generate_diff_report`)
- **validate_engine.py** - Validate Word XML against OOXML XSD schemas (`validate_document`)
- **spec_engine.py** - Evaluate spec.md quality (`check_conflicts`, `check_structure`, `check_body_consistency`)