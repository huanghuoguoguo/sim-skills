"""Default thesis profiles plus helpers for runtime overrides."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


DEFAULT_THESIS_PROFILE = {
    # New: Spec schema defining what thesis specs must contain
    "spec_schema": {
        "sections": {
            "页面设置": {
                "required": True,
                "extractor": "layout",
                "properties": ["paper_size", "margins", "header_distance", "footer_distance"],
            },
            "正文": {
                "required": True,
                "extractor": "font",
                "target_styles": ["Normal"],
                "validation": "cross_source",
                "properties": [
                    "east_asia_font",
                    "ascii_font",
                    "font_size",
                    "line_spacing",
                    "alignment",
                    "first_line_indent",
                ],
            },
            "标题": {
                "required": True,
                "extractor": "heading",
                "levels": [1, 2, 3, 4],  # Configurable per school
                "validation": "cross_source",
                "properties": ["font", "font_size", "line_spacing", "alignment", "space_before", "space_after"],
            },
            "摘要": {
                "required": True,
                "extractor": "abstract",
                "properties": ["title_format", "body_format", "word_count"],
            },
            "关键词": {
                "required": True,
                "extractor": "keyword",
                "properties": ["label_format", "content_format", "count_requirement"],
            },
            "图表Caption": {
                "required": True,
                "extractor": "caption",
                "target_styles": ["Caption"],
                "properties": ["figure_caption", "table_caption", "numbering_style"],
            },
            "参考文献": {
                "required": True,
                "extractor": "reference",
                "properties": ["font", "font_size", "line_spacing", "citation_style"],
            },
            "页眉页脚": {
                "required": True,
                "extractor": "header_footer",
                "properties": ["header_format", "footer_format", "page_numbering"],
            },
            "目录": {
                "required": True,
                "extractor": "toc",
                "properties": ["toc_format", "heading_levels_included"],
            },
            # Optional sections
            "封面": {
                "required": False,
                "extractor": "cover",
                "properties": ["title_page_layout"],
            },
            "附录": {
                "required": False,
                "extractor": "appendix",
                "properties": ["appendix_format", "appendix_numbering"],
            },
            "致谢": {
                "required": False,
                "extractor": "acknowledgment",
                "properties": ["acknowledgment_format"],
            },
        },
    },
    # Existing: evaluate_spec hints
    "evaluate_spec": {
        "section_rules": {
            "页面设置": ["页面设置"],
            "正文": ["正文"],
            "标题": ["标题"],
            "摘要": ["摘要"],
            "图表": ["图", "表"],
            "参考文献": ["参考文献"],
        },
        "body_section_keywords": ["正文"],
    },
    # Existing: extract_spec hints
    "extract_spec": {
        "body_sampling": {
            "body_style_hints": ["normal", "body text", "body text indent", "body", "normal indent"],
            "heading_prefix_patterns": [r"^第.+章"],
            "heading_keywords": ["附录", "摘要", "目录", "参考文献", "致谢"],
            "instruction_hints": ["打印", "适用于", "选填"],
        }
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def load_profile(profile_json: str | None = None, overrides: dict | None = None) -> dict:
    profile = deepcopy(DEFAULT_THESIS_PROFILE)
    if profile_json:
        loaded = json.loads(Path(profile_json).read_text(encoding="utf-8"))
        profile = _deep_merge(profile, loaded)
    if overrides:
        profile = _deep_merge(profile, overrides)
    return profile


def get_required_sections(profile: dict) -> list[str]:
    """Extract required section names from profile spec_schema."""
    sections = profile.get("spec_schema", {}).get("sections", {})
    return [name for name, config in sections.items() if config.get("required", False)]


def get_section_config(profile: dict, section_name: str) -> dict | None:
    """Get configuration for a specific section from profile spec_schema."""
    return profile.get("spec_schema", {}).get("sections", {}).get(section_name)


def get_section_rules_for_structure_check(profile: dict) -> dict[str, list[str]]:
    """Build section_rules dict for spec_engine.check_structure() from profile."""
    # Use evaluate_spec.section_rules if available, else build from spec_schema
    if "section_rules" in profile.get("evaluate_spec", {}):
        return profile["evaluate_spec"]["section_rules"]

    # Build from spec_schema required sections
    sections = profile.get("spec_schema", {}).get("sections", {})
    return {
        name: [name]  # Simple keyword matching
        for name, config in sections.items()
        if config.get("required", False)
    }