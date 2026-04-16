---
name: inspect-word-xml
description: "Use this skill to unpack a .docx/.dotm file and inspect raw XML for debugging. Triggers: when python-docx parser misses information, when you need to see raw OOXML XML (e.g., w:rFonts attributes, numbering definitions, complex field codes), or when diagnosing edge cases in document parsing. Read-only inspection — does not modify the document. Do NOT use for normal document analysis — use parse-word first. Only use when structured parsing is insufficient."
---

# inspect-word-xml

Unpack a Word document to its raw XML files for inspection.

Adapted from Anthropic's official docx skill. This is a read-only debugging tool.

## Use Cases

- python-docx parser returns unexpected results — check the raw XML
- Need to inspect numbering definitions, field codes, or other elements not exposed by python-docx
- Debugging w:rFonts, w:pPr, or other low-level XML attributes
- Checking document.xml structure directly

## Commands

```bash
# Unpack to directory (pretty-printed XML)
python3 -m sim_docs inspect <file.docx> --output-dir unpacked/

# Unpack and show specific XML file
python3 -m sim_docs inspect <file.docx> --show word/document.xml

# Unpack and list all XML files
python3 -m sim_docs inspect <file.docx> --list

# Merge adjacent runs for cleaner XML (default: on)
python3 -m sim_docs inspect <file.docx> --merge-runs false --output-dir unpacked/
```

## Output

Unpacked directory contains the raw docx ZIP contents with pretty-printed XML:

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
