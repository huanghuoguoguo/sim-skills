## Why

21 skills in `.claude/skills/` is manageable but several skills have overlapping concerns, creating unnecessary fragmentation. `query-word-text` and `query-word-style` both query Word documents; `read-pdf` and `read-text` both read document content; four `openspec-*` skills manage a single change lifecycle. Consolidating these reduces cognitive load and simplifies the hierarchy without losing functionality.

## What Changes

- **BREAKING**: Merge `query-word-text` + `query-word-style` into `query-word` with `--mode text/style` subcommands
- **BREAKING**: Merge `read-pdf` + `read-text` into `read-docs` (auto-detects format)
- **BREAKING**: Merge `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, `openspec-explore` into unified `openspec` skill with subcommands
- Update `SKILLS_OVERVIEW.md` to reflect new structure (15 skills)
- Delete merged skill directories, preserve only combined skills
- Update cross-references in workflow skills (`extract-spec`, `check-thesis`, `evaluate-spec`) that invoke the merged skills

## Capabilities

### New Capabilities
- `query-word`: Unified Word document querying with text search (`--mode text --keyword`) and style property lookup (`--mode style --name`)
- `read-docs`: Unified document content reader supporting .pdf, .txt, .md, .docx with format auto-detection
- `openspec`: Unified change lifecycle skill with `propose`, `apply`, `archive`, `explore` subcommands

### Modified Capabilities
- `extract-spec`: Updates skill invocation from `query-word-text`/`query-word-style` to `query-word --mode`
- `check-thesis`: Updates skill invocation references
- `evaluate-spec`: Updates skill invocation references

## Impact

- **Skills deleted**: `query-word-text`, `query-word-style`, `read-pdf`, `read-text`, `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, `openspec-explore` (8 total)
- **Skills created**: `query-word`, `read-docs`, `openspec` (3 new)
- **Skills updated**: `SKILLS_OVERVIEW.md`, `extract-spec/SKILL.md`, `check-thesis/SKILL.md`, `evaluate-spec/SKILL.md`
- **CLI unchanged**: `python3 -m sim_docs query-text` / `query-style` → `python3 -m sim_docs query --mode text/style`
- **User invocation**: `/opsx:propose` → `/openspec propose`; `/opsx:apply` → `/openspec apply`