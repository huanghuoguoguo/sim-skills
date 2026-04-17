"""Check command - batch check document properties."""

from __future__ import annotations

from sim_docs.api import analysis
from sim_docs.analysis.checks import CHECK_SCHEMA
from ._base import write_output, load_checks_json


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

    checks = load_checks_json(args.checks)
    result = analysis.check(args.input, checks)
    write_output(result, args.output)
    return 0