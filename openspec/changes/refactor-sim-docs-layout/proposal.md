## Why

The `sim_docs/` package has grown to 14 flat-layout modules with no layering or domain grouping. A 500-line `DocumentService` god-class and 370-line hand-written `cli.py` concentrate unrelated concerns, making the code hard to navigate, test, and extend. Adding a new command requires touching three places; tests cover only 3 of 8 engines; the package `__init__.py` mutates `sys.path` to reach skills outside the package. Before more features land on top, we need to impose high cohesion / low coupling so future iteration stays cheap.

## What Changes

- **BREAKING (internal API)**: Reorganize `sim_docs/` into domain subpackages: `core/`, `word/`, `pdf/`, `text/`, `analysis/`, `spec/`, plus `api.py` and `cli/`.
- Split the `DocumentService` god-class into domain-scoped namespaces exposed via a thin `api.py`. Preserve CLI behaviour and JSON output contracts.
- Collapse the `docx_parser.py` / `docx_parser_models.py` / `adapters/word.py` indirection into `word/{models,parser,adapter}.py`; drop the adapter if no second source exists.
- Restructure `cli.py` into `cli/commands/*.py` with auto-registration. Each command owns its `add_parser` + `run`, sharing helpers in `cli/commands/_base.py`.
- Vendor validator XSD schemas into `sim_docs/word/validate/schemas/` and remove the `sys.path` hack from `__init__.py`.
- Enforce a one-way dependency layering: `cli → api → {word,pdf,text,analysis,spec} → core`. `analysis/` and `spec/` consume facts, never import raw parsers.
- Mirror the source tree in `sim_docs/tests/` and add test scaffolding for currently uncovered engines (inspect, validate, compare, pdf, text, render).
- Migration executed in three phases (move + re-export shims, facade split, CLI rewrite) so each phase ships independently without breaking external call sites.

## Capabilities

### New Capabilities
- `sim-docs-package-layout`: Defines the directory structure, dependency-layering rules, public API surface (`sim_docs.api`, `sim_docs.DocumentService`), and CLI command registration contract for the `sim_docs` package.

### Modified Capabilities
<!-- No existing capability covers sim_docs package architecture. -->

## Impact

- **Affected code**: every module under `sim_docs/` is moved or renamed; `sim_docs/tests/` is expanded; external importers of `sim_docs` (package `__init__` re-exports) keep working via shims during migration.
- **External CLI contract**: `python3 -m sim_docs <subcommand>` invocations and their JSON outputs are unchanged.
- **Skills**: `.claude/skills/*/SKILL.md` that reference CLI commands are unaffected. Skills that import Python symbols from `sim_docs` keep working through the public API.
- **Docs**: `CLAUDE.md` "Skill Layout" section needs its `sim_docs/` tree diagram updated after migration.
- **Dependencies**: no new runtime dependencies. Removing the `sys.path` hack decouples the package from `.claude/skills/validate-word/scripts/` layout.
