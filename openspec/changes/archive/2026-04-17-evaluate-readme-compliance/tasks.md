## 1. Fix pdf_engine Bug

- [x] 1.1 Rename parameter `extract_tables` to `include_tables` in `pdf_engine.extract_pdf` function signature
- [x] 1.2 Update internal call from `return extract_tables(pdf_path, pages)` to `return _extract_tables(pdf_path, pages)` (or use renamed helper)
- [x] 1.3 Update CLI `read-pdf` command to map `--tables` flag to `include_tables=True`
- [x] 1.4 Update `service.py` `read_pdf` method signature to use `include_tables`
- [x] 1.5 Test: verify `python3 -m sim_docs read-pdf test.pdf --tables` runs without TypeError

## 2. Consolidate sys.path and Code Deduplication

- [x] 2.1 Add centralized sys.path setup in `sim_docs/__init__.py` (inject `.claude/skills/__libs__` and `validate-word/scripts`)
- [x] 2.2 Remove sys.path.insert calls from `adapters/word.py`
- [x] 2.3 Remove sys.path.insert calls from `service.py`
- [x] 2.4 Remove sys.path.insert calls from `check_engine.py`
- [x] 2.5 Remove sys.path.insert calls from `stats_engine.py`
- [x] 2.6 Remove sys.path.insert calls from `spec_engine.py`
- [x] 2.7 Remove duplicate `_generate_diff_report` from `cli.py`, import from `compare_engine`
- [x] 2.8 Update `cli.py` compare command to call `compare_engine.generate_diff_report`
- [x] 2.9 Test: verify `python3 -m sim_docs parse test.docx` still works after sys.path consolidation

## 3. Sync Documentation

- [x] 3.1 Add `docx_parser.py` and `docx_parser_models.py` to `sim_docs/README.md` Skill Layout
- [x] 3.2 Add `tests/` directory listing to `sim_docs/README.md` Skill Layout
- [x] 3.3 Verify and update root `README.md` Legacy Skill Scripts paths (remove or fix deleted references)
- [x] 3.4 Update `CLAUDE.md` Skill Layout to reflect parser relocation (remove `.claude/skills/word/scripts/` reference)
- [x] 3.5 Update `CLAUDE.md` Legacy Skill Scripts section to remove deleted script paths if any
- [x] 3.6 Add `HeaderFooterFact` to `sim_docs/__init__.py` exports
- [x] 3.7 Test: verify `from sim_docs import HeaderFooterFact` succeeds

## 4. Verification

- [x] 4.1 Run all existing tests: `python3 -m pytest sim_docs/tests/`
- [x] 4.2 Manual CLI smoke test: parse, check, stats, compare, read-pdf commands
- [x] 4.3 Review diff of all changes for consistency