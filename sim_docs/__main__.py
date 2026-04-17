"""Entry point for running sim-docs as a module.

Usage:
    python -m sim_docs parse thesis.docx
    python -m sim_docs check thesis.docx checks.json
"""

from __future__ import annotations

from .cli.main import main

raise SystemExit(main())