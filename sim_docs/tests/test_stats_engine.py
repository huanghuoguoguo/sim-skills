"""Unit tests for sim_docs stats_engine module."""

from __future__ import annotations

import unittest

from sim_docs.stats_engine import compute_stats, matches_filter, filter_and_compute_stats


class TestMatchesFilter(unittest.TestCase):
    """Tests for matches_filter helper."""

    def setUp(self):
        """Create sample paragraph for testing."""
        self.sample_paragraph = {
            "text": "This is a sample paragraph with enough length.",
            "style_name": "Normal",
            "properties": {
                "font_size_pt": 12,
                "font_family_east_asia": "宋体",
                "font_family_ascii": "Times New Roman",
                "line_spacing_mode": "multiple",
                "line_spacing_value": 1.5,
                "first_line_indent_pt": 24,
                "alignment": "justify",
            },
        }

    def test_no_filters(self):
        """No filters matches any paragraph."""
        result = matches_filter(
            self.sample_paragraph,
            style_hints=(),
            exclude_texts=(),
            heading_prefixes=(),
            heading_keywords=(),
            instruction_hints=(),
            min_length=0,
            require_body_shape=False,
        )
        self.assertTrue(result)

    def test_style_hint_match(self):
        """Style hint matches normalized style name."""
        result = matches_filter(
            self.sample_paragraph,
            style_hints=("normal",),
            exclude_texts=(),
            heading_prefixes=(),
            heading_keywords=(),
            instruction_hints=(),
            min_length=0,
            require_body_shape=False,
        )
        self.assertTrue(result)

    def test_style_hint_no_match(self):
        """Style hint filters non-matching style."""
        result = matches_filter(
            self.sample_paragraph,
            style_hints=("heading",),
            exclude_texts=(),
            heading_prefixes=(),
            heading_keywords=(),
            instruction_hints=(),
            min_length=0,
            require_body_shape=False,
        )
        self.assertFalse(result)

    def test_min_length_match(self):
        """Min length filter passes long paragraphs."""
        result = matches_filter(
            self.sample_paragraph,
            style_hints=(),
            exclude_texts=(),
            heading_prefixes=(),
            heading_keywords=(),
            instruction_hints=(),
            min_length=10,
            require_body_shape=False,
        )
        self.assertTrue(result)

    def test_min_length_no_match(self):
        """Min length filter rejects short paragraphs."""
        short_paragraph = {"text": "Short", "style_name": "Normal"}
        result = matches_filter(
            short_paragraph,
            style_hints=(),
            exclude_texts=(),
            heading_prefixes=(),
            heading_keywords=(),
            instruction_hints=(),
            min_length=20,
            require_body_shape=False,
        )
        self.assertFalse(result)

    def test_require_body_shape_match(self):
        """Body shape filter passes justify with indent."""
        result = matches_filter(
            self.sample_paragraph,
            style_hints=(),
            exclude_texts=(),
            heading_prefixes=(),
            heading_keywords=(),
            instruction_hints=(),
            min_length=0,
            require_body_shape=True,
        )
        self.assertTrue(result)

    def test_require_body_shape_no_indent_no_justify(self):
        """Body shape filter rejects without indent AND without justify."""
        no_body = {
            "text": "Long enough text here",
            "style_name": "Normal",
            "properties": {
                "alignment": "left",
                "first_line_indent_pt": 0,
            },
        }
        result = matches_filter(
            no_body,
            style_hints=(),
            exclude_texts=(),
            heading_prefixes=(),
            heading_keywords=(),
            instruction_hints=(),
            min_length=0,
            require_body_shape=True,
        )
        self.assertFalse(result)

    def test_exclude_texts_filter(self):
        """Exclude texts removes paragraphs containing token."""
        result = matches_filter(
            self.sample_paragraph,
            style_hints=(),
            exclude_texts=("sample",),
            heading_prefixes=(),
            heading_keywords=(),
            instruction_hints=(),
            min_length=0,
            require_body_shape=False,
        )
        self.assertFalse(result)


class TestComputeStats(unittest.TestCase):
    """Tests for compute_stats function."""

    def test_empty_paragraphs(self):
        """Empty paragraphs returns empty summary."""
        result = compute_stats([])
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["font_size_distribution"], [])

    def test_single_paragraph(self):
        """Single paragraph creates distributions."""
        paragraphs = [
            {
                "text": "中文示例 Sample text",
                "properties": {
                    "font_size_pt": 12,
                    "font_family_east_asia": "宋体",
                    "font_family_ascii": "Times New Roman",
                    "line_spacing_mode": "multiple",
                    "line_spacing_value": 1.5,
                    "first_line_indent_pt": 24,
                },
            }
        ]
        result = compute_stats(paragraphs)
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(len(result["font_size_distribution"]), 1)
        self.assertEqual(result["font_size_distribution"][0]["value"], 12)

    def test_multiple_paragraphs_distribution(self):
        """Multiple paragraphs create sorted distributions."""
        paragraphs = [
            {"text": "Text 1", "properties": {"font_size_pt": 12}},
            {"text": "Text 2", "properties": {"font_size_pt": 12}},
            {"text": "Text 3", "properties": {"font_size_pt": 14}},
        ]
        result = compute_stats(paragraphs)
        self.assertEqual(result["candidate_count"], 3)
        # Distribution should be sorted by count descending
        self.assertEqual(result["font_size_distribution"][0]["value"], 12)
        self.assertEqual(result["font_size_distribution"][0]["count"], 2)
        self.assertEqual(result["font_size_distribution"][1]["value"], 14)
        self.assertEqual(result["font_size_distribution"][1]["count"], 1)

    def test_missing_properties(self):
        """Paragraphs with missing properties are handled."""
        paragraphs = [
            {"text": "No properties", "properties": {}},
        ]
        result = compute_stats(paragraphs)
        self.assertEqual(result["candidate_count"], 1)
        # Missing properties create empty distributions
        self.assertEqual(result["font_size_distribution"], [])

    def test_sample_limit(self):
        """Sample limit restricts number of examples."""
        paragraphs = [
            {"text": f"Paragraph {i}", "properties": {"font_size_pt": 12}}
            for i in range(10)
        ]
        result = compute_stats(paragraphs, sample_limit=3)
        # Should have at most 3 samples
        self.assertLessEqual(len(result["candidate_examples"]), 3)


class TestFilterAndComputeStats(unittest.TestCase):
    """Tests for filter_and_compute_stats function."""

    def test_empty_input(self):
        """Empty facts dict returns empty result."""
        result = filter_and_compute_stats({"paragraphs": []})
        self.assertEqual(result["summary"]["candidate_count"], 0)

    def test_with_filters(self):
        """Filters are applied before computing stats."""
        facts = {
            "paragraphs": [
                {
                    "text": "Short",
                    "style_name": "Normal",
                    "properties": {"font_size_pt": 10},
                },
                {
                    "text": "Long enough paragraph text here 中文",
                    "style_name": "Normal",
                    "properties": {
                        "font_size_pt": 12,
                        "alignment": "justify",
                        "first_line_indent_pt": 24,
                    },
                },
            ]
        }
        result = filter_and_compute_stats(
            facts,
            min_length=20,
            require_body_shape=True,
        )
        # Only second paragraph should match
        self.assertEqual(result["summary"]["candidate_count"], 1)

    def test_exclude_texts(self):
        """Exclude texts filter removes matching paragraphs."""
        facts = {
            "paragraphs": [
                {"text": "Include this", "properties": {"font_size_pt": 12}},
                {"text": "Exclude this keyword", "properties": {"font_size_pt": 14}},
            ]
        }
        result = filter_and_compute_stats(
            facts,
            exclude_texts=["keyword"],
        )
        # Only first paragraph should remain
        self.assertEqual(result["summary"]["candidate_count"], 1)


if __name__ == "__main__":
    unittest.main()