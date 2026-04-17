"""Validate engine for Word document XML structure validation.

Migrated from .claude/skills/validate-word/scripts/run.py.
Note: validators.py logic is integrated here.
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Any


def validate_document(
    path: str | Path,
    auto_repair: bool = False,
    verbose: bool = False,
) -> dict:
    """Validate Word document XML structure against OOXML schemas.

    Args:
        path: Path to .docx file.
        auto_repair: Automatically repair common issues.
        verbose: Enable verbose output.

    Returns:
        Dict with input, success, repairs, and errors.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file type is not supported.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    if path.suffix.lower() not in {".docx", ".dotm"}:
        raise ValueError(f"File must be .docx or .dotm: {path}")

    # Unpack to temp directory
    temp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(temp_dir)
    except zipfile.BadZipFile:
        raise ValueError(f"Not a valid ZIP/DOCX file: {path}")

    unpacked_dir = Path(temp_dir)

    # Import validator from validate-word skill
    validate_path = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "validate-word" / "scripts"
    if str(validate_path) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(validate_path))

    from validators import DOCXSchemaValidator

    validator = DOCXSchemaValidator(unpacked_dir, str(path), verbose=verbose)

    repairs = 0
    if auto_repair:
        repairs = validator.repair()

    success = validator.validate()

    # Collect errors if validation failed
    errors = []
    if not success and hasattr(validator, "errors"):
        errors = validator.errors

    return {
        "input": str(path),
        "success": success,
        "repairs": repairs,
        "errors": errors,
    }