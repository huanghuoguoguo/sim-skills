"""DocumentService facade - deprecated thin wrapper.

.. deprecated::
    Use `sim_docs.api` namespace instead:
        from sim_docs import api
        facts = api.word.parse("thesis.docx")
        api.analysis.check(facts, checks)

This class is preserved for backward compatibility only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sim_docs.api import word, analysis, pdf, text, spec, cache_stats, clear_cache
from sim_docs.word.models import WordDocumentFacts


class DocumentService:
    """Deprecated unified facade - use sim_docs.api instead.

    All methods delegate to the api namespace.
    """

    def __init__(self, cache_size: int = 32):
        """Initialize service. Parameter ignored - api uses shared cache."""
        pass

    def parse(self, path: str | Path) -> WordDocumentFacts:
        """Parse a Word document to structured facts."""
        return word.parse(path)

    def query_style(self, path: str | Path | WordDocumentFacts, style_name: str) -> list:
        """Query styles matching a name pattern."""
        return word.query_style(path, style_name)

    def query_text(self, path: str | Path | WordDocumentFacts, keyword: str) -> list:
        """Query paragraphs containing a keyword."""
        return word.query_text(path, keyword)

    def batch_check(self, path: str | Path | WordDocumentFacts, checks: list[dict] | dict) -> dict:
        """Compare document facts against check instructions."""
        return analysis.check(path, checks)

    def stats(self, path: str | Path | WordDocumentFacts, **kwargs) -> dict:
        """Get paragraph filtering and property distribution statistics."""
        return analysis.stats(path, **kwargs)

    def render(self, path: str | Path, page: int = 1, output: str | Path | None = None) -> bytes | str:
        """Render a specific page of a Word document to an image."""
        return word.render(path, page=page, output=output)

    def validate(self, path: str | Path, auto_repair: bool = False, verbose: bool = False) -> dict:
        """Validate Word document XML structure."""
        return word.validate(path, auto_repair=auto_repair, verbose=verbose)

    def inspect(self, path: str | Path, **kwargs) -> dict:
        """Unpack a Word document for raw XML inspection."""
        return word.inspect(path, **kwargs)

    def read_text(self, path: str | Path) -> dict:
        """Read text from .txt/.md/.docx files."""
        return text.read(path)

    def read_pdf(self, path: str | Path, pages: str | None = None,
                 include_tables: bool = False, extract_all: bool = False) -> dict:
        """Extract text, tables, and structure from PDF files."""
        return pdf.extract(path, pages=pages, include_tables=include_tables, extract_all=extract_all)

    def compare_docs(self, reference: str | Path, target: str | Path) -> dict:
        """Compare two documents for format differences."""
        return word.compare(reference, target)

    def spec_check_conflicts(self, path: str | Path) -> dict:
        """Check obvious contradictions inside spec.md."""
        return spec.check_conflicts(path)

    def spec_check_structure(self, path: str | Path, section_rules: dict[str, list[str]] | None = None) -> dict:
        """Check whether spec.md covers required sections."""
        return spec.check_structure(path, section_rules=section_rules)

    def spec_check_body_consistency(self, evidence: dict, checks: list[dict],
                                     body_section_keywords: list[str] | None = None) -> dict:
        """Compare check instructions against paragraph-stats evidence."""
        return spec.check_body_consistency(evidence, checks, body_section_keywords=body_section_keywords)

    def spec_check_common_sense(self, path: str | Path) -> dict:
        """Check font common sense violations in spec.md."""
        return spec.check_common_sense(path)

    def cache_stats(self) -> dict:
        """Get cache statistics."""
        return cache_stats()

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        clear_cache()