"""Comparison helper functions."""

from __future__ import annotations

import re


def normalized(value: str | None) -> str:
    """Remove whitespace and lowercase for comparison."""
    if value is None:
        return ""
    return re.sub(r"\s+", "", value).lower()


def values_close(expected: float, actual: float, tolerance: float = 0.5) -> bool:
    """Compare numeric values within tolerance."""
    if expected is None or actual is None:
        return False
    try:
        return abs(float(expected) - float(actual)) <= tolerance
    except (TypeError, ValueError):
        return False