#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from spec_validation import load_json_file, validate_spec_structure


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate spec.json structure")
    parser.add_argument("spec", help="Path to spec.json")
    args = parser.parse_args()

    try:
        _, spec = load_json_file(args.spec)
    except FileNotFoundError:
        print(f"Error: File not found {args.spec}", file=sys.stderr)
        return 1

    errors = validate_spec_structure(spec)
    if errors:
        print("❌ SPEC STRUCTURE VALIDATION FAILED")
        for error in errors:
            print(f" - {error}")
        return 1

    print("✅ SPEC STRUCTURE VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
