"""Smoke tests for analysis checks."""

from __future__ import annotations

import unittest


class TestAnalysisChecksSmoke(unittest.TestCase):
    """Smoke tests for analysis/checks.py."""

    def test_import(self):
        """Can import checks module."""
        from sim_docs.analysis.checks import CHECK_SCHEMA, run_batch_check
        self.assertIsInstance(CHECK_SCHEMA, dict)
        self.assertTrue(callable(run_batch_check))