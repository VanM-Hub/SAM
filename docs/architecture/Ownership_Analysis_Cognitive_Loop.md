# Ownership Analysis — SAM (Cognitive Loop Consolidation Gap)

> **Status:** Ownership analysis from direct code verification (2026-08-10), not from documentation.
> **Purpose:** Map *who owns what* before deciding Reuse / Generalize / Refactor / New for the mission cognitive pathway consolidation.
> **Rule of evidence:** Consolidation evidence = **execution trace** (components actually called on a running path), NOT merely injection points.

---

## 1. Key Finding: Multiple "Think-Act" Paths — All Real but Not Unified

Actual verification found **4 cognitive/action systems running in PARALLEL without connecting to each other**, each with its own engine:

| # | Path | Location | Loop/sequence | Operational? |
|---|---|---|---|---|
| 1 | **ReasoningEngine** | `reasoning/engine.py` | `reason()` / `reason_and_execute()` (text→Intent→Plan→Govern gate→Execute) | Tested, but **not runtime-driven** (no consumer; interface exists but not operated) |
| 2 | **SelfHealingLoop** | `healing/loop.py` | 9 phases: Observe→Diagnose→Reason→Plan→Govern→Execute→Verify→Reflect→Learn→(Observe) | Complete, but **run_cycle() not operated** (interface-level injection, not operational) |
| 3 | **GuardianPipeline** | `guardian/pipeline.py` | Observe→Analyze→Decide→Act→Verify (GDP) | **Operational** in CLI (`cli/guardian.py`) |
| 4 | **SelfHealingPlanner** | `autonomy_runtime/healing/` | plan + impact (**proposal only**, not a loop) | Used by Recovery API, but proposal only |

**Main conclusion:** SAM has several "think-act" engines that are each real, but **none is the canonical Mission Cognitive Runtime**. This is the essence of the **Cognitive Loop Consolidation Gap** — confirmed at the ownership level, not merely the concept level.

---

## 2. Ownership per Component (Declared / Wired / Operational)

### Evidence-level definitions
- **Declared**: component exists/registered in code (class/module present)
- **Wired**: component is connected (injected as a dependency) into the system
- **Operational**: component is actually called on a running path (execution trace)

### A. Reasoning→Execution Path ("owner" mission candidate)

| Component | Location | Declared | Wired | Operational | Verification note |
|---|---|---|---|---|---|
| `ReasoningEngine.reason_and_execute()` | `reasoning/engine.py:229` | Yes | Yes (called internally, calls `self._execution_engine.execute(graph)`) | No | **No runtime consumer**: grep for `reason_and_execute`/`ReasoningEngine(` outside `reasoning/` = EMPTY. Only `governed_reasoning/` tests call it. |
| `ExecutionGraphEngine.execute()` | `execution/engine.py:118` | Yes | Yes (injected into ReasoningEngine + SelfHealingLoop) | Partial | Operational ONLY when pulled by `reasoning/engine.py`; in `SelfHealingLoop` it is injected but **never called**. |
| `ProviderInvoker.invoke()` | `universal_ai/provider_invocation.py` | Yes | — | No | Real LLM engine, not yet wired to any cognitive loop. |

### B. Healing Path (complete closed loop, interface-level integration, not operational)

| Component | Location | Declared | Wired | Operational | Verification note |
|---|---|---|---|---|---|
| `SelfHealingLoop.run_cycle()` | `healing/loop.py` | Yes | Yes (accepts 9 dependencies) | No | **No call** to `SelfHealingLoop(` / `run_cycle()` from this loop outside `healing/loop.py`. Consumer grep = EMPTY. |
| `PlanningEngine` (injected) | `healing/loop.py:189` | Yes | Yes | No | Only assigned in `__init__`; `_phase_plan()` builds `HealingAction` MANUALLY via `strategy_map`, never calls the planner. |
| `ExecutionGraphEngine` (injected) | `healing/loop.py:190` | Yes | Yes | No | Only assigned; healing execution inline via `self._healing.execute_healing()`, not the graph engine. |
| `GovernanceEngine` (injected) | `healing/loop.py:188,480` | Yes | Yes | Partial | Used but **simplified**: `_phase_govern()` checks `severity >= 5 → allowed`, NOT full `evaluate(graph)`. |
| `EvolutionPolicy` | `healing/loop.py:191,646,697` | Yes | Yes | Yes | **Active** — `create_proposal()` (PENDING_APPROVAL), including when `confidence >= 0.7`. |
| `OperationalConfidenceCalculator` | `healing/loop.py:192,312,411` | Yes | Yes | Yes | **Active** — `get_current_score()` used in Observe & Verify. |
| `InstitutionalMemoryManager` | `healing/loop.py:193,348,746` | Yes | Yes | Yes | **Active** — `search()` in Diagnose, `store()` in Learn (lessons). |
| `ReflectionManager` | `healing/reflection.py:109` | Yes | Yes (used by SelfHealingLoop) | No | **No consumers outside `healing/`**. Grep `ReflectionManager` outside healing = EMPTY. Reflect complete but not driven on a mission loop. |

### C. Guardian Path (operational, oversight domain)

| Component | Location | Declared | Wired | Operational | Verification note |
|---|---|---|---|---|---|
| `GuardianPipeline.run_cycle()` | `guardian/pipeline.py` | Yes | Yes | Yes | **Operational** — called by `cli/guardian.py:102` via `asyncio.run()`. |
| `ObserverEngine.observe()` | `guardian/observer.py` | Yes | Yes | Yes | Active in Guardian pipeline. |
| `AnalyzerEngine.analyze()` | `guardian/analyzer.py` | Yes | Yes | Yes | Active; detects drift against DesiredOperationalState. |
| `DecisionEngine` / `ActionEngine` / `VerificationEngine` | `guardian/` | Yes | Yes | Yes | Active in Guardian pipeline. |

### D. Mission Runtime Path (representation/state, not a loop)

| Component | Location | Declared | Wired | Operational | Verification note |
|---|---|---|---|---|---|
| `MissionCoordinator.coordinate()` | `mission_runtime/mission_coordinator.py:21` | Yes | — | No | Only creates a `CoordinationPlan` (plan-only) and registers it. **Does not drive a mission loop.** |
| `mission_runtime/` (68 files) | `mission_runtime/` | Yes | — | No | Mission representation/state (builder, registry, snapshot, timeline, etc.), NOT an execution loop. |

### E. Observation Path

| Component | Location | Declared | Wired | Operational | Verification note |
|---|---|---|---|---|---|
| `ObservationEngine.observe()` | `autonomy_runtime/observation/engine.py` | Yes | Yes | Yes | **Operational** — used by `autonomy_runtime/api/observation.py:61` (Runtime Observation API). |
| `observation/` adapters (`observe()`) | `observation/adapters.py` | Yes | — | — | Many `PublicationAdapter.observe()` (mission/workflow/policy/execution/audit/knowledge/memory/artifact) — not seen wired to the mission/reasoning loop. |

---

## 3. Two DIFFERENT "Healing" Systems (potential duplication finding)

There are **two things named "healing"** with different behavior — do not mix them:

| | `sam/healing/` | `sam/autonomy_runtime/healing/` |
|---|---|---|
| Files | `loop.py`, `reflection.py` | `models.py`, `planner.py` |
| Core | `SelfHealingLoop` (9-phase loop) | `SelfHealingPlanner` (`SelfHealingPlan`, proposal-only) |
| Has loop? | Yes | No |
| Has Reflect/Learn? | Yes | No |
| Operational? | Not operated `run_cycle()` (interface-level only) | Used by Recovery API, but proposal only |
| Compliance boundary | — | `planning_checker.py:205` + `recovery_checker.py` bound the healing/recovery implementation location |

**Ownership implication:** Both use the name "healing" but one is a *full closed loop (unused)*, the other is a *proposal planner (used, not a loop)*. This is a source of ambiguity — consolidation must decide which gets which role, and which is merged/deactivated.

---

## 4. Decision Matrix (Reuse / Generalize / Refactor / New)

> This is an ENGINEERING OPINION for the authority to consider, NOT a final decision.

| Capability | Evidence status | Feasible option | Basis for consideration |
|---|---|---|---|
| `reasoning/engine.py` (Reason→Plan→Govern→Act) | Declared+Wired, Operational No (unless pulled) | **Reuse / Generalize** | Complete & tested engine. Strong candidate for the mission brain (add a caller). |
| `execution/engine.py` (ExecutionGraphEngine) | Operational Partial (when pulled by reasoning) | **Reuse** | Real graph engine + retry + compensation. Used by reasoning; just needs driving. |
| `SelfHealingLoop` (9-phase closed loop) | Declared+Wired, Operational No | **Generalize** (basis for mission loop) / **Reuse** (if re-scoped for mission) | Complete loop structure (Observe→Reflect→Learn→Next). Input is currently `Symptom`; needs generalization to `Mission/Goal`. |
| `ReflectionManager` | Operational No (not yet driven) | **Reuse** | Mature reflection repository (record/query/aggregate/lessons). Just needs mission-loop driving. |
| `GuardianPipeline` (Observe→Act→Verify) | **Operational** Yes | **Do not touch / leave as is** (oversight domain) | Already running in CLI; separate guard path. Avoid breaking what is operational. |
| `SelfHealingPlanner` (autonomy_runtime) | Operational Yes (proposal only) | **Refactor / merge** with `SelfHealingLoop` | Name twin to `sam/healing`; potential dual identity. |
| `MissionCoordinator` | Declared, Operational No | **Activate / clarify role** | Currently only makes a plan; could become mission ownership if extended. |
| `mission_runtime/` (68 files) | Declared | **Reuse as state layer** | Do not turn into a loop; use as the correct mission representation/state. |
| `observation/` + `autonomy_runtime/observation` | Operational Yes (runtime obs) | **Reuse as input boundary** | Observation already exists; needs wiring as input to the mission loop (Observe). |

---

## 5. Ownership Conclusion (facts, not decisions)

1. **SAM has several real cognitive/action paths** (ReasoningEngine, SelfHealingLoop, GuardianPipeline, SelfHealingPlanner) — each complete, but **parallel and disconnected**.
2. **Only GuardianPipeline is operational** on a running path (CLI); ReasoningEngine & SelfHealingLoop **have interfaces (interface-level) but `run_cycle()` is not operated** (not "fully isolated" — both already inject planning/execution); SelfHealingPlanner is **proposal-only**.
3. **Reflection & Learning are mature but not connected to a mission loop** — `ReflectionManager` is not consumed outside `healing/`.
4. **Planning/Execution bridges to SelfHealingLoop are interface-only** (injected, not called) — not operational integration.
5. **"Healing" name ambiguity** (two different systems) = Refactor/Merge candidate.
6. **The gap is CONSOLIDATION, not ABSENCE**: there is no canonical Mission Cognitive Runtime unifying Reason→Plan→Govern→Act→Observe→Reflect→Learn→Next-Decision in one Mission-scoped lifecycle. — Fully consistent with the **Cognitive Loop Consolidation Gap** framing.

---

## 6. Status & Handoff

- **Created:** 2026-08-10, engineering verification directly from `src/sam/` code.
- **References:** `Cognitive_Kernel_Gap_Analysis.md` and related internal ownership notes (internal references).
- **Awaiting authority decision:** choose the Reuse/Generalize/Refactor/New combination for consolidation (Section 4 matrix) — this is not an engineering settlement.
- **Rule held:** do not create a new `cognitive_kernel/` before ownership is final; evidence = execution trace, not injection.
