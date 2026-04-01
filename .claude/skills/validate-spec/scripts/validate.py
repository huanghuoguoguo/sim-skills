#!/usr/bin/env python3
"""Compatibility validator for spec.json."""

import argparse
import sys
from pathlib import Path


libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from spec_validation import (
    load_json_file,
    validate_spec_coverage,
    validate_spec_consumability,
    validate_spec_structure,
)

def main():
    parser = argparse.ArgumentParser(description="Validate JSON spec with structure and coverage checks")
    parser.add_argument("spec", help="Path to the extracted spec.json")
    parser.add_argument(
        "--profile",
        default="thesis-basic",
        help="Coverage profile to apply (default: thesis-basic)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode: enforce supported selectors and properties",
    )
    args = parser.parse_args()

    try:
        _, spec_data = load_json_file(args.spec)
    except FileNotFoundError:
        print(f"Error: File not found {args.spec}", file=sys.stderr)
        sys.exit(1)

    errors = []
    errors.extend(validate_spec_structure(spec_data))
    errors.extend(validate_spec_coverage(spec_data, profile=args.profile))
    errors.extend(validate_spec_consumability(spec_data, strict=args.strict))

    if errors:
        print("\n❌ VALIDATION FAILED")
        for err in errors:
            print(f" - {err}")
        sys.exit(1)
    else:
        print("\n✅ SPEC VALIDATION PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
