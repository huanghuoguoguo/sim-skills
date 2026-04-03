---
name: validate-word
description: "Use this skill to validate Word document XML structure against OOXML XSD schemas. Triggers: when you need to check if a .docx file has structural issues (broken references, invalid IDs, malformed XML, missing content types), or when diagnosing why a document appears corrupt. Supports auto-repair for common issues (durableId overflow, missing xml:space). Do NOT use for format checking (font, size, spacing) — use batch-check for that. Do NOT use for .doc or .pdf files."
---

# validate-word

Validates Word document XML structure against ISO/IEC 29500 OOXML schemas.

Adapted from Anthropic's official docx skill. This is a structural validator, not a format checker.

## Use Cases

- Diagnosing corrupt or broken .docx files
- Verifying XML integrity after document manipulation
- Pre-checking documents before processing with other tools
- Auto-repairing common structural issues

## Commands

```bash
# Validate a .docx file
python3 .claude/skills/validate-word/scripts/run.py <file.docx>

# Validate with auto-repair
python3 .claude/skills/validate-word/scripts/run.py <file.docx> --auto-repair

# Verbose output
python3 .claude/skills/validate-word/scripts/run.py <file.docx> -v
```

## What It Validates

| check | description |
|-------|------------|
| XML well-formedness | All XML files parse without errors |
| Namespace declarations | All referenced namespaces are declared |
| Unique IDs | comment IDs, bookmark IDs etc. are unique |
| File references | All .rels targets point to existing files |
| Content types | All files are declared in [Content_Types].xml |
| XSD schema compliance | XML conforms to OOXML standard |
| Whitespace preservation | w:t elements with whitespace have xml:space="preserve" |
| ID constraints | paraId < 0x80000000, durableId < 0x7FFFFFFF |
| Comment markers | commentRangeStart/End are properly paired |

## Auto-Repair

With `--auto-repair`, automatically fixes:
- durableId values exceeding OOXML limits (regenerates valid ID)
- Missing `xml:space="preserve"` on `<w:t>` elements with whitespace
