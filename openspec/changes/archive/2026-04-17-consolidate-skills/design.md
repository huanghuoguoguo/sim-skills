## Context

`.claude/skills/` contains 21 skills organized into three layers: capability (11), workflow (3), meta (4), visual (1), utility (2). The architecture is sound, but several skills at the capability layer duplicate functionality across different modes or file formats:

- `query-word-text` and `query-word-style` both query Word documents, differing only by search dimension (text keyword vs style name)
- `read-pdf` and `read-text` both read document content, differing only by input format
- `openspec-*` (4 skills) manage a single lifecycle: propose → apply → archive, with explore as a thinking mode

Each skill has its own `SKILL.md` with frontmatter description. Workflow skills (`extract-spec`, `check-thesis`) invoke these capability skills. The CLI (`python3 -m sim_docs`) already has unified entry points (`query-text`, `query-style` as separate commands).

Stakeholders: Agent (invokes skills), users (trigger via slash commands), workflow skills (chain capability skills).

## Goals / Non-Goals

**Goals:**
- Reduce skill count from 21 to 15 without losing functionality
- Unified skill naming: single skill with mode/subcommand instead of fragmented skills
- Clear trigger patterns for merged skills
- Update cross-references in workflow skills
- Preserve CLI behavior (user-facing commands unchanged)

**Non-Goals:**
- Changing CLI command names or flags (`query-text`, `query-style` stay separate at CLI level)
- Modifying skill execution logic — only reorganizing skill directories and SKILL.md
- Adding new capabilities or features

## Decisions

### 1. Merge strategy: unified SKILL.md with subcommands

Each merged skill gets a single `SKILL.md` with frontmatter describing all modes/subcommands. Trigger patterns cover all use cases.

**Alternative A: Keep separate skills with shared base**
- Rejected: still multiplies skill count, no simplification

**Alternative B: Create wrapper skill that dispatches**
- Rejected: adds indirection layer; unified SKILL.md is cleaner

**Chosen approach:** Direct merge into single SKILL.md with explicit subcommand documentation.

Example `query-word/SKILL.md` frontmatter:
```yaml
---
name: query-word
description: "Query Word documents for text content or style properties. Use --mode text for keyword search, --mode style for resolved style properties. Triggers: 'search paragraphs', 'find keyword', 'what font', 'style properties', 'query text', 'query style'."
---
```

### 2. CLI commands remain separate

The CLI layer (`sim_docs/cli/commands/query.py`) already has `query-text` and `query-style` as separate subcommands. No change to CLI structure. The skill consolidation affects only `.claude/skills/` organization.

**Rationale:** CLI users expect `query-text` and `query-style` as intuitive commands; skill consolidation is internal organization.

### 3. openspec becomes single slash-command skill

Current: `/opsx:propose`, `/opsx:apply`, `/opsx:archive`, `/opsx:explore` (4 slash commands)
Proposed: `/openspec propose`, `/openspec apply`, `/openspec archive`, `/openspec explore` (1 skill with subcommands)

**Alternative: Keep 4 slash commands**
- Rejected: fragmentation; single `/openspec` is clearer lifecycle view

**Implementation:** New `openspec/SKILL.md` with subcommand dispatch. Delete old `openspec-*` directories.

### 4. read-docs auto-detects format

`read-docs` inspects file extension and routes to appropriate engine (.pdf → `pdf/extract.py`, .txt/.md → `text/read.py`).

**Alternative: Require explicit format flag**
- Rejected: format is obvious from extension; auto-detection reduces friction

### 5. Migration: delete old dirs, update references

Workflow skills (`extract-spec`, `check-thesis`, `evaluate-spec`) reference the old skill names in their SKILL.md descriptions. Update these references to use the new unified skill names.

## Risks / Trade-offs

- **Breaking change for skill invocation** → Mitigation: Agent reads new SKILL.md trigger patterns; existing workflow descriptions updated
- **User confusion on slash commands** → Mitigation: `/openspec` mirrors familiar patterns (`git add`, `git commit`); announce in CLAUDE.md
- **Missed cross-reference** → Mitigation: grep all SKILL.md files for old skill names before deletion
- **Lost trigger pattern specificity** → Mitigation: merged SKILL.md includes all trigger keywords from both originals

## Migration Plan

**Phase 1: Create merged skills**
1. Create `query-word/SKILL.md` combining both query skills' triggers + descriptions
2. Create `read-docs/SKILL.md` combining read skills
3. Create `openspec/SKILL.md` with subcommand dispatch

**Phase 2: Update references**
4. Update `extract-spec/SKILL.md`, `check-thesis/SKILL.md`, `evaluate-spec/SKILL.md` to reference new skill names
5. Update `SKILLS_OVERVIEW.md` hierarchy diagram

**Phase 3: Delete old skills**
6. Remove `query-word-text/`, `query-word-style/`, `read-pdf/`, `read-text/`
7. Remove `openspec-propose/`, `openspec-apply-change/`, `openspec-archive-change/`, `openspec-explore/`

**Rollback:** Revert each phase commit; old skill directories restored from git.

## Open Questions

- Should `/openspec` use `propose`/`apply`/`archive` or `new`/`run`/`done` naming? Default: preserve current terminology (`propose`, `apply`, `archive`).
- Should CLI be unified (`query --mode`) or stay separate (`query-text`, `query-style`)? Default: stay separate (user familiarity).