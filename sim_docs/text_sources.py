from __future__ import annotations

from pathlib import Path
import sys


def read_text_source(path_str: str) -> str:
    path = Path(path_str)
    suffix = path.suffix.lower()

    if suffix in {".txt", ".md", ".json"}:
        return path.read_text(encoding="utf-8")

    if suffix in {".docx", ".dotm"}:
        word_scripts = Path(__file__).resolve().parent.parent / "word" / "scripts"
        if str(word_scripts) not in sys.path:
            sys.path.insert(0, str(word_scripts))
        from docx_parser import parse_word_document

        facts = parse_word_document(str(path))
        return "\n".join(
            paragraph.text for paragraph in facts.paragraphs if paragraph.text.strip()
        )

    raise ValueError(f"Unsupported text source: {path_str}")
