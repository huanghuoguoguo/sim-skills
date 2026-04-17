## 1. Python Code: Common Sense Check

- [x] 1.1 Add `check_common_sense()` function to `sim_docs/spec_engine.py`
- [x] 1.2 Add CLI support for `--mode common-sense` in `sim_docs/cli.py`
- [x] 1.3 Test: `python3 -m sim_docs spec-check --mode common-sense spec.md` returns font conflicts

## 2. SKILL.md: extract-spec Constraints

- [x] 2.1 Add Iron Law section: `NO RULE WRITTEN WITHOUT CROSS-VALIDATION`
- [x] 2.2 Add Red Flags section with 5+ self-check triggers
- [x] 2.3 Add Rationalization Table with 4+ excuse/rebuttal pairs
- [x] 2.4 Add Gate Function pseudo-code for font rule verification
- [x] 2.5 Add Font Common Sense section explaining Chinese fonts ≠ Western fonts
- [x] 2.6 Add Tool Error Handling requirement

## 3. SKILL.md: evaluate-spec Constraints

- [x] 3.1 Add Iron Law: `NO SPEC DELIVERY WITHOUT COMMON-SENSE CHECK`
- [x] 3.2 Add Required skill chain: extract-spec → evaluate-spec → spec-check
- [x] 3.3 Add Tool Error Reporting requirement

## 4. SKILL.md: check-thesis Constraints

- [x] 4.1 Add Red Flags section for common shortcuts
- [x] 4.2 Add Rationalization Table for incomplete check excuses
- [x] 4.3 Strengthen completeness traceback requirement

## 5. Integration Testing

- [x] 5.1 Test full workflow: extract-spec → evaluate-spec on 天津理工大学模板
- [x] 5.2 Verify font common sense conflict is detected and reported
- [x] 5.3 Verify tool errors are not silently ignored