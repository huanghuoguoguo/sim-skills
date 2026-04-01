#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from spec_validation import load_json_file, validate_report_structure


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate report.json structure")
    parser.add_argument("report", help="Path to report.json")
    args = parser.parse_args()

    try:
        _, report = load_json_file(args.report)
    except FileNotFoundError:
        print(f"Error: File not found {args.report}", file=sys.stderr)
        return 1

    errors = validate_report_structure(report)
    if errors:
        print("❌ REPORT VALIDATION FAILED")
        for error in errors:
            print(f" - {error}")
        return 1

    print("✅ REPORT VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
