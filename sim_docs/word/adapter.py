"""Adapter to the existing docx_parser for Word documents."""

from __future__ import annotations

from pathlib import Path

from sim_docs.word.parser import parse_word_document
from sim_docs.word.models import WordDocumentFacts
from sim_docs.core.paths import resolve_path as _resolve_path_glob


class WordAdapter:
    """Adapter to the existing docx_parser.

    Provides a clean interface to parse Word documents without
    requiring callers to manage import paths.
    """

    SUPPORTED_EXTENSIONS = {".docx", ".dotm", ".docm"}

    @staticmethod
    def is_supported(path: str | Path) -> bool:
        """Check if file extension is supported."""
        return Path(path).suffix.lower() in WordAdapter.SUPPORTED_EXTENSIONS

    @staticmethod
    def parse(path: str | Path) -> WordDocumentFacts:
        """Parse a Word document to structured facts.

        Args:
            path: Path to .docx, .dotm, or .docm file.

        Returns:
            WordDocumentFacts with paragraphs, styles, layout, etc.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file type is not supported.
        """
        resolved_path = Path(path).expanduser().resolve()

        if not resolved_path.exists():
            raise FileNotFoundError(f"Document not found: {resolved_path}")

        if not WordAdapter.is_supported(resolved_path):
            raise ValueError(
                f"Unsupported file type: {resolved_path.suffix}. "
                f"Supported: {', '.join(WordAdapter.SUPPORTED_EXTENSIONS)}"
            )

        # Handle glob patterns (e.g., "*.docx")
        glob_matched = _resolve_path_glob(str(path))
        if glob_matched != str(path):
            resolved_path = Path(glob_matched).resolve()

        return parse_word_document(resolved_path)

    @staticmethod
    def query_style(facts: WordDocumentFacts, style_name: str) -> list:
        """Query styles matching a name pattern.

        Args:
            facts: Parsed document facts.
            style_name: Style name to match (case-insensitive, partial).

        Returns:
            List of matching StyleFact objects.
        """
        import re
        pattern = re.compile(r"\s+")
        normalized_query = pattern.sub("", style_name).lower()

        results = []
        for style in facts.styles:
            normalized_name = pattern.sub("", style.name or "").lower()
            if normalized_query in normalized_name:
                results.append(style)
        return results

    @staticmethod
    def query_text(facts: WordDocumentFacts, keyword: str) -> list:
        """Query paragraphs containing a keyword.

        Args:
            facts: Parsed document facts.
            keyword: Keyword to search in paragraph text.

        Returns:
            List of ParagraphFact objects containing the keyword.
        """
        results = []
        for para in facts.paragraphs:
            if keyword in para.text:
                results.append(para)
        return results