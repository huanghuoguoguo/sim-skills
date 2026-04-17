"""Unified document service for sim-skills.

Provides a single entry point for document parsing, querying, checking,
and rendering operations with built-in caching support.

Usage:
    from sim_docs import DocumentService

    service = DocumentService()
    facts = service.parse("thesis.docx")
    service.query_style("thesis.docx", "Heading 1")

    # Or use the namespace API:
    from sim_docs import api
    facts = api.word.parse("thesis.docx")
"""

from __future__ import annotations

from sim_docs.service import DocumentService
from sim_docs.word.models import WordDocumentFacts, ParagraphFact, StyleFact, HeaderFooterFact

__all__ = ["DocumentService", "WordDocumentFacts", "ParagraphFact", "StyleFact", "HeaderFooterFact"]
__version__ = "0.1.0"