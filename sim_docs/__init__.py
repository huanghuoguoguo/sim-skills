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

# Validate-word scripts path (for validators)
_VALIDATE_PATH = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "validate-word" / "scripts"
if str(_VALIDATE_PATH) not in sys.path:
    sys.path.insert(0, str(_VALIDATE_PATH))

from sim_docs.service import DocumentService
from sim_docs.word.models import WordDocumentFacts, ParagraphFact, StyleFact, HeaderFooterFact

__all__ = ["DocumentService", "WordDocumentFacts", "ParagraphFact", "StyleFact", "HeaderFooterFact"]
__version__ = "0.1.0"