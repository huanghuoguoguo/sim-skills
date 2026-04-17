"""DocumentService facade for unified document operations.

Provides a single entry point for parsing, querying, checking, and
rendering documents with built-in caching support.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from sim_docs.core.cache import DocumentCache
from sim_docs.word.adapter import WordAdapter, WordDocumentFacts
from sim_docs.analysis.checks import run_batch_check as _run_batch_check_engine, CHECK_SCHEMA
from sim_docs.analysis.stats import filter_and_compute_stats
from sim_docs.pdf.extract import extract_pdf
from sim_docs.word.inspect import inspect_document
from sim_docs.word.compare import compare_documents, generate_diff_report
from sim_docs.word.validate import validate_document
from sim_docs.spec.engine import check_conflicts, check_structure, check_body_consistency, check_common_sense

from sim_docs.core.helpers import normalized, values_close
from sim_docs.core.paths import resolve_path as _resolve_path_glob


class DocumentService:
    """Unified facade for document operations with caching.

    Usage:
        service = DocumentService()
        facts = service.parse("thesis.docx")
        service.query_style("thesis.docx", "Heading 1")
        service.batch_check("thesis.docx", checks)
    """

    def __init__(self, cache_size: int = 32):
        """Initialize service with cache.

        Args:
            cache_size: Maximum number of documents to cache.
        """
        self._cache = DocumentCache(max_size=cache_size)

    # -------------------------------------------------------------------------
    # Core operations
    # -------------------------------------------------------------------------

    def parse(self, path: str | Path) -> WordDocumentFacts:
        """Parse a Word document to structured facts.

        Uses cache to avoid redundant parsing.

        Args:
            path: Path to .docx, .dotm, or .docm file.

        Returns:
            WordDocumentFacts with paragraphs, styles, layout, etc.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file type is not supported.
        """
        resolved = self._resolve_path(path)
        cached = self._cache.get(resolved)
        if cached is not None:
            return cached

        facts = WordAdapter.parse(resolved)
        self._cache.set(resolved, facts)
        return facts

    def query_style(
        self,
        path: str | Path | WordDocumentFacts,
        style_name: str,
    ) -> list:
        """Query styles matching a name pattern.

        Args:
            path: Path to document or pre-parsed facts.
            style_name: Style name to match (case-insensitive, partial).

        Returns:
            List of matching StyleFact objects.
        """
        facts = self._get_facts(path)
        return WordAdapter.query_style(facts, style_name)

    def query_text(
        self,
        path: str | Path | WordDocumentFacts,
        keyword: str,
    ) -> list:
        """Query paragraphs containing a keyword.

        Args:
            path: Path to document or pre-parsed facts.
            keyword: Keyword to search in paragraph text.

        Returns:
            List of ParagraphFact objects containing the keyword.
        """
        facts = self._get_facts(path)
        return WordAdapter.query_text(facts, keyword)

    # -------------------------------------------------------------------------
    # Batch check
    # -------------------------------------------------------------------------

    def batch_check(
        self,
        path: str | Path | WordDocumentFacts,
        checks: list[dict] | dict,
    ) -> dict:
        """Compare document facts against check instructions.

        Args:
            path: Path to document or pre-parsed facts.
            checks: List of check instructions or dict with "checks" key.

        Returns:
            Result dict with summary, results, and issues.
        """
        facts = self._get_facts(path)
        facts_dict = facts.to_dict() if hasattr(facts, "to_dict") else facts

        if isinstance(checks, dict) and "checks" in checks:
            checks = checks["checks"]

        return self._run_batch_check(facts_dict, checks)

    def _run_batch_check(self, facts: dict, checks: list[dict]) -> dict:
        """Execute batch check logic using check_engine."""
        return _run_batch_check_engine(facts, checks)

    # -------------------------------------------------------------------------
    # Stats
    # -------------------------------------------------------------------------

    def stats(
        self,
        path: str | Path | WordDocumentFacts,
        style_hint: str | None = None,
        min_length: int = 0,
        require_body_shape: bool = False,
        exclude_texts: list[str] | None = None,
        heading_prefixes: list[str] | None = None,
        heading_keywords: list[str] | None = None,
        instruction_hints: list[str] | None = None,
        sample_limit: int = 8,
    ) -> dict:
        """Get paragraph filtering and property distribution statistics.

        Uses stats_engine for computation.

        Args:
            path: Path to document or pre-parsed facts.
            style_hint: Style name to filter (normalized).
            min_length: Minimum paragraph text length.
            require_body_shape: Only paragraphs with justify/indent.
            exclude_texts: Exclude paragraphs containing these texts.
            heading_prefixes: Regex patterns for heading exclusion.
            heading_keywords: Keyword prefixes for heading exclusion.
            instruction_hints: Text hints for instruction exclusion.
            sample_limit: Max candidate examples.

        Returns:
            Stats dict with filters, summary, and distributions.
        """
        facts = self._get_facts(path)
        facts_dict = facts.to_dict() if hasattr(facts, "to_dict") else facts

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

    # -------------------------------------------------------------------------
    # Render
    # -------------------------------------------------------------------------

    def render(
        self,
        path: str | Path,
        page: int = 1,
        output: str | Path | None = None,
    ) -> bytes | str:
        """Render a specific page of a Word document to an image.

        Args:
            path: Path to .docx or .dotm file.
            page: Page number (1-indexed).
            output: Output image path. If None, returns bytes.

        Returns:
            PNG bytes if output is None, otherwise output path.
        """
        from sim_docs.word.render import render_page
        resolved = self._resolve_path(path)
        return render_page(resolved, page=page, output=output)

    # -------------------------------------------------------------------------
    # Validate
    # -------------------------------------------------------------------------

    def validate(
        self,
        path: str | Path,
        auto_repair: bool = False,
        verbose: bool = False,
    ) -> dict:
        """Validate Word document XML structure against OOXML schemas.

        Uses validate_engine for validation.

        Args:
            path: Path to .docx file.
            auto_repair: Automatically repair common issues.
            verbose: Enable verbose output.

        Returns:
            Validation result dict with success status and details.
        """
        resolved = self._resolve_path(path)
        return validate_document(resolved, auto_repair=auto_repair, verbose=verbose)

    # -------------------------------------------------------------------------
    # Inspect
    # -------------------------------------------------------------------------

    def inspect(
        self,
        path: str | Path,
        output_dir: str | None = None,
        show: str | None = None,
        list_files: bool = False,
        merge_runs: bool = True,
    ) -> dict:
        """Unpack a Word document for raw XML inspection.

        Uses inspect_engine for unpacking.

        Args:
            path: Path to .docx or .dotm file.
            output_dir: Output directory for unpacked files.
            show: Show content of a specific XML file.
            list_files: List all XML files in the document.
            merge_runs: Merge adjacent runs with identical formatting.

        Returns:
            Dict with message, output_dir, and optionally file list/content.
        """
        resolved = self._resolve_path(path)
        return inspect_document(
            resolved,
            output_dir=output_dir,
            show=show,
            list_files=list_files,
            merge_runs=merge_runs,
        )

    # -------------------------------------------------------------------------
    # Read text
    # -------------------------------------------------------------------------

    def read_text(self, path: str | Path) -> dict:
        """Read text from .txt/.md/.docx files.

        Args:
            path: Path to text file or Word document.

        Returns:
            Dict with input, text, and line_count.
        """
        resolved = self._resolve_path(path)

        from .text_sources import read_text_source

        text = read_text_source(resolved)
        return {
            "input": str(resolved),
            "text": text,
            "line_count": len(text.splitlines()),
        }

    # -------------------------------------------------------------------------
    # Read PDF
    # -------------------------------------------------------------------------

    def read_pdf(
        self,
        path: str | Path,
        pages: str | None = None,
        include_tables: bool = False,
        extract_all: bool = False,
    ) -> dict:
        """Extract text, tables, and structure from PDF files.

        Uses pdf_engine for extraction.

        Args:
            path: Path to PDF file.
            pages: Page range (e.g., "1-5", "1,3,5").
            include_tables: Extract tables only.
            extract_all: Full extraction (text + tables).

        Returns:
            Dict with pages, full_text, and optionally tables.
        """
        resolved = self._resolve_path(path)
        return extract_pdf(
            resolved,
            pages=pages,
            include_tables=include_tables,
            extract_all_content=extract_all,
        )

    # -------------------------------------------------------------------------
    # Compare docs
    # -------------------------------------------------------------------------

    def compare_docs(
        self,
        reference: str | Path,
        target: str | Path,
    ) -> dict:
        """Compare two documents for format differences.

        Uses compare_engine for comparison.

        Args:
            reference: Path to reference .docx file.
            target: Path to target .docx file.

        Returns:
            Dict with diff_count and diffs list.
        """
        ref_path = self._resolve_path(reference)
        target_path = self._resolve_path(target)

        ref_facts = WordAdapter.parse(ref_path)
        target_facts = WordAdapter.parse(target_path)

        return compare_documents(
            ref_facts.to_dict(),
            target_facts.to_dict(),
            ref_path=ref_path,
            target_path=target_path,
        )

    # -------------------------------------------------------------------------
    # Spec check
    # -------------------------------------------------------------------------

    def spec_check_conflicts(self, path: str | Path) -> dict:
        """Check obvious contradictions inside spec.md.

        Args:
            path: Path to spec.md file.

        Returns:
            Dict with spec_path, status, conflicts, and summary.
        """
        resolved = self._resolve_path(path)
        return check_conflicts(resolved)

    def spec_check_structure(
        self,
        path: str | Path,
        section_rules: dict[str, list[str]] | None = None,
    ) -> dict:
        """Check whether spec.md covers required sections.

        Args:
            path: Path to spec.md file.
            section_rules: Dict mapping section names to keyword lists.

        Returns:
            Dict with spec_path, status, covered_sections, missing_sections.
        """
        resolved = self._resolve_path(path)
        return check_structure(resolved, section_rules=section_rules)

    def spec_check_body_consistency(
        self,
        evidence: dict,
        checks: list[dict],
        body_section_keywords: list[str] | None = None,
    ) -> dict:
        """Compare check instructions against paragraph-stats evidence.

        Args:
            evidence: paragraph-stats output dict with "summary" key.
            checks: List of check instruction dicts.
            body_section_keywords: Only compare checks whose section contains
                one of these keywords.

        Returns:
            Dict with status, body_evidence_summary, supported_rules, mismatches.
        """
        return check_body_consistency(
            checks,
            evidence,
            body_section_keywords=body_section_keywords,
        )

    def spec_check_common_sense(self, path: str | Path) -> dict:
        """Check font common sense violations in spec.md.

        Detects when Chinese fonts are incorrectly specified as Western fonts.

        Args:
            path: Path to spec.md file.

        Returns:
            Dict with spec_path, status, conflicts, and summary.
        """
        resolved = self._resolve_path(path)
        return check_common_sense(resolved)

    # -------------------------------------------------------------------------
    # Cache management
    # -------------------------------------------------------------------------

    def cache_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with hits, misses, size, and max_size.
        """
        stats = self._cache.stats()
        return {
            "hits": stats.hits,
            "misses": stats.misses,
            "size": stats.size,
            "max_size": stats.max_size,
        }

    def clear_cache(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _resolve_path(self, path: str | Path) -> str:
        """Resolve path, supporting glob patterns and ~ expansion."""
        p = Path(path).expanduser().resolve()
        # Try glob matching
        glob_matched = _resolve_path_glob(str(path))
        if glob_matched != str(path):
            return glob_matched
        return str(p)

    def _get_facts(self, path_or_facts: str | Path | WordDocumentFacts) -> WordDocumentFacts:
        """Get facts from path or use pre-parsed facts.

        Supports:
        - WordDocumentFacts object (returned directly)
        - .docx/.dotm/.docm files (parsed)
        - .json files (loaded as pre-parsed facts)
        """
        if isinstance(path_or_facts, WordDocumentFacts):
            return path_or_facts

        path = Path(path_or_facts).expanduser().resolve()

        # Support loading pre-parsed facts from JSON
        if path.suffix.lower() == '.json':
            import json
            facts_dict = json.loads(path.read_text(encoding='utf-8'))
            return WordDocumentFacts.from_dict(facts_dict)

        return self.parse(path_or_facts)