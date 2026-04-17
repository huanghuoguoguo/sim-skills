"""Check command - batch check document properties."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sim_docs.api import analysis
from sim_docs.analysis.checks import CHECK_SCHEMA
from ._base import write_output


NAME = "check"
HELP = "Batch check document properties"


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(NAME, help=HELP)
    parser.add_argument("input", nargs="?", help="Path to .docx/.dotm file")
    parser.add_argument("checks", nargs="?", help="Path to checks JSON file")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--schema", action="store_true", help="Print supported check types")


def run(args) -> int:
    if args.schema:
        write_output(CHECK_SCHEMA, None)
        return 0

    checks_path = Path(args.checks).expanduser().resolve()
    checks_raw = json.loads(checks_path.read_text(encoding="utf-8"))
    checks = checks_raw.get("checks", checks_raw) if isinstance(checks_raw, dict) else checks_raw

    result = analysis.check(args.input, checks)
    write_output(result, args.output)
    return 0