## 1. Create merged skills

- [ ] 1.1 Create `.claude/skills/query-word/SKILL.md` with unified frontmatter (triggers: "search paragraphs", "find keyword", "what font", "style properties", "query text", "query style") and body documenting `--mode text` and `--mode style`
- [ ] 1.2 Create `.claude/skills/read-docs/SKILL.md` with unified frontmatter (triggers: "read text", "read pdf", "extract pdf", "plain text", "document content") and body documenting format auto-detection
- [ ] 1.3 Create `.claude/skills/openspec/SKILL.md` with unified frontmatter (triggers: "openspec", "propose", "apply", "archive", "change lifecycle") and body documenting subcommands: `propose`, `apply`, `archive`, `explore`

## 2. Update cross-references

- [ ] 2.1 Update `.claude/skills/extract-spec/SKILL.md`: replace references to `query-word-text`/`query-word-style` with `query-word`
- [ ] 2.2 Update `.claude/skills/check-thesis/SKILL.md`: replace references to `batch-check` and other merged skill references
- [ ] 2.3 Update `.claude/skills/evaluate-spec/SKILL.md`: replace any merged skill references
- [ ] 2.4 Update `.claude/skills/SKILLS_OVERVIEW.md`: replace skill hierarchy diagram and quick reference table with 15 skills (remove 8 merged, add 3 unified)

## 3. Delete old skill directories

- [x] 3.1 Delete `.claude/skills/query-word-text/` directory
- [x] 3.2 Delete `.claude/skills/query-word-style/` directory
- [x] 3.3 Delete `.claude/skills/read-pdf/` directory
- [x] 3.4 Delete `.claude/skills/read-text/` directory
- [x] 3.5 Delete `.claude/skills/openspec-propose/` directory
- [x] 3.6 Delete `.claude/skills/openspec-apply-change/` directory
- [x] 3.7 Delete `.claude/skills/openspec-archive-change/` directory
- [x] 3.8 Delete `.claude/skills/openspec-explore/` directory
- [x] 3.9 Delete `.claude/skills/batch-check/` directory (Phase 2: CLI consolidation)
- [x] 3.10 Delete `.claude/skills/paragraph-stats/` directory
- [x] 3.11 Delete `.claude/skills/parse-word/` directory
- [x] 3.12 Delete `.claude/skills/query-word/` directory
- [x] 3.13 Delete `.claude/skills/render-word-page/` directory
- [x] 3.14 Delete `.claude/skills/read-docs/` directory
- [x] 3.15 Delete `.claude/skills/validate-word/` directory
- [x] 3.16 Delete `.claude/skills/inspect-word-xml/` directory
- [x] 3.17 Delete `.claude/skills/compare-docs/` directory
- [x] 3.18 Delete `.claude/skills/peek-thinking/` directory
- [x] 3.19 Delete `.claude/skills/writing-skills/` directory

## 4. Update CLAUDE.md

- [x] 4.1 Update CLAUDE.md to document new skill count (5 workflow skills)
- [x] 4.2 Add reference to CLI_REFERENCE.md for CLI documentation
- [x] 4.3 Simplify Skill Layout section

## 4b. Create CLI_REFERENCE.md

- [x] 4b.1 Create comprehensive CLI_REFERENCE.md with all CLI tool documentation
- [x] 4b.2 Include all check types, selectors, parameters, output formats
- [x] 4b.3 Include Chinese font size mapping table
- [x] 4b.4 Include troubleshooting guidance

## 5. Verification

- [x] 5.1 Verify skill count: 5 workflow skills remaining
- [x] 5.2 Verify deleted: batch-check, paragraph-stats, parse-word, query-word, render-word-page, read-docs, validate-word, inspect-word-xml, compare-docs, peek-thinking, writing-skills
- [x] 5.3 Verify CLI_REFERENCE.md exists with comprehensive documentation
- [x] 5.4 Verify SKILLS_OVERVIEW.md reflects new architecture
- [x] 5.5 Verify CLAUDE.md points to CLI_REFERENCE.md