"""Smoke tests for CLI main."""

from __future__ import annotations

import unittest


class TestCLIMainSmoke(unittest.TestCase):
    """Smoke tests for cli/main.py."""

    def test_import(self):
        """Can import CLI main."""
        from sim_docs.cli.main import main, COMMANDS
        self.assertTrue(callable(main))
        self.assertIsInstance(COMMANDS, list)
        self.assertTrue(len(COMMANDS) > 0)

    def test_commands_have_required_fields(self):
        """Each command has NAME, HELP, add_parser, run."""
        from sim_docs.cli.main import COMMANDS
        for name, help_text, add_parser, run in COMMANDS:
            self.assertIsInstance(name, str)
            self.assertIsInstance(help_text, str)
            self.assertTrue(callable(add_parser))
            self.assertTrue(callable(run))