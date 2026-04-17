## Context

`sim_docs/` is the unified document service behind every skill in this repo (parse, check, stats, render, validate, inspect, compare, pdf, text, spec). Today it is a flat package of 14 modules plus a `DocumentService` god-class (~500 lines, 12+ unrelated methods) and a 370-line hand-written `cli.py`. Naming is inconsistent (`*_engine.py` variously means pure function module, thin script wrapper, or mode-dispatcher), `__init__.py` mutates `sys.path` into `.claude/skills/validate-word/scripts/`, and only 3 of 8 engines have unit tests. Every new feature either bloats `service.py` or adds another top-level module, reinforcing the mess.

External consumers are: (a) the CLI invoked by skills via `python3 -m sim_docs …`, and (b) a small Python import surface used inside tests and possibly by SKILL helpers. Both contracts must keep working during the refactor.

## Goals / Non-Goals

**Goals:**
- One obvious place for every module, organized by domain.
- Strict, one-way dependency layering so `analysis/` and `spec/` are document-agnostic and independently testable.
- Thin, domain-scoped API facade; no god-class.
- CLI where adding a command touches exactly one file.
- Remove the `sys.path` hack; the package becomes self-contained.
- Test suite mirrors source tree, with scaffolding for previously uncovered modules.
- Migration lands in phases that each ship green.

**Non-Goals:**
- Changing CLI subcommand names, flags, or JSON output shapes.
- Rewriting parser/engine logic — this is reorganization, not behaviour change.
- Adding new features, capabilities, or dependencies.
- Changing skill files in `.claude/skills/*/SKILL.md`.
- Performance optimization of parsing or checking.

## Decisions

### 1. Target package layout

```
sim_docs/
├── __init__.py          # public re-exports only
├── __main__.py          # → sim_docs.cli.main:main
├── api.py               # thin domain-scoped facade (see §2)
│
├── core/                # infra, no domain knowledge
│   ├── cache.py
│   ├── paths.py         # resolve_path, ~ expansion, glob
│   ├── io.py            # write_json_output, read helpers
│   └── soffice.py
│
├── word/
│   ├── models.py        # ← docx_parser_models.py
│   ├── parser.py        # ← docx_parser.py
│   ├── adapter.py       # ← adapters/word.py (kept only if it adds value)
│   ├── render.py        # ← service.render + _convert_to_pdf
│   ├── inspect.py       # ← inspect_engine.py
│   ├── compare.py       # ← compare_engine.py
│   └── validate/
│       ├── __init__.py  # ← validate_engine.py
│       └── schemas/     # vendored XSDs (moved from .claude/skills/validate-word/scripts/schemas)
│
├── pdf/extract.py       # ← pdf_engine.py
├── text/read.py         # ← text_sources.py
│
├── analysis/
│   ├── checks.py        # ← check_engine.py
│   └── stats.py         # ← stats_engine.py
│
├── spec/
│   ├── engine.py        # ← spec_engine.py (four pure functions, no dispatcher)
│   ├── rules.py         # ← spec_rules.py
│   └── profiles.py      # ← thesis_profiles.py
│
├── cli/
│   ├── __init__.py
│   ├── main.py
│   └── commands/
│       ├── _base.py     # shared: _write_output, argument helpers, Command protocol
│       ├── parse.py
│       ├── query.py     # query-style + query-text
│       ├── check.py
│       ├── stats.py
│       ├── render.py
│       ├── validate.py
│       ├── inspect.py
│       ├── compare.py
│       ├── read.py      # read-text + read-pdf
│       └── spec.py      # spec-check (--mode)
│
└── tests/               # mirror source tree
```

**Alternatives considered:** (a) keep flat layout but rename modules — rejected, doesn't fix god-class or CLI; (b) split `sim_docs` into multiple sibling packages — rejected, overkill and breaks import paths for no gain.

### 2. API facade shape

Replace `DocumentService` with a **namespace facade**. `api.py` exposes:

```python
from sim_docs import api
api.word.parse(path)              api.word.query_style(path, name)
api.word.render(path, page=…)     api.word.validate(path, …)
api.analysis.check(path, checks)  api.analysis.stats(path, …)
api.pdf.extract(path, …)          api.text.read(path)
api.spec.check_conflicts(path)    api.spec.check_structure(path, …)
```

Each namespace is a small module (~50–100 lines) holding a shared `DocumentCache` and delegating to domain modules. Backwards compat: `sim_docs.DocumentService` stays as a deprecated thin wrapper delegating to `api.*` until all internal callers migrate.

**Alternatives:** (a) multiple `WordService`/`SpecService` classes — same cohesion gain but more ceremony; (b) pure module-level functions with no cache — rejected, cache is useful across CLI calls within one process (tests, batched tools). Namespace facade preserves the single-entry-point ergonomics users currently get from `DocumentService`.

### 3. CLI auto-registration

Each `cli/commands/<name>.py` exports:

```python
NAME = "parse"
HELP = "Parse Word document to structured facts"

def add_parser(sub): …          # adds subparser, returns it
def run(args) -> int: …         # executes, returns exit code
```

`cli/main.py` discovers commands via an explicit `COMMANDS = [parse, query, check, …]` import list (not `importlib` magic — explicit > implicit, easier for type checkers). Shared `_write_output`, JSON loading, and path resolution live in `_base.py`.

Benefit: adding a command = one new file + one line in `COMMANDS`. Testing a command = import its module directly, no argparse plumbing in tests.

### 4. Dependency layering (enforced by review, not tooling yet)

```
cli  ─▶  api  ─▶  {word, pdf, text, analysis, spec}  ─▶  core
```

Rules:
- `core/` imports nothing from siblings.
- `word/`, `pdf/`, `text/` import only from `core/`.
- `analysis/`, `spec/` import only from `core/` and consume `facts: dict` at their boundary — they **do not** import `word.parser` directly. This is what makes them document-agnostic.
- `api.py` is the only module that wires parser → analysis.
- `cli/` depends only on `api` + `core.io`.

### 5. Vendor validator schemas

Move `.claude/skills/validate-word/scripts/schemas/` + validator modules into `sim_docs/word/validate/`. Delete the `sys.path` mutation in `__init__.py`. The skill directory keeps its `SKILL.md` but the Python code becomes a thin shell calling `sim_docs api`.

### 6. Tests layout

`sim_docs/tests/` mirrors source: `tests/word/test_parser.py`, `tests/analysis/test_checks.py`, `tests/spec/test_engine.py`, etc. Existing 3 tests move into new layout. Add **smoke tests only** (import + one happy-path call) for previously uncovered modules — full coverage is out of scope for this change.

## Risks / Trade-offs

- **Broken imports for external callers** → Mitigation: Phase 1 moves files but keeps `sim_docs/<old_name>.py` re-export shims (`from .word.parser import *`). Phase 3 removes shims only after grep confirms no external use.
- **CLI regression** → Mitigation: before removing old `cli.py`, run every subcommand against a canonical `.docx` and diff JSON output against a pre-refactor baseline stored in `tests/cli_golden/`.
- **Validator schemas path break** → Mitigation: Phase 2 does the schema move with a parallel period where both locations work; remove old path only after CI green.
- **Skills that import Python symbols from `sim_docs`** → Mitigation: `sim_docs/__init__.py` keeps exporting `DocumentService`, `WordDocumentFacts`, `ParagraphFact`, `StyleFact`, `HeaderFooterFact` with unchanged signatures.
- **Large diff, hard to review** → Mitigation: three commits, one per phase; each phase is independently green.
- **Hidden coupling surfaces during move** (e.g., `spec_engine` secretly reaching into parser) → Mitigation: layer violations surface as import errors during Phase 2; triage case-by-case, either push the logic into `api.py` or pass facts in explicitly.

## Migration Plan

**Phase 1 — Move & shim (1 commit):**
1. Create new directories, move files with `git mv` preserving history.
2. In each old top-level module, leave a single-line re-export shim: `from sim_docs.word.parser import *  # noqa`.
3. Update internal imports within moved files to new paths.
4. Run existing tests + CLI smoke. Green = ship.

**Phase 2 — API split & schemas vendor (1 commit):**
5. Introduce `sim_docs/api.py` with `word/analysis/pdf/text/spec` namespaces.
6. Rewrite `DocumentService` as a deprecated thin wrapper over `api.*`.
7. Move validator schemas into `sim_docs/word/validate/schemas/`; delete `sys.path` hack from `__init__.py`.
8. Run tests + CLI smoke.

**Phase 3 — CLI rewrite & shim removal (1 commit):**
9. Build `cli/` with per-command modules + `_base.py`.
10. Replace `cli.py` with a re-export to `cli.main`.
11. Grep for external references to old top-level modules; if clean, delete Phase 1 shims.
12. Update `CLAUDE.md` tree diagram. Add golden CLI tests.

**Rollback:** each phase is a single commit; revert is `git revert <sha>`.

## Open Questions

- Should `sim_docs.DocumentService` be kept permanently as a stable API, or removed once internal callers migrate? Default: keep, mark deprecated in docstring, revisit in 6 months.
- Do any `.claude/skills/` scripts import `sim_docs.*` Python symbols (beyond CLI)? Needs a grep during Phase 1 kickoff to size the compat shim surface.
- Is `adapters/word.py` pulling its weight, or collapsible into `word/parser.py`? Decide during Phase 1 based on what it actually adds.
