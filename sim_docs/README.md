# sim_docs - Unified Document Service

A unified service layer for document parsing, querying, checking, and rendering with built-in caching support.

## Architecture

The package is organized into domain subpackages with strict one-way layering:

```
cli → api → {word, pdf, text, analysis, spec} → core
```

```
sim_docs/
├── __init__.py          # Package exports
├── __main__.py          # CLI entry (python3 -m sim_docs)
├── api.py               # Namespace facade (api.word, api.analysis, etc.)
├── service.py           # Deprecated DocumentService wrapper
│
├── core/                # Infrastructure (no domain knowledge)
│   ├── cache.py         # LRU cache for parsed documents
│   ├── paths.py         # Path resolution + glob
│   ├── io.py            # JSON/text output helpers
│   ├── helpers.py       # normalized(), values_close()
│   └── soffice.py       # LibreOffice subprocess helper
│
├── word/                # Word (.docx/.dotm) domain
│   ├── parser.py        # Core Word parser (CJK/ASCII font separation)
│   ├── models.py        # Parser dataclasses
│   ├── adapter.py       # Parser facade with path resolution
│   ├── render.py        # Page rendering (LibreOffice + PyMuPDF)
│   ├── inspect.py       # XML unpacking and inspection
│   ├── compare.py       # Document comparison
│   └── validate/        # XSD schema validation (vendored schemas)
│
├── pdf/extract.py       # PDF text/table extraction
├── text/read.py         # .txt/.md/.docx text reading
│
├── analysis/            # Document-agnostic analysis
│   ├── checks.py        # Batch property comparison
│   └── stats.py         # Paragraph filtering + statistics
│
├── spec/                # Spec.md evaluation
│   ├── engine.py        # check_conflicts/structure/body-consistency/common-sense
│   ├── rules.py         # Font-size parsing, heading helpers
│   └── profiles.py      # Thesis profile configuration
│
├── cli/                 # CLI with auto-registration
│   ├── main.py          # Explicit COMMANDS registry
│   └── commands/        # Per-command modules
│
└── tests/               # Mirrors source layout
```

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
python3 -m sim_docs check --schema  # View supported check types

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

### Recommended: Namespace API

```python
from sim_docs import api

# Parse document (cached)
facts = api.word.parse("thesis.docx")

# Query styles
styles = api.word.query_style("thesis.docx", "Heading 1")

# Query text
paragraphs = api.word.query_text("thesis.docx", "宋体")

# Batch check
result = api.analysis.check("thesis.docx", [
    {"type": "font", "selector": "style:Normal", "expected": "宋体"},
    {"type": "font_size", "selector": "style:Heading 1", "expected": 16},
])

# Get statistics
stats = api.analysis.stats("thesis.docx", min_length=20, require_body_shape=True)

# Render page
output_path = api.word.render("thesis.docx", page=1, output="page1.png")

# Validate document
validation = api.word.validate("thesis.docx", auto_repair=True)

# Compare documents
diff = api.word.compare("reference.docx", "target.docx")

# Read text/pdf
text = api.text.read("file.txt")
pdf_data = api.pdf.extract("file.pdf", pages="1-5")

# Evaluate spec.md
conflicts = api.spec.check_conflicts("spec.md")
structure = api.spec.check_structure("spec.md")
body = api.spec.check_body_consistency(evidence, checks)

# Cache management
stats = api.cache_stats()
api.clear_cache()
```

### Legacy: DocumentService (deprecated)

```python
from sim_docs import DocumentService

service = DocumentService()  # Still works, but deprecated
facts = service.parse("thesis.docx")
# ... same methods as before
```

## Caching

The API uses a shared in-memory LRU cache:

- **Cache size**: 32 documents by default
- **Invalidation**: Automatic when source file is modified
- **Statistics**: `api.cache_stats()` returns {"hits", "misses", "size", "max_size"}
- **Clear**: `api.clear_cache()` resets cache

## Supported Formats

- `.docx` - Word documents
- `.dotm` - Word templates
- `.docm` - Macro-enabled Word documents
- `.txt`, `.md` - Text files (read-text)
- `.pdf` - PDF files (read-pdf)

## Domain Modules

Each domain provides specialized functionality:

| Domain | Module | Key Functions |
|--------|--------|---------------|
| word | parser.py | `parse_word_document` |
| word | validate/ | `validate_document`, DOCXSchemaValidator |
| word | compare.py | `compare_documents`, `generate_diff_report` |
| analysis | checks.py | `run_batch_check`, CHECK_SCHEMA |
| analysis | stats.py | `filter_and_compute_stats` |
| spec | engine.py | `check_conflicts`, `check_structure`, `check_body_consistency` |
| pdf | extract.py | `extract_pdf` |
| text | read.py | `read_text_source` |

## Installation

The package is part of the sim-skills project. No separate installation required.

Dependencies:
- `python-docx` - Word document parsing
- `defusedxml` - Safe XML parsing
- `lxml` - XSD schema validation
- `PyMuPDF` (optional) - Page rendering