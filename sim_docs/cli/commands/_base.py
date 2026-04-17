"""Shared utilities for CLI commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Protocol


def write_output(data, output_path: str | None = None) -> None:
    """Write JSON data to file or stdout."""
    content = json.dumps(data, ensure_ascii=False, indent=2)
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")


class Command(Protocol):
    """Protocol for CLI commands."""

    NAME: str
    HELP: str

    def add_parser(self, subparsers) -> None:
        """Add subparser for this command."""
        ...

    def run(self, args) -> int:
        """Execute command, return exit code."""
        ...