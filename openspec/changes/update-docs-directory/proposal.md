## Why

The `docs/` directory contains 5 design documents that describe the MVP architecture before the recent consolidation. The tool scripts structure (`scripts/run.py`) and directory layout described in these docs no longer match the actual codebase after the unified `sim_docs` service layer was introduced.

These outdated docs cause confusion for new contributors and mislead Agent when it reads them for context.

## What Changes

- Update `docs/00-背景与机会.md` — minor: project name, skill count
- Update `docs/01-产品设计.md` — rewrite tool scripts section to reference `sim_docs` CLI
- Update `docs/02-MVP设计.md` — rewrite tool scripts table, directory structure, batch_check section
- Rewrite `docs/03-MVP实施方案.md` — mark as completed, archive or rewrite as implementation notes
- Minor update `docs/04-Spec-Schema草案.md` — add cross-reference to sim_docs

## Capabilities

### New Capabilities

None — this is documentation-only update.

### Modified Capabilities

None — no spec-level behavior changes.

## Impact

- `docs/*.md` files (5 files)
- No code changes
- README.md already accurate, no change needed