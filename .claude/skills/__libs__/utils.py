"""Shared utilities for skill scripts."""

from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path


def resolve_path(path_str: str) -> str:
    """Resolve a path, supporting glob patterns."""
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str


def _write_to_file(content: str, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json_output(data, output_path: str | None = None) -> None:
    """Write JSON data to a file or stdout."""
    content = json.dumps(data, ensure_ascii=False, indent=2)
    if output_path:
        _write_to_file(content, output_path)
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")


def write_text_output(content: str, output_path: str | None = None) -> None:
    """Write plain text to a file or stdout."""
    if output_path:
        _write_to_file(content, output_path)
    else:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")


def setup_word_scripts_path(anchor_file: str) -> None:
    """Add the word/scripts directory to sys.path, relative to a skill script file.

    Usage at the top of any skill script that needs docx_parser:
        setup_word_scripts_path(__file__)
    """
    word_scripts = Path(anchor_file).resolve().parents[2] / "word" / "scripts"
    if str(word_scripts) not in sys.path:
        sys.path.insert(0, str(word_scripts))


def normalized(value: str | None) -> str:
    """Remove whitespace and lowercase for comparison."""
    if value is None:
        return ""
    return re.sub(r"\s+", "", value).lower()


def values_close(expected: float, actual: float, tolerance: float = 0.5) -> bool:
    """Compare numeric values within tolerance."""
    if expected is None or actual is None:
        return False
    try:
        return abs(float(expected) - float(actual)) <= tolerance
    except (TypeError, ValueError):
        return False


def load_facts(path: str, anchor_file: str | None = None) -> dict:
    """Load document facts from JSON or parse from .docx/.dotm.

    Args:
        path: Path to a .json facts file or a .docx/.dotm document.
        anchor_file: Caller's __file__, used to locate docx_parser.
            Required when path is a Word file.
    """
    if path.endswith(".json"):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    if anchor_file is None:
        raise ValueError("anchor_file is required when loading .docx/.dotm")
    setup_word_scripts_path(anchor_file)
    from docx_parser import parse_word_document
    return parse_word_document(path).to_dict()
