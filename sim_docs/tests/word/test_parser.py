"""Smoke tests for word parser."""

from __future__ import annotations

import unittest


class TestWordParserSmoke(unittest.TestCase):
    """Smoke tests for word/parser.py."""

    def test_import(self):
        """Can import word parser."""
        from sim_docs.word.parser import parse_word_document
        self.assertTrue(callable(parse_word_document))


class TestWordModelsSmoke(unittest.TestCase):
    """Smoke tests for word/models.py."""

    def test_import(self):
        """Can import word models."""
        from sim_docs.word.models import WordDocumentFacts, ParagraphFact, StyleFact, HeaderFooterFact
        self.assertTrue(WordDocumentFacts is not None)


class TestWordAdapterSmoke(unittest.TestCase):
    """Smoke tests for word/adapter.py."""

    def test_import(self):
        """Can import word adapter."""
        from sim_docs.word.adapter import WordAdapter
        self.assertTrue(WordAdapter is not None)