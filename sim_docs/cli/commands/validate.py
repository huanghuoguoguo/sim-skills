"""Validate command - validate document XML structure."""

from __future__ import annotations

import argparse

from sim_docs.api import word


NAME = "validate"
HELP = "Validate document XML structure"


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(NAME, help=HELP)
    parser.add_argument("input", help="Path to .docx file")
    parser.add_argument("--auto-repair", action="store_true", help="Automatically repair issues")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")


def run(args) -> int:
    result = word.validate(args.input, auto_repair=args.auto_repair, verbose=args.verbose)
    if result["success"]:
        print("All validations PASSED!")
        if result["repairs"]:
            print(f"Auto-repaired {result['repairs']} issue(s)")
        return 0
    else:
        print("Validation FAILED")
        return 1