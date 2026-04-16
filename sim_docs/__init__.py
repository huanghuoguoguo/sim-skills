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

from .service import DocumentService
from .docx_parser_models import WordDocumentFacts, ParagraphFact, StyleFact

__all__ = ["DocumentService", "WordDocumentFacts", "ParagraphFact", "StyleFact"]
__version__ = "0.1.0"