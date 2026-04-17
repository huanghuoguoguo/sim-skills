"""Parse command - parse Word document to structured facts."""

from __future__ import annotations

import argparse

from sim_docs.api import word
from ._base import write_output


NAME = "parse"
HELP = "Parse Word document to structured facts"


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(NAME, help=HELP)
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--output", help="Output JSON file path")


def run(args) -> int:
    facts = word.parse(args.input)
    write_output(facts.to_dict(), args.output)
    return 0