#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


shared_word_scripts = Path(__file__).resolve().parents[2] / "word" / "scripts"
if str(shared_word_scripts) not in sys.path:
    sys.path.insert(0, str(shared_word_scripts))

from render_page import main


if __name__ == "__main__":
    raise SystemExit(main())
