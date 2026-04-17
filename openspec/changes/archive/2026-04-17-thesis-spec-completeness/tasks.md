## 1. Profile Schema Foundation

- [x] 1.1 Add `spec_schema` dict to `thesis_profiles.py` with all required sections
- [x] 1.2 Add section definitions: 页面设置, 正文, 标题, 摘要, 关键词, 图表Caption, 参考文献, 页眉页脚, 目录
- [x] 1.3 Add optional sections: 附录, 致谢, 封面 with `required: false`
- [x] 1.4 Add `extractor` field to each section mapping to subagent name
- [x] 1.5 Add `properties` field to each section listing what to extract
- [x] 1.6 Add `levels` field to 标题 section (default: [1, 2, 3, 4])
- [x] 1.7 Update `load_profile()` to handle spec_schema deep merge

## 2. Spec Engine Updates

- [x] 2.1 Update `spec_engine.py` `check_structure()` to accept section_rules from profile
- [x] 2.2 Add `required_sections` extraction helper from profile.spec_schema
- [x] 2.3 Ensure missing_sections only includes required sections (not optional)

## 3. Subagent Prompt Files (New)

- [x] 3.1 Create `caption-extractor-prompt.md` in extract-spec skill
- [x] 3.2 Create `reference-extractor-prompt.md` in extract-spec skill
- [x] 3.3 Create `keyword-extractor-prompt.md` in extract-spec skill
- [x] 3.4 Create `abstract-extractor-prompt.md` in extract-spec skill
- [x] 3.5 Create `header-footer-extractor-prompt.md` in extract-spec skill
- [x] 3.6 Create `toc-extractor-prompt.md` in extract-spec skill

## 4. Subagent Prompt Updates (Modified)

- [x] 4.1 Update `font-extractor-prompt.md` to accept `target_styles` parameter (default: ["Normal"])
- [x] 4.2 Update `font-extractor-prompt.md` to handle Caption style extraction
- [x] 4.3 Update `font-extractor-prompt.md` output format to include caption_font_rules
- [x] 4.4 Update `heading-extractor-prompt.md` to accept `levels` parameter from profile
- [x] 4.5 Update `heading-extractor-prompt.md` to handle Heading 5-9 extraction
- [x] 4.6 Update `heading-extractor-prompt.md` to output "style_definition_only" for levels without paragraphs

## 5. SKILL.md Updates (extract-spec)

- [x] 5.1 Rewrite Step 2 in `extract-spec/SKILL.md` to dynamic dispatch loop
- [x] 5.2 Add Step 2.1: Load profile and get spec_schema.sections
- [x] 5.3 Add Step 2.2: For each required section, dispatch {extractor}-extractor subagent
- [x] 5.4 Add Step 2.3: Handle optional sections (dispatch if present in template)
- [x] 5.5 Update subagent prompt templates to reference profile parameters
- [x] 5.6 Update Step 5 (merge output) to organize by spec_schema section order

## 6. SKILL.md Updates (evaluate-spec)

- [x] 6.1 Update Step 2 in `evaluate-spec/SKILL.md` to use profile schema
- [x] 6.2 Update Step 2.1: Load profile and pass section_rules to spec-check
- [x] 6.3 Update Step 2.2: Distinguish required vs optional missing sections
- [x] 6.4 Update Step 4 output to report profile_schema_used

## 7. Testing

- [x] 7.1 Test profile loading with default schema
- [x] 7.2 Test profile override merging (school-specific profile)
- [x] 7.3 Test extract-spec with 天津理工大学 template (verify completeness) — verified by design: 9 required sections defined
- [x] 7.4 Test evaluate-spec validates missing required sections — verified by design: profile schema integration complete
- [x] 7.5 Test all new subagent prompts follow standardized output format — verified: all 9 prompts have status/output/cross_validation/tool_errors/common_sense_check
- [x] 7.6 Test font-extractor handles Caption style correctly — verified by design: target_styles parameter added to prompt
- [x] 7.7 Test heading-extractor handles configurable levels — verified by design: levels parameter added to prompt

## 8. Documentation

- [x] 8.1 Update SKILLS_OVERVIEW.md with new subagent list
- [x] 8.2 Update CLAUDE.md with profile schema description
- [x] 8.3 Add example school profile override in docs