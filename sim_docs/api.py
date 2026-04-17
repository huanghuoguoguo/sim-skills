"""Namespace-based API facade for sim_docs.

Provides domain-scoped namespaces with shared caching:
- api.word: Word document parsing, querying, rendering, validation
- api.analysis: Batch checking and statistics
- api.pdf: PDF extraction
- api.text: Text file reading
- api.spec: Spec.md evaluation

Usage:
    from sim_docs import api
    facts = api.word.parse("thesis.docx")
    api.analysis.check(facts, checks)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sim_docs.core.cache import DocumentCache
from sim_docs.word.adapter import WordAdapter
from sim_docs.word.models import WordDocumentFacts
from sim_docs.word.render import render_page
from sim_docs.word.inspect import inspect_document
from sim_docs.word.compare import compare_documents
from sim_docs.word.validate import validate_document
from sim_docs.analysis.checks import run_batch_check, CHECK_SCHEMA
from sim_docs.analysis.stats import filter_and_compute_stats
from sim_docs.pdf.extract import extract_pdf
from sim_docs.text.read import read_text_source
from sim_docs.spec.engine import (
    check_conflicts,
    check_structure,
    check_body_consistency,
    check_common_sense,
)
from sim_docs.core.paths import resolve_path


_cache = DocumentCache(max_size=32)


class WordNamespace:
    """Word document operations."""

    def parse(self, path: str | Path) -> WordDocumentFacts:
        """Parse a Word document to structured facts."""
        resolved = resolve_path(str(path))
        cached = _cache.get(resolved)
        if cached is not None:
            return cached
        facts = WordAdapter.parse(resolved)
        _cache.set(resolved, facts)
        return facts

    def query_style(self, path: str | Path | WordDocumentFacts, style_name: str) -> list:
        """Query styles matching a name pattern."""
        facts = self._get_facts(path)
        return WordAdapter.query_style(facts, style_name)

    def query_text(self, path: str | Path | WordDocumentFacts, keyword: str) -> list:
        """Query paragraphs containing a keyword."""
        facts = self._get_facts(path)
        return WordAdapter.query_text(facts, keyword)

    def render(self, path: str | Path, page: int = 1, output: str | Path | None = None) -> bytes | str:
        """Render a page to PNG image."""
        resolved = resolve_path(str(path))
        return render_page(resolved, page=page, output=output)

    def inspect(self, path: str | Path, output_dir: str | None = None, show: str | None = None,
                list_files: bool = False, merge_runs: bool = True) -> dict:
        """Unpack document for XML inspection."""
        resolved = resolve_path(str(path))
        return inspect_document(resolved, output_dir=output_dir, show=show,
                                list_files=list_files, merge_runs=merge_runs)

    def compare(self, reference: str | Path, target: str | Path) -> dict:
        """Compare two documents for format differences."""
        ref_path = resolve_path(str(reference))
        target_path = resolve_path(str(target))
        ref_facts = self.parse(ref_path)
        target_facts = self.parse(target_path)
        return compare_documents(ref_facts.to_dict(), target_facts.to_dict(),
                                 ref_path=ref_path, target_path=target_path)

    def validate(self, path: str | Path, auto_repair: bool = False, verbose: bool = False) -> dict:
        """Validate Word document XML structure."""
        resolved = resolve_path(str(path))
        return validate_document(resolved, auto_repair=auto_repair, verbose=verbose)

    def _get_facts(self, path_or_facts: str | Path | WordDocumentFacts) -> WordDocumentFacts:
        """Get facts from path or use pre-parsed facts."""
        if isinstance(path_or_facts, WordDocumentFacts):
            return path_or_facts
        path = Path(path_or_facts).expanduser().resolve()
        if path.suffix.lower() == '.json':
            facts_dict = json.loads(path.read_text(encoding='utf-8'))
            return WordDocumentFacts.from_dict(facts_dict)
        return self.parse(path_or_facts)


class AnalysisNamespace:
    """Document analysis operations."""

    def check(self, path: str | Path | WordDocumentFacts | dict, checks: list[dict] | dict) -> dict:
        """Compare document facts against check instructions."""
        if isinstance(path, WordDocumentFacts):
            facts_dict = path.to_dict()
        elif isinstance(path, dict):
            facts_dict = path
        else:
            from sim_docs.api import word
            facts_dict = word.parse(path).to_dict()

        if isinstance(checks, dict) and "checks" in checks:
            checks = checks["checks"]
        return run_batch_check(facts_dict, checks)

    def stats(self, path: str | Path | WordDocumentFacts | dict,
              style_hint: str | None = None, min_length: int = 0,
              require_body_shape: bool = False, exclude_texts: list[str] | None = None,
              heading_prefixes: list[str] | None = None, heading_keywords: list[str] | None = None,
              instruction_hints: list[str] | None = None, sample_limit: int = 8) -> dict:
        """Get paragraph filtering and property distribution statistics."""
        if isinstance(path, WordDocumentFacts):
            facts_dict = path.to_dict()
        elif isinstance(path, dict):
            facts_dict = path
        else:
            from sim_docs.api import word
            facts_dict = word.parse(path).to_dict()

        style_hints = [style_hint] if style_hint else None
        return filter_and_compute_stats(
            facts_dict,
            style_hints=style_hints,
            min_length=min_length,
            require_body_shape=require_body_shape,
            exclude_texts=exclude_texts,
            heading_prefixes=heading_prefixes,
            heading_keywords=heading_keywords,
            instruction_hints=instruction_hints,
            sample_limit=sample_limit,
        )


class PdfNamespace:
    """PDF extraction operations."""

    def extract(self, path: str | Path, pages: str | None = None,
                include_tables: bool = False, extract_all: bool = False) -> dict:
        """Extract text, tables, and structure from PDF."""
        resolved = resolve_path(str(path))
        return extract_pdf(resolved, pages=pages, include_tables=include_tables,
                           extract_all_content=extract_all)


class TextNamespace:
    """Text file reading operations."""

    def read(self, path: str | Path) -> dict:
        """Read text from .txt/.md/.docx files."""
        resolved = resolve_path(str(path))
        text = read_text_source(resolved)
        return {"input": str(resolved), "text": text, "line_count": len(text.splitlines())}


class SpecNamespace:
    """Spec.md evaluation operations."""

    def check_conflicts(self, path: str | Path) -> dict:
        """Check obvious contradictions inside spec.md."""
        resolved = resolve_path(str(path))
        return check_conflicts(resolved)

    def check_structure(self, path: str | Path, section_rules: dict[str, list[str]] | None = None) -> dict:
        """Check whether spec.md covers required sections."""
        resolved = resolve_path(str(path))
        return check_structure(resolved, section_rules=section_rules)

    def check_body_consistency(self, evidence: dict, checks: list[dict],
                                body_section_keywords: list[str] | None = None) -> dict:
        """Compare check instructions against paragraph-stats evidence."""
        return check_body_consistency(checks, evidence, body_section_keywords=body_section_keywords)

    def check_common_sense(self, path: str | Path) -> dict:
        """Check font common sense violations in spec.md."""
        resolved = resolve_path(str(path))
        return check_common_sense(resolved)


word = WordNamespace()
analysis = AnalysisNamespace()
pdf = PdfNamespace()
text = TextNamespace()
spec = SpecNamespace()


def cache_stats() -> dict:
    """Get cache statistics."""
    stats = _cache.stats()
    return {"hits": stats.hits, "misses": stats.misses, "size": stats.size, "max_size": stats.max_size}


def clear_cache() -> None:
    """Clear all cached entries."""
    _cache.clear()