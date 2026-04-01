#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


legacy_dir = Path(__file__).resolve().parents[2] / "word" / "scripts"
if str(legacy_dir) not in sys.path:
    sys.path.insert(0, str(legacy_dir))

from query_text import main


if __name__ == "__main__":
    raise SystemExit(main())
