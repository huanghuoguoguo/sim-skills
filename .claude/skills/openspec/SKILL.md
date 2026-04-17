---
name: openspec
description: "Manage OpenSpec change lifecycle. Subcommands: propose (create change), apply (implement tasks), archive (finalize), explore (thinking mode). Triggers: 'openspec', 'propose', 'apply', 'archive', 'change lifecycle', 'create change', 'implement change', '/openspec', '/opsx'. Use `/openspec <subcommand>` to invoke."
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "2.0"
---

# openspec

Unified OpenSpec change lifecycle management.

## Subcommands

| Subcommand | Purpose | Alias |
|------------|---------|-------|
| `propose` | Create new change with all artifacts | `/opsx:propose` |
| `apply` | Implement tasks from a change | `/opsx:apply` |
| `archive` | Archive completed change | `/opsx:archive` |
| `explore` | Enter thinking mode for ideas/problems | `/opsx:explore` |

## Usage

```bash
/openspec propose <name>      # Create change proposal
/openspec apply <name>        # Implement tasks
/openspec archive <name>      # Archive completed change
/openspec explore             # Enter thinking mode
```

## Lifecycle Flow

```
propose → apply → archive
         ↑
      explore (optional: before/during)
```

---

## propose

Create a new change with artifacts:
- proposal.md (what & why)
- design.md (how)
- specs/*.md (requirements)
- tasks.md (implementation steps)

**Input**: Change name (kebab-case) or description.

**Steps**:
1. If no input, ask what to build
2. Create change directory: `openspec new change "<name>"`
3. Get artifact build order: `openspec status --change "<name>" --json`
4. Create artifacts in sequence until apply-ready

---

## apply

Implement tasks from a change.

**Input**: Change name (optional, inferred from context if possible).

**Steps**:
1. Select change (prompt if ambiguous)
2. Check status: `openspec status --change "<name>" --json`
3. Read context files (proposal, design, specs, tasks)
4. Implement each task, mark complete as you go
5. On completion, suggest archive

---

## archive

Archive a completed change.

**Input**: Change name (optional).

**Steps**:
1. Prompt for selection if no name
2. Check artifact completion
3. Move change to archive directory
4. Update timestamps

---

## explore

Enter explore mode - a thinking partner for exploring ideas.

**IMPORTANT**: Explore mode is for thinking, NOT implementing. You may read files and investigate, but never write code. If user asks to implement, remind them to exit and run `/openspec propose`.

**Stance**:
- Curious, not prescriptive
- Open threads, not interrogations
- Visual (use ASCII diagrams)
- Adaptive (follow interesting threads)
- Grounded (explore actual codebase)