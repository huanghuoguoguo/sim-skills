# CLI Reference

Complete reference for `sim_docs` CLI commands. Run `python3 -m sim_docs --help` for quick overview.

## Commands Overview

| Command | Purpose |
|---------|---------|
| `parse` | Parse .docx/.dotm to structured facts (JSON) |
| `query-text` | Search paragraphs by keyword |
| `query-style` | Query resolved style properties |
| `stats` | Filter paragraphs + compute distributions |
| `check` | Batch property comparison |
| `render` | Render page as PNG |
| `compare` | Compare two Word documents |
| `read-pdf` | Extract text/tables from PDF |
| `read-text` | Read .txt/.md/.docx content |
| `validate` | Validate XML structure |
| `inspect` | Unpack and inspect raw XML |
| `spec-check` | Evaluate spec.md quality |

---

## parse

Parse .docx or .dotm into structured DocumentIR (JSON facts).

```bash
python3 -m sim_docs parse <file.docx> [--output facts.json]
```

**Output structure**:
- `metadata`: document info (title, author, etc.)
- `layout`: page size, margins
- `paragraphs`: list of ParagraphFact with font, size, alignment, spacing, indentation
- `styles`: list of StyleFact with resolved properties
- `headers` / `footers`: header/footer content if present

**Use cases**:
- `extract-spec` needs template facts
- `check-thesis` needs thesis paragraph/style data
- Other tools need unified document parsing base

**Note**: Only supports `.docx` and `.dotm`. Not `.doc` or `.pdf`.

---

## query-text

Search paragraphs by keyword. Returns matching paragraphs with index, style, and properties.

```bash
python3 -m sim_docs query-text <file.docx> --keyword "摘要"
```

**Use cases**:
- Find formatting instructions: "宋体", "字号", "格式要求"
- Locate sections: "摘要", "参考文献", "目录"
- Extract text-based rules from templates

**Output**: List of ParagraphFact objects with id, index, text, style_name, properties.

---

## query-style

Query resolved style properties. Returns final values after inheritance cascade (direct format > current style > parent style > document default).

```bash
python3 -m sim_docs query-style <file.docx> --style "Heading 1"
```

**Use cases**:
- Check what font/size "Heading 1" uses
- Verify "正文" style configuration
- Confirm effective properties when template has inheritance chain

**Output**: List of StyleFact objects with name, style_id, type, properties.

---

## stats

Filter paragraphs by style/content and compute property distributions.

```bash
python3 -m sim_docs stats <facts.json|file.docx> [options]
```

**Parameters**:

| Parameter | Description |
|-----------|-------------|
| `--style-hint HINT` | Keep only matching style names (repeatable) |
| `--exclude-text TEXT` | Exclude paragraphs containing this text (repeatable) |
| `--heading-prefix REGEX` | Exclude matching heading prefixes (repeatable) |
| `--heading-keyword KW` | Exclude paragraphs starting with this keyword (repeatable) |
| `--instruction-hint HINT` | Exclude instructional text (repeatable) |
| `--min-length N` | Minimum paragraph length in chars (default: 0) |
| `--require-body-shape` | Keep only justified paragraphs or those with first-line indent |
| `--sample-limit N` | Maximum sample count (default: 8) |
| `--output PATH` | Output file path |

**Output structure**:
```json
{
  "input": "file.docx",
  "filters": {"style_hints": [...], "min_length": 20},
  "summary": {
    "candidate_count": 150,
    "style_distribution": [{"value": "Normal", "count": 140}],
    "font_size_distribution": [{"value": 12.0, "count": 135}],
    "line_spacing_distribution": [{"value": "multiple:1.5", "count": 130}],
    "first_line_indent_distribution": [{"value": 21.0, "count": 128}],
    "east_asia_font_distribution": [{"value": "宋体", "count": 120}],
    "ascii_font_distribution": [{"value": "Times New Roman", "count": 90}],
    "candidate_examples": [...]
  }
}
```

**Critical rule**: Always run `stats --style-hint <hint>` to discover actual style names before constructing check instructions.

---

## check

Batch property comparison engine. Compare facts against expected values.

```bash
# View supported check types
python3 -m sim_docs check --schema

# Execute checks
python3 -m sim_docs check <facts.json|file.docx> <checks.json> [--output result.json]
```

### Supported Check Types

| type | target | expected format | tolerance |
|------|--------|-----------------|-----------|
| `font` | font family | string, scope: `east_asia` / `ascii` | exact match |
| `font_size` | font size in pt | number | 0.2 pt |
| `alignment` | paragraph alignment | `left` / `center` / `right` / `justify` / `distribute` | exact match |
| `line_spacing` | line spacing | `{"mode": "multiple|exact|at_least", "value": N}` | 0.1 |
| `spacing_before` | space before in pt | number | 0.5 pt |
| `spacing_after` | space after in pt | number | 0.5 pt |
| `first_line_indent` | first line indent in pt | number | 0.5 pt |
| `margin` | page margin in cm | number, requires `side` | 0.05 cm |
| `page_size` | paper size | `"A4"` | exact match |

### Selectors

| selector | behavior |
|----------|----------|
| `style:<name>` | Match paragraphs with style_name matching `<name>` or any `style_aliases` |
| `caption:figure` | Match figure captions by `style_aliases` or `caption_prefix_patterns` |
| `caption:table` | Match table captions by `style_aliases` or `caption_prefix_patterns` |
| `document:layout` | Document-level; auto-assigned for `margin` and `page_size` |

### Check Instruction Format

```json
[
  {
    "id": "body-font-east",
    "type": "font",
    "scope": "east_asia",
    "selector": "style:Normal",
    "style_aliases": ["Normal", "正文", "Body Text", "Body Text Indent"],
    "expected": "宋体",
    "section": "正文格式",
    "rule_text": "正文中文字体为宋体"
  },
  {
    "id": "body-font-size",
    "type": "font_size",
    "selector": "style:Normal",
    "style_aliases": ["Normal", "正文", "Body Text"],
    "expected": 12,
    "expected_display": "小四（12pt）"
  },
  {
    "id": "body-line-spacing",
    "type": "line_spacing",
    "selector": "style:Normal",
    "style_aliases": ["Normal", "正文"],
    "expected": {"mode": "multiple", "value": 1.5}
  },
  {
    "id": "h1-alignment",
    "type": "alignment",
    "selector": "style:Heading 1",
    "style_aliases": ["Heading 1", "标题 1"],
    "expected": "center"
  },
  {
    "id": "fig-caption-font-size",
    "type": "font_size",
    "selector": "caption:figure",
    "style_aliases": ["Caption", "题注"],
    "caption_prefix_patterns": ["^图\\s*\\d", "^Figure\\s*\\d"],
    "expected": 10.5
  },
  {"id": "page-size", "type": "page_size", "expected": "A4"},
  {"id": "margin-top", "type": "margin", "side": "top", "expected": 2.54}
]
```

### Output Structure

```json
{
  "summary": {"total": 10, "pass": 8, "fail": 1, "unresolved": 1},
  "results": [
    {
      "id": "body-font-size",
      "type": "font_size",
      "status": "pass",
      "expected": "小四（12pt）",
      "actual": "300 ok",
      "matched_count": 300,
      "issues": []
    },
    {
      "id": "h1-alignment",
      "type": "alignment",
      "status": "fail",
      "expected": "center",
      "actual": "3 ok / 2 mismatch",
      "matched_count": 5,
      "issues": [
        {"paragraph_id": "p-15", "actual": "left", "text_preview": "第三章 系统设计"}
      ]
    }
  ]
}
```

### Critical Rules

- **`style_aliases` must be complete**: Missing any style name causes missed paragraphs.
- **`unresolved` means 0 matches**: Selector or style_aliases likely wrong.
- **Use `stats` first**: Discover actual style names before constructing checks.

### Chinese Font Size Mapping

| Chinese name | pt value |
|-------------|----------|
| 初号 | 42 |
| 小初 | 36 |
| 一号 | 26 |
| 小一 | 24 |
| 二号 | 22 |
| 小二 | 18 |
| 三号 | 16 |
| 小三 | 15 |
| 四号 | 14 |
| 小四 | 12 |
| 五号 | 10.5 |
| 小五 | 9 |

**First line indent**: 2 Chinese characters at 小四 = 24pt. Formula: `indent_pt = font_size_pt * 2`.

---

## render

Render a specific page as PNG image.

```bash
python3 -m sim_docs render <file.docx> --page 1 --output page1.png
```

**Use cases**:
- Visual verification when text-based facts conflict
- Check page number position, header/footer layout
- Verify cover page, TOC dot leaders

**Note**: Requires LibreOffice + PyMuPDF. Install with: `pip install PyMuPDF`.

---

## compare

Compare formatting between two Word documents.

```bash
python3 -m sim_docs compare <reference.docx> <target.docx> [--output diff.json] [--report diff_report.md]
```

**Output structure**:
```json
{
  "reference": "ref.docx",
  "target": "target.docx",
  "diff_count": 5,
  "diffs": [
    {
      "type": "structure",
      "aspect": "paragraph_count",
      "reference": 100,
      "target": 98,
      "message": "段落数量不一致"
    },
    {
      "type": "layout",
      "aspect": "page_margins.top_cm",
      "reference": 2.54,
      "target": 3.0,
      "message": "上边距：参考=2.54, 目标=3.0"
    }
  ]
}
```

---

## read-pdf

Extract text and tables from PDF files.

```bash
# Extract text from all pages
python3 -m sim_docs read-pdf <file.pdf>

# Extract from specific pages
python3 -m sim_docs read-pdf <file.pdf> --pages 1-5

# Extract tables only
python3 -m sim_docs read-pdf <file.pdf> --tables

# Full extraction (text + tables)
python3 -m sim_docs read-pdf <file.pdf> --all --output result.json
```

**Output structure**:
```json
{
  "input": "spec.pdf",
  "page_count": 10,
  "pages": [{"page_number": 1, "text": "...", "tables": [...]}],
  "full_text": "all pages combined..."
}
```

---

## read-text

Read plain text from .txt, .md, or .docx files.

```bash
python3 -m sim_docs read-text <file.txt>
python3 -m sim_docs read-text <file.md>
python3 -m sim_docs read-text <file.docx>
```

**Output structure**:
```json
{
  "input": "file.txt",
  "text": "file content...",
  "line_count": 100
}
```

---

## validate

Validate Word document XML structure against OOXML XSD schemas.

```bash
# Validate
python3 -m sim_docs validate <file.docx>

# Validate with auto-repair
python3 -m sim_docs validate <file.docx> --auto-repair

# Verbose output
python3 -m sim_docs validate <file.docx> -v
```

### Validation Checks

| check | description |
|-------|-------------|
| XML well-formedness | All XML files parse without errors |
| Namespace declarations | All referenced namespaces declared |
| Unique IDs | comment IDs, bookmark IDs unique |
| File references | All .rels targets point to existing files |
| Content types | All files declared in [Content_Types].xml |
| XSD schema compliance | XML conforms to OOXML standard |
| Whitespace preservation | w:t elements with whitespace have xml:space="preserve" |
| ID constraints | paraId < 0x80000000, durableId < 0x7FFFFFFF |
| Comment markers | commentRangeStart/End properly paired |

### Auto-Repair

With `--auto-repair`, fixes:
- durableId values exceeding OOXML limits
- Missing `xml:space="preserve"` on `<w:t>` elements

---

## inspect

Unpack .docx to raw XML files for debugging.

```bash
# Unpack to directory (pretty-printed XML)
python3 -m sim_docs inspect <file.docx> --output-dir unpacked/

# Unpack and show specific XML file
python3 -m sim_docs inspect <file.docx> --show word/document.xml

# Unpack and list all XML files
python3 -m sim_docs inspect <file.docx> --list
```

**Output directory**:
```
unpacked/
├── [Content_Types].xml
├── _rels/
│   └── .rels
├── word/
│   ├── document.xml      # Main document content
│   ├── styles.xml        # Style definitions
│   ├── numbering.xml     # List/numbering definitions
│   ├── settings.xml      # Document settings
│   └── _rels/
│       └── document.xml.rels
└── docProps/
    ├── app.xml
    └── core.xml
```

**Use cases**:
- python-docx parser misses information
- Need raw OOXML XML (w:rFonts, numbering, field codes)
- Debugging edge cases

---

## spec-check

Evaluate spec.md quality for completeness and consistency.

```bash
# Check for conflicts between rules
python3 -m sim_docs spec-check --mode conflicts <spec.md>

# Check section structure completeness
python3 -m sim_docs spec-check --mode structure <spec.md>

# Check body text consistency (requires evidence from actual document)
python3 -m sim_docs spec-check --mode body-consistency --evidence <evidence.json> --checks <checks.json>
```

**Modes**:
- `conflicts`: Find contradictory rules (e.g., "宋体" vs "黑体" for same selector)
- `structure`: Verify all required sections present
- `body-consistency`: Cross-validate spec rules against actual document evidence