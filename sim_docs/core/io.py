"""Output writing utilities."""

from __future__ import annotations

import json
import sys
from pathlib import Path


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