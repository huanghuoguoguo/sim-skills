"""Default thesis profiles plus helpers for runtime overrides."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


DEFAULT_THESIS_PROFILE = {
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
    "extract_spec": {
        "body_sampling": {
            "body_style_hints": ["normal", "body text", "body text indent", "body", "normal indent"],
            "heading_prefix_patterns": [r"^第.+章"],
            "heading_keywords": ["附录", "摘要", "目录", "参考文献", "致谢"],
            "instruction_hints": ["打印", "适用于", "选填"],
        }
    },
    "check_thesis": {
        "translate_spec": {
            "ignored_heading_keywords": ["来源"],
            "manual_heading_keywords": ["待确认项"],
            "semantic_section_keywords": ["摘要", "参考文献", "目录"],
            "layout_section_keywords": ["页面设置"],
            "figure_caption_heading_keywords": ["图题"],
            "table_caption_heading_keywords": ["表题"],
            "body_section_keywords": ["正文"],
            "figure_caption_prefix_patterns": [r"^图\s*[0-9一二三四五六七八九十]"],
            "table_caption_prefix_patterns": [r"^表\s*[0-9一二三四五六七八九十]"],
            "body_selector": {
                "selector": "style:Normal",
                "style_name": "Normal",
                "style_aliases": ["Normal", "正文", "Body Text", "Body"],
            },
            "caption_style": {
                "style_name": "Caption",
                "figure_aliases": ["Caption", "题注", "图题"],
                "table_aliases": ["Caption", "题注", "表题"],
            },
            "title_style_map": {
                "一级标题": {"style_name": "Heading 1", "style_aliases": ["Heading 1", "标题1", "一级标题", "1级标题"]},
                "二级标题": {"style_name": "Heading 2", "style_aliases": ["Heading 2", "标题2", "二级标题", "2级标题"]},
                "三级标题": {"style_name": "Heading 3", "style_aliases": ["Heading 3", "标题3", "三级标题", "3级标题"]},
                "四级标题": {"style_name": "Heading 4", "style_aliases": ["Heading 4", "标题4", "四级标题", "4级标题"]},
                "五级标题": {"style_name": "Heading 5", "style_aliases": ["Heading 5", "标题5", "五级标题", "5级标题"]},
                "六级标题": {"style_name": "Heading 6", "style_aliases": ["Heading 6", "标题6", "六级标题", "6级标题"]},
            },
            "default_title_style": {
                "style_name": "Heading 1",
                "style_aliases": ["Heading 1", "标题1", "一级标题"],
            },
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
