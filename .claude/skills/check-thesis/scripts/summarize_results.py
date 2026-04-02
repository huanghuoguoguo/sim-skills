#!/usr/bin/env python3
"""Summarize raw thesis check results into compact grouped diagnostics."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import sys

libs_dir = Path(__file__).resolve().parents[2] / "__libs__"
if str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))

from utils import write_json_output


def format_location(location: dict) -> str:
    if not location:
        return "未定位"
    if "paragraph_index" in location:
        style_name = location.get("style_name")
        prefix = f"段落 #{location['paragraph_index']}"
        if style_name:
            prefix += f"（{style_name}）"
        preview = (location.get("text_preview") or "").strip()
        if preview:
            return f"{prefix}: {preview}"
        return prefix
    if location.get("scope") == "document.layout":
        side = location.get("side")
        if side:
            return f"页面设置/{side}"
        return "页面设置"
    selector = location.get("selector")
    if selector:
        return selector
    return "未定位"


def _stringify_actual(value) -> str:
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def summarize_deterministic_results(batch_result: dict, sample_limit: int = 5) -> list[dict]:
    grouped = []
    for result in batch_result.get("results", []):
        if result["status"] not in {"fail", "unresolved"}:
            continue

        issues = result.get("issues", [])
        location_examples = []
        actual_counter: Counter[str] = Counter()
        message_counter: Counter[str] = Counter()
        for issue in issues:
            message_counter[issue.get("message", "不符合要求")] += 1
            actual = issue.get("actual")
            if actual is not None:
                actual_counter[_stringify_actual(actual)] += 1
            if len(location_examples) < sample_limit:
                location_examples.append(format_location(issue.get("location", {})))

        grouped.append(
            {
                "id": result.get("id"),
                "section": result.get("section"),
                "rule_text": result.get("rule_text"),
                "type": result.get("type"),
                "selector": result.get("selector"),
                "status": result.get("status"),
                "expected": result.get("expected"),
                "actual_summary": [value for value, _ in actual_counter.most_common(3)],
                "issue_summary": [
                    {"message": message, "count": count}
                    for message, count in message_counter.most_common()
                ],
                "matched_count": result.get("matched_count"),
                "issue_count": len(issues),
                "location_examples": location_examples,
            }
        )
    return grouped


def build_agent_payload(
    thesis_path: str,
    spec_path: str,
    spec_title: str,
    translation_summary: dict,
    summary: dict,
    grouped_failures: list[dict],
    semantic_results: list[dict],
    manual_results: list[dict],
) -> dict:
    return {
        "thesis": thesis_path,
        "spec_path": spec_path,
        "spec_title": spec_title,
        "summary": summary,
        "translation_summary": translation_summary,
        "deterministic_failures": grouped_failures,
        "semantic_queue": semantic_results,
        "manual_queue": manual_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize raw thesis check results")
    parser.add_argument("batch_result", help="Path to batch_result JSON")
    parser.add_argument("--output", help="Where to write summarized JSON")
    parser.add_argument("--sample-limit", type=int, default=5, help="Maximum location examples per failed rule")
    args = parser.parse_args()

    batch_result = json.loads(Path(args.batch_result).read_text(encoding="utf-8"))
    payload = {
        "grouped_failures": summarize_deterministic_results(batch_result, sample_limit=args.sample_limit),
    }
    write_json_output(payload, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
