# Sprint 23 Completion Report — Graph Revision & Intent Evolution

**Date:** 2026-07-25
**Branch:** `feature/sprint13-plugin-runtime`
**Commit:** (after 6c63f73 + 6e59fc9 + pending commit)

---

## Summary

Sprint 23 is the final phase of Execution Graph intelligence, adding the ability for SAM to **revise graphs mid-execution** and **evolve intents** when new evidence suggests the original plan no longer fits.

---

## Fase 1 — Plan Candidates & Plan Ranking ✓

Delivered in previous work. Adds PlanCandidate and PlanRanker to the Reasoning pipeline, enabling the engine to generate multiple candidate execution plans and rank them by score.

---

## Fase 2 — Decision Nodes & Conditional Branching ✓ (6c63f73)

- Decision Node model (`DecisionNode`, `DecisionCondition`, `DecisionType`)
- Graph integration: `get_branch_target()`, enhanced `validate()`
- Engine: evidence accumulation, dynamic dependency injection, branch target skipping
- 11 decision-specific tests in `test_decision_nodes.py`

**Migration fix:** Removed duplicate `INSERT OR REPLACE INTO schema_version` from migrations 008–011 (6e59fc9).

---

## Fase 3 — Graph Revision & Intent Evolution ✓ (this commit)

### Files Created

| File | Description |
|------|-------------|
| `src/sam/reasoning/revision.py` | `GraphRevision` model + `RevisionManager` class |
| `src/sam/reasoning/evolution.py` | `IntentEvolution` model + `EvolutionManager` class |
| `src/sam/persistence/migrations/023_add_revision_tables.sql` | DB tables for `graph_revisions` and `intent_evolutions` |
| `test_revision_evolution.py` | 33 tests covering all scenarios |

### Files Modified

| File | Change |
|------|--------|
| `src/sam/execution/engine.py` | Added `revision_manager` parameter; `_check_and_propose_revision()` called after decision nodes detect unhealthy/failed evidence |
| `src/sam/reasoning/__init__.py` | Exported `GraphRevision`, `RevisionManager`, `RevisionTrigger`, `IntentEvolution`, `EvolutionManager` |

### GraphRevision & RevisionManager

- **GraphRevision** records: what changed (`new_nodes`, `modified_nodes`, `removed_nodes`), why (`reason`), what triggered it (`trigger` in {`decision_node`, `timeout`, `evidence_change`, `governance`, `manual`}), and full snapshots before/after
- **RevisionManager.propose_revision()** — accepts a graph ID, reason, and changes dict; auto-increments version against DB
- **RevisionManager.apply_revision()** — clones the graph, removes/cleans nodes, strips dangling dependencies
- **RevisionManager.get_revision_history()** — retrieves revision history from DB, newest first

### IntentEvolution & EvolutionManager

- **IntentEvolution** records: original → new intent mapping, evidence IDs that triggered the change, type/target transitions
- **EvolutionManager.propose_evolution()** — creates an evolution record with optional new Intent
- **EvolutionManager.apply_evolution()** — activates the new Intent by setting status to PLANNING
- **EvolutionManager.get_evolution_history()** — retrieves evolution history from DB

### Engine Integration

- `ExecutionGraphEngine` accepts an optional `revision_manager` parameter
- After each decision node completes, `_check_and_propose_revision()` scans accumulated evidence for failure signals (status == FAILED/COMPENSATED, output containing "unhealthy" or "warning")
- If triggers are detected, a `GraphRevision` is proposed via the manager

### Migration 023

- `graph_revisions`: id, graph_id, version, previous_version, reason, trigger, new_nodes, modified_nodes, removed_nodes, snapshot_before, snapshot_after, created_at
- `intent_evolutions`: id, original_intent_id, new_intent_id, evidence_ids, reason, original_type, new_type, original_target, new_target, timestamp

---

## Test Results

### Fase 3-specific (33 tests)

```
test_revision_evolution.py ........... (6 model tests)
test_revision_evolution.py ........... (9 revision manager tests)
test_revision_evolution.py ....... (7 evolution manager tests)
test_revision_evolution.py ..... (5 engine integration tests)
33 passed ✓
```

### Full test suite (excluding pre-existing migration-DB errors)

```
831 passed, 1 skipped ✓
```

### Pre-existing issues (not regressions)

- 4 integration tests fail on migration `010_add_knowledge_fts.sql` column reference (`no such column: statement`) — pre-existing
- 12 unit tests error on the same migration dependency — pre-existing
- All core unit tests (799) + Fase 3 tests (33) pass clean

---

## Architecture

```
ExecutionGraphEngine
    ├─ _run_topological() ── decision node ──→ _check_and_propose_revision()
    │                                             │
    │                                             ▼
    │                                       RevisionManager
    │                                           ├─ propose_revision()
    │                                           ├─ apply_revision()
    │                                           └─ get_revision_history()
    │
    ├─ _execute_decision_node()
    │
    └─ (optional) EvolutionManager
            ├─ propose_evolution()
            ├─ apply_evolution()
            └─ get_evolution_history()
```

---

## Next Steps for Aster's Review

1. **Fase 3 code review** — verify revision/evolution models and engine integration
2. **Migration validation** — fix pre-existing `010_add_knowledge_fts.sql` column bug (out of scope but blocking clean CI)
3. **Sprint 24 planning** — Plugin Runtime (as previously directed by Aster) or Observability/Monitoring layer
