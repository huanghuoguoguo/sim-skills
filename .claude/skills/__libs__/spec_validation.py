from __future__ import annotations

import glob
import json
from pathlib import Path


THESIS_COVERAGE_PROFILES = {
    "thesis-basic": {
        "required_selectors": [],  # 不再强制要求特定 selector，交给 Agent 判断
        "require_layout": False,   # 不再强制要求 layout
    }
}

ALLOWED_ALIGNMENTS = {"left", "center", "right", "justify"}
ALLOWED_SEVERITIES = {"critical", "major", "minor", "info"}
SUPPORTED_SELECTORS = {
    "body.paragraph",
    "body.heading.level1",
    "body.heading.level2",
    "body.heading.level3",
    "figure.caption",
    "table.caption",
}
SUPPORTED_PROPERTIES = {
    "font_family_zh",
    "font_family_en",
    "font_family",
    "font_family_ascii",
    "font_family_east_asia",
    "font_size_pt",
    "alignment",
    "line_spacing_pt",
    "line_spacing_mode",
    "line_spacing_value",
    "space_before_pt",
    "space_after_pt",
    "first_line_indent_pt",
    "first_line_indent_chars",
    "bold",
    "italic",
    "font_weight",
    "leader",
    "numbering_format",
    "label_bold",
    "label_font_family",
    "label_font_size_pt",
    "content_font_family",
    "content_font_size_pt",
    "indent_per_level_chars",
    "page_margin_top_cm",
    "page_margin_bottom_cm",
    "page_margin_left_cm",
    "page_margin_right_cm",
}


def resolve_path(path_str: str) -> str:
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str


def load_json_file(path_str: str) -> tuple[str, dict]:
    resolved = resolve_path(path_str)
    path = Path(resolved)
    if not path.exists():
        raise FileNotFoundError(resolved)
    return resolved, json.loads(path.read_text(encoding="utf-8"))


def validate_spec_structure(spec: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["Root element must be an object."]

    for field_name in ("spec_id", "name", "version", "rules"):
        if field_name not in spec:
            errors.append(f"Missing required top-level field: '{field_name}'.")

    rules = spec.get("rules")
    if rules is None:
        return errors
    if not isinstance(rules, list):
        return ["'rules' must be a list of rule objects."]

    seen_ids: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"Rule at index {index} must be an object.")
            continue

        rule_id = rule.get("id")
        if not rule_id:
            errors.append(f"Rule at index {index} is missing 'id'.")
        elif rule_id in seen_ids:
            errors.append(f"Duplicate rule id: '{rule_id}'.")
        else:
            seen_ids.add(rule_id)

        if not rule.get("selector"):
            errors.append(f"Rule {rule_id or index} is missing 'selector'.")

        properties = rule.get("properties")
        if properties is None:
            errors.append(f"Rule {rule_id or index} is missing 'properties'.")
            continue
        if not isinstance(properties, dict):
            errors.append(f"Rule {rule_id or index} has non-object 'properties'.")
            continue

        for property_name, value in properties.items():
            if property_name == "alignment" and value not in ALLOWED_ALIGNMENTS:
                errors.append(
                    f"Rule {rule_id or index} has invalid alignment '{value}'. "
                    f"Use one of: {sorted(ALLOWED_ALIGNMENTS)}."
                )
            if (property_name.endswith("_pt") or property_name.endswith("_cm")) and not isinstance(value, (int, float)):
                errors.append(
                    f"Rule {rule_id or index} property '{property_name}' must be numeric."
                )

        severity = rule.get("severity")
        if severity is not None and severity not in ALLOWED_SEVERITIES:
            errors.append(
                f"Rule {rule_id or index} has invalid severity '{severity}'. "
                f"Use one of: {sorted(ALLOWED_SEVERITIES)}."
            )

    return errors


def _has_page_margins(spec: dict) -> bool:
    layout = spec.get("layout")
    if isinstance(layout, dict):
        margins = layout.get("page_margins")
        if isinstance(margins, dict) and all(
            key in margins for key in ("top_cm", "bottom_cm", "left_cm", "right_cm")
        ):
            return True

    rules = spec.get("rules", [])
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        properties = rule.get("properties", {})
        if not isinstance(properties, dict):
            continue
        if all(
            key in properties
            for key in (
                "page_margin_top_cm",
                "page_margin_bottom_cm",
                "page_margin_left_cm",
                "page_margin_right_cm",
            )
        ):
            return True
    return False


def validate_spec_coverage(spec: object, profile: str = "thesis-basic") -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["Root element must be an object."]

    config = THESIS_COVERAGE_PROFILES.get(profile)
    if config is None:
        return [f"Unknown coverage profile: '{profile}'."]

    rules = spec.get("rules", [])
    if not isinstance(rules, list):
        return ["'rules' must be a list before coverage can be checked."]

    selectors = {
        rule.get("selector")
        for rule in rules
        if isinstance(rule, dict) and rule.get("selector")
    }

    for selector in config["required_selectors"]:
        if selector not in selectors:
            errors.append(f"Missing required selector for profile '{profile}': '{selector}'.")

    if config["require_layout"] and not _has_page_margins(spec):
        errors.append(
            "Missing page margin coverage. Provide either spec.layout.page_margins "
            "or a rule with page_margin_*_cm properties."
        )

    return errors


def validate_spec_consumability(spec: object, strict: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["Root element must be an object."]

    rules = spec.get("rules", [])
    if not isinstance(rules, list):
        return ["'rules' must be a list before consumability can be checked."]

    # strict=False 时只检查基本形状，不限制 selector 和 property 的具体内容
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"Rule at index {index} must be an object.")
            continue

        rule_id = rule.get("id", index)
        selector = rule.get("selector")

        if not selector:
            errors.append(f"Rule {rule_id} is missing 'selector'.")
            continue

        # 非严格模式下，只检查 selector 是否为字符串，不限制具体值
        if not isinstance(selector, str):
            errors.append(f"Rule {rule_id} has non-string 'selector'.")
            continue

        # 非严格模式下，如果 selector 不在预定义列表中，只输出警告不报错
        if strict and selector not in SUPPORTED_SELECTORS:
            errors.append(
                f"Rule {rule_id} uses unsupported selector '{selector}'. "
                f"Supported selectors: {sorted(SUPPORTED_SELECTORS)}."
            )

        properties = rule.get("properties", {})
        if not isinstance(properties, dict):
            errors.append(f"Rule {rule_id} has non-object 'properties'.")
            continue

        # 非严格模式下，不检查 property 是否在预定义列表中
        if strict:
            for property_name, value in properties.items():
                if property_name not in SUPPORTED_PROPERTIES:
                    errors.append(
                        f"Rule {rule_id} uses unsupported property '{property_name}'. "
                        "Move the explanation to spec.md instead of spec.json."
                    )
                    continue
                if isinstance(value, (dict, list)):
                    errors.append(
                        f"Rule {rule_id} property '{property_name}' must be scalar in spec.json."
                    )

    return errors


def validate_report_structure(report: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["Root element must be an object."]

    for field_name in ("issue_count", "issues"):
        if field_name not in report:
            errors.append(f"Missing required top-level field: '{field_name}'.")

    issues = report.get("issues")
    if issues is None:
        return errors
    if not isinstance(issues, list):
        return ["'issues' must be a list."]

    issue_count = report.get("issue_count")
    if isinstance(issue_count, int) and issue_count != len(issues):
        errors.append(
            f"'issue_count' ({issue_count}) does not match actual issues length ({len(issues)})."
        )

    # skipped_rules 是可选字段，用于记录被跳过的规则
    skipped_rules = report.get("skipped_rules")
    if skipped_rules is not None and not isinstance(skipped_rules, list):
        errors.append("'skipped_rules' must be a list.")

    severity_summary = report.get("issues_by_severity")
    if severity_summary is not None and isinstance(severity_summary, dict):
        expected = {"critical": 0, "major": 0, "minor": 0, "info": 0}
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            severity = issue.get("severity", "info")
            if severity in expected:
                expected[severity] += 1
        for key, value in expected.items():
            actual_value = severity_summary.get(key)
            if actual_value is not None and actual_value != value:
                errors.append(
                    f"Severity summary mismatch for '{key}': expected {value}, got {actual_value}."
                )

    for index, issue in enumerate(issues):
        if not isinstance(issue, dict):
            errors.append(f"Issue at index {index} must be an object.")
            continue
        for field_name in ("rule_id", "severity", "location", "expected", "actual", "message"):
            if field_name not in issue:
                errors.append(f"Issue at index {index} is missing '{field_name}'.")

    return errors
