"""Compare command - compare two documents."""

from __future__ import annotations

import argparse
from pathlib import Path

from sim_docs.api import word
from sim_docs.word.compare import generate_diff_report
from ._base import write_output


NAME = "compare"
HELP = "Compare two documents"


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(NAME, help=HELP)
    parser.add_argument("reference", help="Path to reference .docx file")
    parser.add_argument("target", help="Path to target .docx file")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--report", help="Output Markdown report path")


def run(args) -> int:
    result = word.compare(args.reference, args.target)
    write_output(result, args.output)
    if args.report:
        report = generate_diff_report(result["diffs"], args.reference, args.target)
        Path(args.report).write_text(report, encoding="utf-8")
        print(f"Markdown report saved to: {args.report}")
    return 0