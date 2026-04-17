"""Shared utilities for CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

from sim_docs.core.io import write_json_output
from sim_docs.core.paths import resolve_path


def write_output(data, output_path: str | None = None) -> None:
    """Write JSON data to file or stdout."""
    write_json_output(data, output_path)


def load_checks_json(path: str) -> list | dict:
    """Load checks from JSON file, unwrapping {"checks": [...]} if present."""
    resolved = resolve_path(path)
    raw = json.loads(Path(resolved).read_text(encoding="utf-8"))
    return raw.get("checks", raw) if isinstance(raw, dict) else raw