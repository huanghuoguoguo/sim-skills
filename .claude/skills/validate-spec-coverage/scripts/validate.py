#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from spec_validation import THESIS_COVERAGE_PROFILES, load_json_file, validate_spec_coverage


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate spec.json coverage")
    parser.add_argument("spec", help="Path to spec.json")
    parser.add_argument(
        "--profile",
        default="thesis-basic",
        choices=sorted(THESIS_COVERAGE_PROFILES),
        help="Coverage profile to apply",
    )
    args = parser.parse_args()

    try:
        _, spec = load_json_file(args.spec)
    except FileNotFoundError:
        print(f"Error: File not found {args.spec}", file=sys.stderr)
        return 1

    errors = validate_spec_coverage(spec, profile=args.profile)
    if errors:
        print(f"❌ SPEC COVERAGE VALIDATION FAILED ({args.profile})")
        for error in errors:
            print(f" - {error}")
        return 1

    print(f"✅ SPEC COVERAGE VALIDATION PASSED ({args.profile})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
