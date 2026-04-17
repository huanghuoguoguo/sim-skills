## Context

Current architecture:
- `thesis_profiles.py`: Provides sampling hints for extraction, section keywords for evaluation
- `extract-spec/SKILL.md`: Hardcoded 3 subagents (font, layout, heading)
- `spec_engine.py`: `check_structure()` uses hardcoded section rules
- Subagent outputs: `status`, `output`, `cross_validation`, `tool_errors`, `common_sense_check`

Problem: No contract defines what a thesis spec must contain. Profile hints ≠ extraction contract.

Constraint: Subagent architecture must remain (main Agent dispatches + evaluates, subagents execute).

## Goals / Non-Goals

**Goals:**
- Define contract for thesis spec completeness via profile `spec_schema`
- Dynamic subagent dispatch based on profile
- Completeness validation in evaluate-spec
- Support school-specific profile overrides

**Non-Goals:**
- New schema file format (use existing Python dict in profile)
- Auto-detecting school from template filename
- Extracting every possible element (focus on standard thesis structure)

## Decisions

### D1: Profile as Schema Contract (not separate file)

**Decision:** Extend `thesis_profiles.py` with `spec_schema` dict, not create a new YAML schema file.

**Alternatives considered:**
1. New `thesis-spec-schema.yaml`: More formal, but requires new parser, adds complexity
2. Inline in SKILL.md: Not school-specific, hard to override
3. Python dict in profile: Existing mechanism, easy override, no new infra

**Rationale:** Profile mechanism already exists, schools can override by providing JSON. Python dict is easier to work with than YAML parsing.

### D2: Extractor Naming Convention

**Decision:** Extractors named by section: `{section}-extractor`. Profile maps section → extractor.

```python
"sections": {
    "关键词": {"extractor": "keyword"},
    "参考文献": {"extractor": "reference"},
    ...
}
```

SKILL.md dispatches `{extractor}-extractor` subagent.

**Rationale:** Clear mapping, easy to add new sections by adding to profile + creating prompt file.

### D3: Required vs Optional Sections

**Decision:** Profile defines `required: true/false` per section. evaluate-spec validates required sections only.

```python
"摘要": {"required": True, "extractor": "abstract"},
"附录": {"required": False, "extractor": "appendix"},
```

**Rationale:** Standard thesis structure has common elements; optional sections (附录, 致谢) vary by school.

### D4: Subagent Reuse for Caption

**Decision:** Extend `font-extractor` to handle Caption style, not create separate `caption-font-extractor`.

**Alternatives considered:**
1. New `caption-font-extractor`: Duplicates font logic
2. `caption-extractor` handles font + numbering: Mixing concerns
3. `font-extractor` with `target_styles` parameter: Reuse existing logic

**Rationale:** Font extraction logic is identical; only style differs. font-extractor already has cross-validation + common-sense check.

### D5: Text Instruction Extractors

**Decision:** Some extractors (keyword, reference, abstract) primarily read text instructions, not styles.

**Pattern:**
- `keyword-extractor`: Search `query-text --keyword "关键词"` for format rules
- `reference-extractor`: Search `query-text --keyword "参考文献"` for citation style
- `abstract-extractor`: Search for "摘要" + "字数" requirements

**Rationale:** Template text describes these sections' formats explicitly. Styles may not exist or be inconsistent.

### D6: Header/Footer from Sections

**Decision:** `header-footer-extractor` analyzes section breaks for page numbering.

**Pattern:**
- Parse facts.json `section_count` and `headers[]/footers[]` arrays
- Detect Roman vs Arabic page numbering from footer text patterns (`- ii -` vs `- 1 -`)
- Report which sections use which format

**Rationale:** Page numbering varies by section (前置部分 Roman, 正文部分 Arabic). Must analyze all sections.

## Risks / Trade-offs

### Risk: Template lacks text instructions for some sections
→ **Mitigation:** Extractor returns `NEEDS_CONTEXT` with `text_instructions: {"found": false}`. Main Agent asks user.

### Risk: Style defined but no example paragraphs (Heading 5-9)
→ **Mitigation:** Extractor returns `source: "style_definition_only"` with `conflict_note`. Mark as "未验证".

### Risk: Profile too rigid for non-standard thesis types
→ **Mitigation:** Schools override profile JSON. Optional sections can be toggled.

### Trade-off: More subagents = more complexity
→ **Accept:** Necessary for completeness. Each subagent is focused, follows standard output format.

## Open Questions

1. **School profile loading mechanism?**
   - Option A: CLI `--profile school-tjut.json`
   - Option B: Auto-detect from template filename regex
   - Option C: Manual per invocation
   
   **Recommendation:** Option A (explicit) for now, B can be added later.

2. **Heading levels: hardcoded or configurable?**
   - Current: heading-extractor handles 1-4
   - Proposal: profile defines `levels: [1,2,3,4,5,6]`
   
   **Recommendation:** Configurable via profile. Default includes 1-4, schools can extend.