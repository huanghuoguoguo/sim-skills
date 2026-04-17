## Context

The docs/ directory was written during MVP planning phase. Since then:

1. Tool scripts consolidated into `sim_docs` unified service layer
2. Scripts paths `scripts/run.py` replaced by CLI `python3 -m sim_docs`
3. Skills grew from 3 to 20 (10 capability + 4 workflow + 4 OpenSpec + 2 utility)
4. DocumentService provides LRU caching, which wasn't documented

Current state:
- README.md — accurate, reflects current structure
- sim_docs/README.md — accurate, CLI and Python API documented
- docs/ — outdated, describes pre-consolidation architecture

## Goals / Non-Goals

**Goals:**
- Sync docs/ with current architecture
- Preserve historical context (MVP planning rationale)
- Mark completed tasks in implementation doc

**Non-Goals:**
- Rewrite docs from scratch
- Add new documentation
- Change code structure

## Decisions

### Decision 1: Update In-Place vs Archive

**Choice:** Update in-place, preserve doc structure

**Alternatives considered:**
- Archive docs to `docs/archive/` — loses accessibility
- Delete docs — loses design rationale history

**Rationale:** The docs capture MVP planning decisions which remain valid. Just need to update tool script references and directory structures.

### Decision 2: Handle Implementation Doc

**Choice:** Rewrite `03-MVP实施方案.md` as "Implementation Notes" with status markers

**Alternatives considered:**
- Delete it — loses task history
- Leave unchanged — misleading about current state

**Rationale:** Mark each task as `[x]` or `[archived]` to show completion status, note what changed.

## Risks / Trade-offs

**Risk: Docs become outdated again as architecture evolves**
→ Mitigation: Add note at top linking to README.md and sim_docs/README.md as authoritative sources

**Trade-off: Spending time on docs vs feature work**
→ Acceptable: Small effort (5 files), prevents future confusion