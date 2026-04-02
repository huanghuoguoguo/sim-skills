#!/usr/bin/env python3
"""Check obvious contradictions inside spec.md."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from spec_rules import parse_font_size_signals, parse_heading
from utils import resolve_path, write_json_output


def check_conflicts(path: str | Path) -> dict:
    spec_path = Path(path)
    lines = spec_path.read_text(encoding="utf-8").splitlines()

    conflicts = []
    headings: dict[int, str] = {}
    named_size_assignments: dict[str, list[dict]] = {}

    for line_number, raw_line in enumerate(lines, 1):
        parsed = parse_heading(raw_line)
        if parsed:
            level, text = parsed
            headings[level] = text
            for stale_level in list(headings):
                if stale_level > level:
                    headings.pop(stale_level, None)
            continue

        signals = parse_font_size_signals(raw_line)
        if signals["conflict"]:
            conflicts.append(
                {
                    "line_number": line_number,
                    "context": " / ".join(headings[level] for level in sorted(headings)),
                    "text": raw_line.strip(),
                    "type": "font_size_conflict",
                    "reasons": signals["conflict_reasons"],
                }
            )

        if len(signals["named_sizes"]) == 1 and len(signals["explicit_pts"]) == 1:
            name, _ = signals["named_sizes"][0]
            named_size_assignments.setdefault(name, []).append(
                {
                    "line_number": line_number,
                    "context": " / ".join(headings[level] for level in sorted(headings)),
                    "text": raw_line.strip(),
                    "pt": signals["explicit_pts"][0],
                }
            )

    for name, assignments in named_size_assignments.items():
        unique_pts = sorted({assignment["pt"] for assignment in assignments})
        if len(unique_pts) <= 1:
            continue
        conflicts.append(
            {
                "line_number": assignments[0]["line_number"],
                "context": assignments[0]["context"],
                "text": name,
                "type": "font_size_inconsistent_across_spec",
                "reasons": [
                    f"字号名 {name} 在 spec 中对应多个 pt 值："
                    + ", ".join(f"{pt:g}pt" for pt in unique_pts)
                ],
                "examples": assignments,
            }
        )

    return {
        "spec_path": str(spec_path),
        "status": "pass" if not conflicts else "needs_revision",
        "conflicts": conflicts,
        "summary": {
            "conflict_count": len(conflicts),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check obvious contradictions inside spec.md")
    parser.add_argument("spec", help="Path to spec.md")
    parser.add_argument("--output", help="Where to write JSON diagnostics")
    args = parser.parse_args()

    payload = check_conflicts(resolve_path(args.spec))
    write_json_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
