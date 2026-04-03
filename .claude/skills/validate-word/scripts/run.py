#!/usr/bin/env python3
"""Validate Word document XML against OOXML schemas.

Usage:
    python run.py <file.docx> [--auto-repair] [-v]

Adapted from Anthropic's official docx skill.
"""

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path

# Add validators to path
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from validators import DOCXSchemaValidator


def main():
    parser = argparse.ArgumentParser(description="Validate Word document XML structure")
    parser.add_argument("file", help="Path to .docx file")
    parser.add_argument(
        "--auto-repair",
        action="store_true",
        help="Automatically repair common issues (hex IDs, whitespace preservation)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: {path} does not exist")
        sys.exit(1)

    if path.suffix.lower() not in {".docx", ".dotm"}:
        print(f"Error: {path} must be a .docx or .dotm file")
        sys.exit(1)

    # Unpack to temp directory for validation
    temp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(temp_dir)
    except zipfile.BadZipFile:
        print(f"Error: {path} is not a valid ZIP/DOCX file")
        sys.exit(1)

    unpacked_dir = Path(temp_dir)

    validator = DOCXSchemaValidator(
        unpacked_dir, path, verbose=args.verbose
    )

    if args.auto_repair:
        total_repairs = validator.repair()
        if total_repairs:
            print(f"Auto-repaired {total_repairs} issue(s)")

    success = validator.validate()

    if success:
        print("All validations PASSED!")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
