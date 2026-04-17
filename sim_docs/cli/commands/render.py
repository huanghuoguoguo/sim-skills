"""Render command - render page to image."""

from __future__ import annotations

import argparse

from sim_docs.api import word


NAME = "render"
HELP = "Render page to image"


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(NAME, help=HELP)
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--page", type=int, default=1, help="Page number (1-indexed)")
    parser.add_argument("--output", required=True, help="Output image file (e.g., page1.png)")


def run(args) -> int:
    word.render(args.input, page=args.page, output=args.output)
    print(f"Rendered page {args.page} to '{args.output}'")
    return 0