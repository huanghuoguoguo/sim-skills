## Why

The current 20 skills are well-designed with clear triggers and boundaries, but lack a unified overview document showing their relationships, categories, and dependency hierarchy. This makes it harder for users and new contributors to understand the skill architecture at a glance.

Additionally, there are minor naming inconsistencies and potential opportunities for consolidation that warrant review before adding more skills.

## What Changes

- Add a `SKILLS_OVERVIEW.md` document in `.claude/skills/` that maps all skills by category and shows their relationships
- Document the skill hierarchy: Capability → Workflow → Meta/Utility
- Review and potentially rename `batch-check` to `check-rules` for consistency with `compare-docs`
- Consider merging `visual-check` into `check-thesis` workflow documentation (as an optional sub-step)
- Update SKILL.md descriptions to reference the overview document

## Capabilities

### New Capabilities

- `skills-overview`: A single reference document that categorizes all skills, shows their relationships, and provides a navigation map for the skill system

### Modified Capabilities

No existing capability specs are being modified. This is a documentation-only change.

## Impact

- `.claude/skills/SKILLS_OVERVIEW.md` (new file)
- Minor updates to existing SKILL.md frontmatter descriptions
- No changes to Python implementation code