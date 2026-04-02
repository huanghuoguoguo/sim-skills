"""Shared utilities for skill scripts."""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path


def resolve_path(path_str: str) -> str:
    """Resolve a path, supporting glob patterns."""
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str


def write_json_output(data, output_path: str | None = None) -> None:
    """Write JSON data to a file or stdout."""
    content = json.dumps(data, ensure_ascii=False, indent=2)
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")


def setup_word_scripts_path(anchor_file: str) -> None:
    """Add the word/scripts directory to sys.path, relative to a skill script file.

    Usage at the top of any skill script that needs docx_parser:
        setup_word_scripts_path(__file__)
    """
    word_scripts = Path(anchor_file).resolve().parents[2] / "word" / "scripts"
    if str(word_scripts) not in sys.path:
        sys.path.insert(0, str(word_scripts))
