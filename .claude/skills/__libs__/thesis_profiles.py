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
