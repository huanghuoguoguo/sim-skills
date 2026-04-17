## Context

The `.claude/skills/` directory contains 20 skills organized loosely by type:
- 10 capability skills (tool wrappers)
- 4 workflow skills (composite orchestrators)
- 4 OpenSpec meta-skills (workflow management)
- 2 utility skills

Skills are well-designed with clear triggers in frontmatter, but there's no top-level view. Users must read individual SKILL.md files to understand the architecture.

Current skill categories (derived from analysis):

| Category | Skills | Purpose |
|----------|--------|---------|
| **Core Parsing** | `parse-word` | Foundation: docx → structured facts |
| **Query/Stats** | `query-word-text`, `query-word-style`, `paragraph-stats` | Query and analyze parsed content |
| **Validation** | `batch-check`, `validate-word` | Compare against rules or schemas |
| **Debugging** | `inspect-word-xml` | Raw XML inspection for edge cases |
| **Visual** | `render-word-page`, `visual-check` | Page rendering and vision workflows |
| **Other Docs** | `read-pdf`, `read-text` | PDF and text file reading |
| **Comparison** | `compare-docs` | Document diffing |
| **Workflow** | `extract-spec`, `check-thesis`, `evaluate-spec` | Upstream/downstream document workflows |
| **OpenSpec** | `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, `openspec-explore` | Change lifecycle management |
| **Utility** | `peek-thinking` | Model debugging |

## Goals / Non-Goals

**Goals:**
- Create a single `SKILLS_OVERVIEW.md` that serves as a navigation map
- Document skill relationships and dependency hierarchy
- Clarify which skills are meant to be user-facing vs internal
- Provide guidance on when to use which skill

**Non-Goals:**
- Merge skills (current design is clean, each has distinct purpose)
- Change Python implementation
- Create new skills

## Decisions

### Decision 1: Overview Document Location

**Choice:** `.claude/skills/SKILLS_OVERVIEW.md`

**Alternatives considered:**
- `.claude/skills/README.md` — would conflict with potential skill-specific READMEs
- `.claude/SKILLS.md` — too far from actual skills directory

**Rationale:** Keeps overview adjacent to the skills it describes, easy to find when navigating the skills directory.

### Decision 2: Organization Structure

**Choice:** Group by functional category, not by alphabetical order

**Alternatives considered:**
- Alphabetical list — harder to understand relationships
- Dependency graph only — harder to find specific skills

**Rationale:** Categories help users understand skill purpose at a glance. Dependency graph is a supplementary section.

### Decision 3: Naming Consistency Review

**Choice:** Keep current names, note inconsistency in overview

**Alternatives considered:**
- Rename `batch-check` → `check-rules` — would require updating all references

**Rationale:** Current names are clear enough. Renaming would break existing documentation references. Document the naming convention instead.

## Risks / Trade-offs

**Risk: Overview becomes outdated as skills evolve**
→ Mitigation: Make overview a living document, update when adding/removing skills

**Risk: Users might skip reading individual SKILL.md if overview is comprehensive**
→ Mitigation: Keep overview as a navigation map, not a replacement for detailed SKILL.md content

**Trade-off: Adding documentation overhead vs clarity**
→ Acceptable: One overview file is minimal overhead for significant clarity improvement