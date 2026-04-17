"""Inspect command - unpack document for XML inspection."""

from __future__ import annotations

import argparse

from sim_docs.api import word


NAME = "inspect"
HELP = "Unpack document for XML inspection"


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(NAME, help=HELP)
    parser.add_argument("input", help="Path to .docx/.dotm file")
    parser.add_argument("--output-dir", help="Output directory for unpacked files")
    parser.add_argument("--show", help="Show content of specific XML file")
    parser.add_argument("--list", action="store_true", help="List all XML files")
    parser.add_argument("--merge-runs", type=lambda x: x.lower() == "true", default=True, help="Merge adjacent runs")


def run(args) -> int:
    result = word.inspect(
        args.input,
        output_dir=args.output_dir,
        show=args.show,
        list_files=args.list,
        merge_runs=args.merge_runs,
    )
    print(result["message"])
    print(f"Output: {result['output_dir']}")
    if result.get("files"):
        print("\nXML files:")
        for f in result["files"]:
            print(f"  {f['path']} ({f['size']} bytes)")
    if result.get("show_content"):
        print(f"\n--- {args.show} ---")
        print(result["show_content"])
    elif result.get("show_error"):
        print(f"\n{result['show_error']}")
    return 0