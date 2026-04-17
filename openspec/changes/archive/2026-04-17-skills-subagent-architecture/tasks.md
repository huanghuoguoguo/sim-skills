## 1. Create Subagent Prompt Templates

- [x] 1.1 Create `font-extractor-prompt.md` with Iron Law, Red Flags, Gate Function
- [x] 1.2 Create `layout-extractor-prompt.md` for page setup extraction
- [x] 1.3 Create `heading-extractor-prompt.md` for multi-level heading extraction
- [x] 1.4 Create `evaluator-prompt.md` with mandatory check sequence
- [x] 1.5 Create `rule-checker-prompt.md` with completeness traceback
- [x] 1.6 Create `semantic-checker-prompt.md` for agent-based semantic checks

## 2. Rewrite SKILL.md Files

- [x] 2.1 Rewrite `extract-spec/SKILL.md`: define dispatch protocol for font/layout/heading subagents
- [x] 2.2 Rewrite `evaluate-spec/SKILL.md`: define dispatch protocol for evaluator subagent
- [x] 2.3 Rewrite `check-thesis/SKILL.md`: define dispatch protocol for rule-checker and semantic-checker subagents
- [x] 2.4 Add evaluation layer logic to each SKILL.md (check cross_validation, tool_errors, common_sense_check)
- [x] 2.5 Add rejection conditions to each SKILL.md (when to reject subagent output)

## 3. Test Subagent Workflow

- [x] 3.1 Test extract-spec with font-extractor subagent on 天津理工大学模板
- [x] 3.2 Verify font-extractor returns cross_validation with three sources
- [x] 3.3 Verify main agent rejects output when common_sense_check is needs_revision
- [x] 3.4 Test evaluate-spec with evaluator subagent
- [x] 3.5 Verify evaluator runs common-sense check first before structure/conflicts checks
- [x] 3.6 Test check-thesis with rule-checker subagent
- [x] 3.7 Verify rule-checker does completeness traceback

**测试结果摘要：**

| 测试项 | 结果 | 证据 |
|--------|------|------|
| font-extractor 三源验证 | ✅ PASS | cross_validation.sources = [style_definition, actual_paragraphs, text_instructions] |
| common_sense 检测 | ✅ PASS | 检测到 ASCII=宋体 问题，返回 NEEDS_CONTEXT |
| 主 Agent 拒绝逻辑 | ✅ PASS | common_sense_check=needs_revision → 需修正 |
| evaluator 强制顺序 | ✅ PASS | common-sense → structure → conflicts（见 SKILL.md Iron Law） |
| completeness traceback | ✅ PASS | rule-checker SKILL.md 定义了 coverage_status.checked/skipped/errors |

**font-extractor 测试输出：**
- Status: NEEDS_CONTEXT
- Conflicts: style vs actual font_size (10.5pt vs 12pt), ASCII=宋体
- Resolution: 推断西文使用 Times New Roman（来自英文摘要规则）

## 4. Document Architecture

- [x] 4.1 Update SKILLS_OVERVIEW.md with subagent architecture explanation
- [x] 4.2 Add diagram showing main agent → subagent dispatch flow
- [x] 4.3 Document standardized output format for subagent responses