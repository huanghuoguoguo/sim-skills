## 1. Pre-flight

- [ ] 1.1 Grep the repo for external importers of `sim_docs.*` Python symbols (outside `sim_docs/` itself) and record the list — this sizes the compat-shim surface.
- [ ] 1.2 Capture a CLI baseline: run every `python3 -m sim_docs <subcommand>` against a canonical `.docx` fixture, save JSON outputs under `sim_docs/tests/cli_golden/`.
- [ ] 1.3 Create a working branch `refactor/sim-docs-layout`.

## 2. Phase 1 — Move & shim

- [ ] 2.1 Create subpackage directories: `sim_docs/{core,word,pdf,text,analysis,spec,cli}/` with empty `__init__.py`.
- [ ] 2.2 `git mv` files into targets: `cache.py`→`core/cache.py`, `utils.py`→`core/paths.py` (+ extract io helpers into `core/io.py`), `soffice.py`→`core/soffice.py`, `docx_parser.py`→`word/parser.py`, `docx_parser_models.py`→`word/models.py`, `adapters/word.py`→`word/adapter.py`, `inspect_engine.py`→`word/inspect.py`, `validate_engine.py`→`word/validate/__init__.py`, `compare_engine.py`→`word/compare.py`, `pdf_engine.py`→`pdf/extract.py`, `text_sources.py`→`text/read.py`, `check_engine.py`→`analysis/checks.py`, `stats_engine.py`→`analysis/stats.py`, `spec_engine.py`→`spec/engine.py`, `spec_rules.py`→`spec/rules.py`, `thesis_profiles.py`→`spec/profiles.py`.
- [ ] 2.3 Update all intra-package imports inside moved files to new paths.
- [ ] 2.4 Extract `render` helpers out of `service.py` into `sim_docs/word/render.py`.
- [ ] 2.5 Leave a one-line re-export shim at every old top-level path (e.g., `sim_docs/docx_parser.py` → `from sim_docs.word.parser import *  # noqa`) for each importer recorded in 1.1.
- [ ] 2.6 Decide the fate of `adapters/word.py`: if it only forwards to parser, inline it into `word/parser.py` and drop `word/adapter.py`; otherwise keep. Document the decision in the commit message.
- [ ] 2.7 Run existing test suite; run CLI baseline from 1.2 and diff. Commit if green.

## 3. Phase 2 — API split & schema vendor

- [ ] 3.1 Create `sim_docs/api.py` with namespace objects `api.word`, `api.analysis`, `api.pdf`, `api.text`, `api.spec`. Wire them to a shared `DocumentCache`.
- [ ] 3.2 Move every method body from `DocumentService` into the matching `api.*` namespace; rewrite `DocumentService` as a deprecated thin wrapper delegating to `api.*` (keep signatures and return types identical).
- [ ] 3.3 Split `spec_engine` dispatcher: expose `spec.engine.check_conflicts`, `check_structure`, `check_body_consistency`, `check_common_sense` as standalone functions; remove any internal mode switch.
- [ ] 3.4 Move XSD schemas from `.claude/skills/validate-word/scripts/schemas/` into `sim_docs/word/validate/schemas/`; move validator Python modules alongside under `sim_docs/word/validate/`.
- [ ] 3.5 Delete the `sys.path` mutation from `sim_docs/__init__.py`; update validator imports to use relative paths.
- [ ] 3.6 Verify `.claude/skills/validate-word/SKILL.md` still works by invoking `python3 -m sim_docs validate <file.docx>`; update the skill if it still references the old path.
- [ ] 3.7 Enforce layering by eyeball: grep each subpackage's imports and confirm the rules in spec requirement "One-way dependency layering". Fix any violations by routing through `api.py`.
- [ ] 3.8 Run tests + CLI baseline. Commit if green.

## 4. Phase 3 — CLI rewrite & shim removal

- [ ] 4.1 Create `sim_docs/cli/commands/_base.py` with `_write_output`, JSON/argument helpers, and a `Command` protocol (`NAME`, `HELP`, `add_parser`, `run`).
- [ ] 4.2 Create one command module per subcommand under `sim_docs/cli/commands/`: `parse.py`, `query.py` (query-style + query-text), `check.py`, `stats.py`, `render.py`, `validate.py`, `inspect.py`, `compare.py`, `read.py` (read-text + read-pdf), `spec.py` (spec-check with `--mode`).
- [ ] 4.3 Write `sim_docs/cli/main.py` with an explicit `COMMANDS = [parse, query, check, …]` list and a `main()` that wires subparsers.
- [ ] 4.4 Update `sim_docs/__main__.py` to call `sim_docs.cli.main:main`.
- [ ] 4.5 Delete the old `sim_docs/cli.py` (or replace with a single-line re-export to `sim_docs.cli.main`).
- [ ] 4.6 Re-grep for old top-level module references; if none remain outside the shim files themselves, delete all Phase 1 re-export shims.
- [ ] 4.7 Run tests + CLI baseline diff; it MUST match byte-for-byte on stable fields. Commit if green.

## 5. Tests & docs

- [ ] 5.1 Create `sim_docs/tests/` subdirectories mirroring source layout.
- [ ] 5.2 Move existing tests (`test_cache.py`, `test_spec_engine.py`, `test_stats_engine.py`) into the matching subdirectories and update imports.
- [ ] 5.3 Add a smoke test (import + one happy-path call) for each domain subpackage that currently lacks one: `word/parser`, `word/render`, `word/inspect`, `word/validate`, `word/compare`, `pdf/extract`, `text/read`, `analysis/checks`, `cli/main`.
- [ ] 5.4 Add a CLI golden-output test that runs every subcommand and diffs against `tests/cli_golden/`.
- [ ] 5.5 Update the `sim_docs/` tree diagram in `CLAUDE.md` to reflect the new layout.
- [ ] 5.6 Update `sim_docs/README.md` with the new architecture overview and layering rules.

## 6. Wrap-up

- [ ] 6.1 Confirm all three phase commits are on the branch and each is independently green (checkout each commit, run tests).
- [ ] 6.2 Open a PR summarizing the three phases; link to `openspec/changes/refactor-sim-docs-layout/`.
- [ ] 6.3 After merge, run `/opsx:archive refactor-sim-docs-layout` to archive the change.
