"""Stats command - paragraph filtering and statistics."""

from __future__ import annotations

import argparse

from sim_docs.api import analysis
from ._base import write_output


NAME = "stats"
HELP = "Paragraph filtering and statistics"


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(NAME, help=HELP)
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--style-hint", help="Style name to filter")
    parser.add_argument("--min-length", type=int, default=0, help="Min paragraph text length")
    parser.add_argument("--require-body-shape", action="store_true", help="Only paragraphs with justify/indent")
    parser.add_argument("--exclude-text", action="append", default=[], help="Exclude paragraphs containing text")
    parser.add_argument("--heading-prefix", action="append", default=[], help="Regex for heading exclusion")
    parser.add_argument("--heading-keyword", action="append", default=[], help="Keyword prefix for heading exclusion")
    parser.add_argument("--instruction-hint", action="append", default=[], help="Text hint for instruction exclusion")
    parser.add_argument("--sample-limit", type=int, default=8, help="Max candidate examples")


def run(args) -> int:
    result = analysis.stats(
        args.input,
        style_hint=args.style_hint,
        min_length=args.min_length,
        require_body_shape=args.require_body_shape,
        exclude_texts=args.exclude_text,
        heading_prefixes=args.heading_prefix,
        heading_keywords=args.heading_keyword,
        instruction_hints=args.instruction_hint,
        sample_limit=args.sample_limit,
    )
    output_data = {"input": args.input, "filters": result.get("filters", {}), "summary": result.get("summary", {})}
    write_output(output_data, args.output)
    return 0