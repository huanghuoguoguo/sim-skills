"""Unified document service for sim-skills.

Provides a single entry point for document parsing, querying, checking,
and rendering operations with built-in caching support.

Usage:
    from sim_docs import DocumentService

    service = DocumentService()
    facts = service.parse("thesis.docx")
    service.query_style("thesis.docx", "Heading 1")
"""

from __future__ import annotations

import sys
from pathlib import Path

# Centralized sys.path setup for utility imports
# This ensures __libs__ is available for all modules in the package
_LIBS_PATH = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "__libs__"
if str(_LIBS_PATH) not in sys.path:
    sys.path.insert(0, str(_LIBS_PATH))

# Validate-word scripts path (for validators)
_VALIDATE_PATH = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "validate-word" / "scripts"
if str(_VALIDATE_PATH) not in sys.path:
    sys.path.insert(0, str(_VALIDATE_PATH))

from .service import DocumentService
from .docx_parser_models import WordDocumentFacts, ParagraphFact, StyleFact, HeaderFooterFact

__all__ = ["DocumentService", "WordDocumentFacts", "ParagraphFact", "StyleFact", "HeaderFooterFact"]
__version__ = "0.1.0"