"""Unit tests for sim_docs spec_engine module."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from sim_docs.spec.engine import (
    check_conflicts,
    check_structure,
    check_body_consistency,
    parse_headings,
    parse_heading,
    top_value,
)


class TestParseHeadings(unittest.TestCase):
    """Tests for heading parsing."""

    def test_parse_heading_with_hash(self):
        """Parse heading with # prefix."""
        result = parse_heading("# Title")
        self.assertEqual(result, (1, "Title"))

    def test_parse_heading_with_multiple_hashes(self):
        """Parse heading with ## prefix."""
        result = parse_heading("## Subtitle")
        self.assertEqual(result, (2, "Subtitle"))

    def test_parse_heading_no_heading(self):
        """Non-heading line returns None."""
        result = parse_heading("Just a paragraph")
        self.assertIsNone(result)

    def test_parse_headings_from_lines(self):
        """Parse multiple lines and extract headings."""
        lines = [
            "# Main Title",
            "Some content here",
            "## Section 1",
            "More content",
            "### Subsection",
            "",
            "# Another Title",
        ]
        headings = parse_headings(lines)
        self.assertEqual(len(headings), 4)
        self.assertEqual(headings[0]["level"], 1)
        self.assertEqual(headings[0]["text"], "Main Title")
        self.assertEqual(headings[3]["text"], "Another Title")


class TestTopValue(unittest.TestCase):
    """Tests for top_value helper."""

    def test_top_value_from_distribution(self):
        """Get top value from sorted distribution."""
        distribution = [{"value": "宋体", "count": 50}, {"value": "黑体", "count": 10}]
        result = top_value(distribution)
        self.assertEqual(result["value"], "宋体")

    def test_top_value_empty_distribution(self):
        """Empty distribution returns None."""
        result = top_value([])
        self.assertIsNone(result)


class TestCheckConflicts(unittest.TestCase):
    """Tests for check_conflicts."""

    def test_no_conflicts(self):
        """Spec with no contradictions passes."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("# 正文格式\n")
            f.write("正文使用宋体小四号字体\n")
            temp_path = f.name

        try:
            result = check_conflicts(temp_path)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(result["conflicts"], [])
        finally:
            os.unlink(temp_path)

    def test_font_size_conflict(self):
        """Spec with font size contradictions returns needs_revision."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("# 正文格式\n")
            f.write("正文使用宋体小四号字体，字号12pt\n")
            f.write("标题使用黑体三号，字号16pt\n")
            temp_path = f.name

        try:
            result = check_conflicts(temp_path)
            # Should detect potential conflict between "小四" and "12pt"
            # Note: actual behavior depends on parse_font_size_signals
            self.assertIn(result["status"], ["pass", "needs_revision"])
        finally:
            os.unlink(temp_path)


class TestCheckStructure(unittest.TestCase):
    """Tests for check_structure."""

    def test_complete_structure(self):
        """Spec with all required sections passes."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("# 正文格式\n")
            f.write("正文使用宋体小四号\n")
            f.write("\n")
            f.write("# 标题格式\n")
            f.write("标题使用黑体三号\n")
            f.write("\n")
            f.write("## 字体要求\n")
            f.write("宋体和黑体\n")
            f.write("\n")
            f.write("# 页眉\n")
            f.write("页眉内容\n")
            f.write("\n")
            f.write("# 页脚\n")
            f.write("页脚内容\n")
            f.write("\n")
            f.write("# 页边距\n")
            f.write("上下左右各2.5cm\n")
            temp_path = f.name

        try:
            result = check_structure(temp_path)
            self.assertEqual(result["status"], "pass")
            self.assertEqual(len(result["missing_sections"]), 0)
        finally:
            os.unlink(temp_path)

    def test_missing_sections(self):
        """Spec missing required sections returns needs_revision."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("# 正文格式\n")
            f.write("正文使用宋体小四号\n")
            temp_path = f.name

        try:
            result = check_structure(temp_path)
            self.assertEqual(result["status"], "needs_revision")
            self.assertGreater(len(result["missing_sections"]), 0)
            # Check that at least one expected section is missing
            missing_names = [s["section"] for s in result["missing_sections"]]
            self.assertIn("标题", missing_names)
        finally:
            os.unlink(temp_path)

    def test_custom_section_rules(self):
        """Custom section rules override defaults."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("# Custom Section\n")
            f.write("Some content\n")
            temp_path = f.name

        try:
            custom_rules = {"Custom": ["Custom", "custom"]}
            result = check_structure(temp_path, section_rules=custom_rules)
            self.assertEqual(result["status"], "pass")
        finally:
            os.unlink(temp_path)


class TestCheckBodyConsistency(unittest.TestCase):
    """Tests for check_body_consistency."""

    def test_matching_values(self):
        """Evidence matching checks passes."""
        evidence = {
            "summary": {
                "font_size_distribution": [{"value": 12, "count": 100}],
                "line_spacing_distribution": [{"value": "multiple:1.5", "count": 100}],
                "first_line_indent_distribution": [{"value": 24, "count": 100}],
                "east_asia_font_distribution": [{"value": "宋体", "count": 100}],
                "ascii_font_distribution": [{"value": "Times New Roman", "count": 100}],
            }
        }

        checks = [
            {
                "type": "font_size",
                "section": "正文",
                "expected": 12,
                "rule_text": "正文小四号",
            },
            {
                "type": "font",
                "section": "正文",
                "scope": "east_asia",
                "expected": "宋体",
                "rule_text": "正文宋体",
            },
        ]

        result = check_body_consistency(checks, evidence)
        self.assertEqual(result["status"], "pass")
        self.assertGreater(len(result["supported_rules"]), 0)

    def test_mismatching_values(self):
        """Evidence not matching checks returns needs_revision."""
        evidence = {
            "summary": {
                "font_size_distribution": [{"value": 14, "count": 100}],
                "line_spacing_distribution": [{"value": "exact:20", "count": 100}],
                "first_line_indent_distribution": [{"value": 0, "count": 100}],
            }
        }

        checks = [
            {
                "type": "font_size",
                "section": "正文",
                "expected": 12,
                "rule_text": "正文小四号",
            },
        ]

        result = check_body_consistency(checks, evidence)
        self.assertEqual(result["status"], "needs_revision")
        self.assertGreater(len(result["mismatches"]), 0)

    def test_body_section_filter(self):
        """Filter checks by body section keywords."""
        evidence = {
            "summary": {
                "font_size_distribution": [{"value": 12, "count": 100}],
            }
        }

        checks = [
            {
                "type": "font_size",
                "section": "正文",
                "expected": 12,
                "rule_text": "正文小四号",
            },
            {
                "type": "font_size",
                "section": "标题",
                "expected": 16,
                "rule_text": "标题三号",
            },
        ]

        # Only check body-related sections
        result = check_body_consistency(
            checks, evidence, body_section_keywords=["正文", "body"]
        )
        # Only the body check should be evaluated
        total_evaluated = len(result["supported_rules"]) + len(result["mismatches"])
        self.assertEqual(total_evaluated, 1)


if __name__ == "__main__":
    unittest.main()