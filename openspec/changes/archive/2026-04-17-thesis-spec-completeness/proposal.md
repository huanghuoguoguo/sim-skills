## Why

Current `extract-spec` skill only extracts ~40% of thesis format elements (页面设置, 正文, 标题 1-4). Missing: 关键词, 摘要细节, 图表Caption, 参考文献, 页眉页脚, 附录, 致谢. This happens because there's no "contract" defining what a thesis spec must contain—the profile only provides sampling hints, SKILL.md hardcodes only 3 subagents.

Users cannot verify if extraction is complete, and downstream `check-thesis` lacks rules for many sections.

## What Changes

- **thesis_profiles.py**: Add `spec_schema` defining required/optional sections and their extractors
- **extract-spec/SKILL.md**: Dynamic subagent dispatch based on profile schema (read sections → dispatch extractor)
- **evaluate-spec/SKILL.md**: Validate completeness against profile schema (all required sections present)
- **7 new subagent prompts**: caption-extractor, reference-extractor, keyword-extractor, abstract-extractor, header-footer-extractor, toc-extractor, cover-extractor
- **spec_engine.py**: `check_structure()` accepts section rules from profile schema
- **heading-extractor**: Extend to extract Heading 5-9 (currently only 1-4)

## Capabilities

### New Capabilities

- `spec-schema-profile`: Profile-based schema defining what thesis specs must contain (required sections, extractors, validation rules)
- `caption-extractor-subagent`: Extract figure/table caption format from style definition + text instructions
- `reference-extractor-subagent`: Extract reference section format (font, line spacing, citation style) from text instructions
- `keyword-extractor-subagent`: Extract keyword format (label vs content formatting) from text instructions
- `abstract-extractor-subagent`: Extract abstract format (title, body, word count requirements)
- `header-footer-extractor-subagent`: Extract header/footer format including page numbering across sections (Roman/Arabic)
- `toc-extractor-subagent`: Extract TOC format and structure

### Modified Capabilities

- `font-extractor-subagent`: Extend to handle Caption style in addition to Normal
- `heading-extractor-subagent`: Extend to extract Heading 5-9 levels (profile defines which levels)
- `spec-evaluator-subagent`: Validate completeness against profile spec_schema

## Impact

- **thesis_profiles.py**: Major expansion—add `spec_schema` dict with all section definitions
- **extract-spec/SKILL.md**: Step 2 rewritten—dynamic dispatch loop reading from profile
- **evaluate-spec/SKILL.md**: Step 1 rewritten—check_structure uses profile schema
- **spec_engine.py**: `check_structure()` parameter `section_rules` now comes from profile
- **New files**: 7 `-prompt.md` files in `.claude/skills/extract-spec/`
- **Backward compatible**: Schools can override profile; default profile covers standard thesis structure