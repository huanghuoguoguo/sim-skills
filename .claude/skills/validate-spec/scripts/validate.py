#!/usr/bin/env python3
"""Validate the completeness and schema of an extracted spec.json."""

import argparse
import glob
import json
import sys
from pathlib import Path

def resolve_path(path_str: str) -> str:
    matched = glob.glob(path_str)
    if matched:
        return matched[0]
    return path_str

def validate_schema(spec) -> list:
    errors = []
    
    if not isinstance(spec, dict):
        return ["Root element must be a dictionary."]
        
    required_top_level = ["spec_id", "name", "version", "layout", "rules"]
    for req in required_top_level:
        if req not in spec:
            errors.append(f"Missing required top-level field: '{req}'")
            
    if "layout" in spec and isinstance(spec["layout"], dict):
        layout = spec["layout"]
        if "page_margins" not in layout:
            errors.append("Missing 'page_margins' in 'layout'")
        else:
            margins = layout["page_margins"]
            if not all(k in margins for k in ["top_cm", "bottom_cm", "left_cm", "right_cm"]):
                errors.append("Incomplete 'page_margins': must have top_cm, bottom_cm, left_cm, right_cm")

    if "rules" in spec and isinstance(spec["rules"], list):
        rules = spec["rules"]
        selectors = {r.get("selector") for r in rules if "selector" in r}
        
        # Verify essential rules exist
        required_selectors = [
            "body.paragraph", 
            "body.heading.level1", 
            "body.heading.level2",
            "body.heading.level3",
            "abstract.title",
            "abstract.body",
            "toc.title",
            "toc.entry",
            "references.title",
            "references.entry"
        ]
        for req in required_selectors:
            if req not in selectors:
                errors.append(f"CRITICAL MISSING: You MUST define a rule for '{req}'.")
                
        # Basic rule structure
        for rule in rules:
            if "id" not in rule:
                errors.append("A rule is missing an 'id'.")
            if "properties" not in rule:
                errors.append(f"Rule {rule.get('id', 'Unknown')} is missing 'properties'.")
    elif "rules" in spec:
        errors.append("'rules' must be a list of rule definitions.")
        
    return errors

def main():
    parser = argparse.ArgumentParser(description="Validate JSON Spec Completeness")
    parser.add_argument("spec", help="Path to the extracted spec.json")
    args = parser.parse_args()

    spec_path = resolve_path(args.spec)
    if not Path(spec_path).exists():
        print(f"Error: File not found {spec_path}", file=sys.stderr)
        sys.exit(1)

    with open(spec_path, 'r', encoding='utf-8') as f:
        try:
            spec_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON Parsing Error: The file does not contain valid JSON.\nDetails: {e}")
            sys.exit(1)

    errors = validate_schema(spec_data)

    if errors:
        print("\n❌ VALIDATION FAILED: The spec.json schema is incomplete or incorrect!")
        print("Please fix the following missing fields or structural issues before finalizing:")
        for err in errors:
            print(f" - {err}")
        sys.exit(1)
    else:
        print("\n✅ SCHEMA VALIDATION PASSED: The spec.json contains all essential fields for a Thesis Document.")
        sys.exit(0)

if __name__ == "__main__":
    main()
