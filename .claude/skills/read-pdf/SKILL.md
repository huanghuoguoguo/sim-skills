---
name: read-pdf
description: "Use this skill to extract text, tables, and structure from PDF files. Triggers: when user provides a .pdf file containing formatting rules, specification documents, or reference material that needs to be read. Supports text extraction (with layout preservation), table extraction, and page-to-image conversion. Do NOT use for .docx files — use parse-word instead. Do NOT use for creating or editing PDFs."
---

# read-pdf

Extract text, tables, and structural information from PDF files.

## Use Cases

- Reading PDF formatting specifications for extract-spec workflow
- Extracting tables of formatting rules from PDF documents
- Converting PDF pages to images for visual reference
- Reading scanned PDF content via text extraction

## Commands

```bash
# Extract text from all pages
python3 -m sim_docs read-pdf <file.pdf>

# Extract text from specific pages
python3 -m sim_docs read-pdf <file.pdf> --pages 1-5

# Extract tables
python3 -m sim_docs read-pdf <file.pdf> --tables

# Full extraction (text + tables + structure)
python3 -m sim_docs read-pdf <file.pdf> --all --output result.json
```

## Output Structure

```json
{
  "input": "spec.pdf",
  "page_count": 10,
  "pages": [
    {
      "page_number": 1,
      "width": 595.0,
      "height": 842.0,
      "text": "page text content...",
      "tables": [
        [["Header1", "Header2"], ["val1", "val2"]]
      ]
    }
  ],
  "full_text": "all pages combined..."
}
```
