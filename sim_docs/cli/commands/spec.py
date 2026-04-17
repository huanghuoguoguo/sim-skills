"""Spec-check command - evaluate spec.md quality."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sim_docs.api import spec
from ._base import write_output


NAME = "spec-check"
HELP = "Evaluate spec.md quality"


def add_parser(subparsers) -> None:
    parser = subparsers.add_parser(NAME, help=HELP)
    parser.add_argument("--mode", required=True,
                        choices=["conflicts", "structure", "body-consistency", "common-sense"],
                        help="Check mode")
    parser.add_argument("input", nargs="?", help="Path to spec.md file (for conflicts/structure/common-sense mode)")
    parser.add_argument("--evidence", help="Path to evidence JSON (for body-consistency mode)")
    parser.add_argument("--checks", help="Path to checks JSON (for body-consistency mode)")
    parser.add_argument("--output", help="Output JSON file path")


def run(args) -> int:
    if args.mode == "conflicts":
        result = spec.check_conflicts(args.input)
        write_output(result, args.output)
        return 0 if result["status"] == "pass" else 1

    elif args.mode == "structure":
        result = spec.check_structure(args.input)
        write_output(result, args.output)
        return 0 if result["status"] == "pass" else 1

    elif args.mode == "body-consistency":
        evidence_path = Path(args.evidence).expanduser().resolve()
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        checks_path = Path(args.checks).expanduser().resolve()
        checks_raw = json.loads(checks_path.read_text(encoding="utf-8"))
        checks = checks_raw.get("checks", checks_raw) if isinstance(checks_raw, dict) else checks_raw
        result = spec.check_body_consistency(evidence, checks)
        write_output(result, args.output)
        return 0 if result["status"] == "pass" else 1

    elif args.mode == "common-sense":
        result = spec.check_common_sense(args.input)
        write_output(result, args.output)
        return 0 if result["status"] == "pass" else 1

    return 1