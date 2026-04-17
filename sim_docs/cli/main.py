"""CLI main entry point with auto-registration."""

from __future__ import annotations

import argparse

from .commands import parse, query, check, stats, render, validate, inspect, compare, read, spec


# Explicit list avoids importlib magic; easier for type checkers and debugging
COMMANDS = [
    (parse.NAME, parse.HELP, parse.add_parser, parse.run),
    (query.NAME_STYLE, query.HELP_STYLE, query.add_parser_style, query.run_style),
    (query.NAME_TEXT, query.HELP_TEXT, query.add_parser_text, query.run_text),
    (check.NAME, check.HELP, check.add_parser, check.run),
    (stats.NAME, stats.HELP, stats.add_parser, stats.run),
    (render.NAME, render.HELP, render.add_parser, render.run),
    (validate.NAME, validate.HELP, validate.add_parser, validate.run),
    (inspect.NAME, inspect.HELP, inspect.add_parser, inspect.run),
    (compare.NAME, compare.HELP, compare.add_parser, compare.run),
    (read.NAME_TEXT, read.HELP_TEXT, read.add_parser_text, read.run_text),
    (read.NAME_PDF, read.HELP_PDF, read.add_parser_pdf, read.run_pdf),
    (spec.NAME, spec.HELP, spec.add_parser, spec.run),
]


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sim-docs",
        description="Unified document service for parsing, querying, checking, and rendering documents.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    handlers = {}
    for name, help_text, add_parser_fn, run_fn in COMMANDS:
        add_parser_fn(subparsers)
        handlers[name] = run_fn

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())