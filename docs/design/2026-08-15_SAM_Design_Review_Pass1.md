# SAM — Design Review (Pass 1)

**Reviewer:** External Design Review
**Date:** 2026-08-15
**Scope:** High-level design (constitutional + architectural + operational)
**Sources:** `MISSION.md`, `docs/foundation/*`, `docs/architecture/SAM_ARCHITECTURE.md`, `docs/specifications/*`, `docs/adr/*`, `ATLAS.md`, `src/sam/` (structure + sampled reads: `application/ux/service.py`, `api/routes/ux.py`, `api/server.py`, `execution_runtime/approval_gate.py`, `runtime_service/runtime_service.py`, `delegated_authority/authority.py`, `application/ux/runner.py`).

> **Methodology note:** This is a first-pass, opinionated high-level design review — not a formal compliance audit. It distinguishes factual observations (with sources) from subjective observations/questions.

---

## TL;DR

SAM is an unusually rare project. Most AI frameworks optimize for capability; SAM optimizes for *accountability*. The Mission → Constitution → Philosophy → Governance → Architecture → Specs → Implementation hierarchy, maintained with discipline, is its primary strength.

However, there are five areas where the design may break or become a burden at scale. These are detailed below, preceded by what works well.

---

## A. What Works Well

### A1. Identity hierarchy maintained with discipline
- Mission → Constitution (16 Articles) → Philosophy → Governance → Architecture → Specs → Implementation.
- These documents exist, cross-link, and have compliance audits (see `docs/compliance/P1-001..008`).
- **Constitution.md pattern**: each Article has Principle / Meaning / Architectural Impact / Supported Decisions / Violations. This is not just a good list — it is an explicit violation pattern. Few projects do this.

### A2. Article XVI (Presentation Principle) is genuinely useful
> "Presentation Layers shall never contain business logic. ... All runtime orchestration belongs to Runtime Service."

This is an anti-pattern killer in industry, where UI/front-end becomes a god object. Code sampling supports this: `api/routes/ux.py` is only an HTTP adapter — `MissionUXService` is called but does not evaluate policy/approval; it only orchestrates. It does not hold credentials. Correct.

### A3. Single canonical execution path (M9)
- UI → `/ux` → `MissionUXService` → `ApprovalGate` → mission runner → connector → real effect.
- "No second executor" — explicit, enforced in code comments and tests.
- In contrast to frameworks where AI can directly call tools, SAM gates at a single point: deterministic, auditable.

### A4. M14 fail-closed semantics for auto-approval
- `AuthoritySource.OWNER | ENTRUSTMENT | NONE` — authority always points to a human, not learned.
- `requires_human_approval=True` → never auto-approves.
- This is a mature stance — most "autonomous agents" default to auto-approval with weak safety rails.

### A5. Capabilities as universal language (Article III + CAPABILITY_SPECIFICATION)
- Identifies `<domain>.<category>.<capability>` (e.g. `memory.lookup`).
- Implementation-independent, versioned, discoverable, certifiable.
- Aligns with the Registry pattern (Article IV) — Citizens discover via capability, not direct import.
- A sound foundation for multi-provider, multi-model, multi-runtime.

### A6. Specification freeze declaration
- `docs/SPECIFICATION_FREEZE.md` + specs in `docs/specifications/`.
- Specs are contracts; not living documents. Changes require a new ADR.
- Clear separation of decision (ADR) vs contract (spec). Good.

### A7. Spec → Implementation traceability
- 4 runtime suite tests in `tests/{knowledge,memory,policy,workflow,artifact,audit,mission,execution}_runtime/` + unit + e2e.
- 4,017 baseline tests passing. Coverage is measurable; regression is trackable.

---

## B. Concerns / Gaps

### B1. "Citizen equality" (Article X) is more rhetorical than enforced
**Observation:** Article X states "Runtime is not superior to Provider. Agent is not superior to Workflow. All Citizens obey identical constitutional rules."

**But in code:** `runtime_service/`, `execution_runtime/`, `runtime_service/wiring.py` (composition root), and approval_gate all live in the Runtime layer. `Provider` is only an adapter in the connector layer. Architecturally, Provider is clearly below Runtime. Article X violation, or is the Citizen definition shifting in practice?

**Recommendation:** Either:
- (a) Acknowledge that "equality" means "same constitutional rights", not "same power" — and make this explicit in the Glossary or Constitution; or
- (b) Add a runtime-level conformance test proving all Citizen types pass through the same governance path (same approval gate, same audit, same capability discovery).

### B2. Ward (M13) breaks Citizen equality OR Citizen definition is under-specified
**Observation:** M13 (Aug 14) — Ward = external subject (GitHub repo, Windows PC, file). `docs/foundation/CITIZEN_SPECIFICATION.md` defines Citizen as "autonomous constitutional participant capable of interacting with the SAM Governance System through standardized contracts."

Ward is not a constitutional participant — it is an entrustment subject. ATLAS states "Ward = external entity entrusted to SAM (observe/protect/govern)." But in implementation, Ward often has its own adapter, identity, and governance module (`src/sam/ward/{adapters,capability,entrustment,governance,identity,registry}`).

**Question:** Is Ward actually a new Citizen type added without spec, OR does the Citizen definition need amendment? Currently "Citizen" implicitly means "internal", while Ward = "external Citizen" — this needs an official clarification.

### B3. ApprovalGate exists in two places
**Observation:**
- `src/sam/execution_runtime/approval_gate.py` — `class ApprovalGate`, returns `ApprovalDecision` (immutable DTO).
- `src/sam/application/ux/approval.py` — `class ApprovalCoordinator` (used by `MissionUXService`).

Is this intentional layering (Application coordinator vs. canonical gate)? Or is there a hidden second path?

**Recommendation:** Read both files and check for a test proving "if Application bypasses the canonical gate, the system fails closed." If yes, document it. If no, this is a potential Article V violation.

### B4. 99 sub-packages under `src/sam/` is an organisational risk
**Observation:** 99 sub-packages, categorized in ATLAS as "world / 4.0 / 5.x / M14 / application / api / legacy / backlog / infra". ATLAS states "folder ≠ semantic identity" — good, **but**:
- 8 folders are in **backlog** (`agent/`, `intelligence_runtime/`, `connectors/`, `orchestrator/`, `skills/`, `model_runtime/`, `patterns/`, `providers/`). They exist on the filesystem but **must not be activated**.
- How many engineers will see the `connectors/` folder and try to import it without knowing it is backlog? Without tooling enforcement (e.g. a lint rule blocking imports from `backlog/`), this is a risk.
- **Recommendation:** Add a "No-Import-From-Backlog" lint rule in CI. Alternatively, rename `backlog/` to `_backlog_DO_NOT_IMPORT/` as a visual cue.

### B5. "Canonical" vs "Real" naming inconsistency in execution_runtime
**Observation:** Under `src/sam/execution_runtime/`:
- `canonical_ai_bridge.py`, `canonical_browser_connector.py`, `canonical_db_connector.py`, ...
- `real_harness.py`, `real_credential_remediation.py`, `real_pdf_investigation.py`, ...

Are `canonical_*` and `real_*` two different generations? Is one of them legacy? It is unclear from the structure.

**Recommendation:** Audit the naming. If `canonical_*` is a wrapper and `real_*` is the implementation, document it. If they are from different generations, mark them (e.g. `legacy_real_*.py` or move to `legacy/execution_runtime/`).

### B6. Approval bottleneck at scale
**Observation:** Article V: "Nothing executes before explicit approval." M14: auto-approval is only from Entrustment. For routine missions (e.g. health check, log rotation, credential rotation), will a human really approve every time? Or does the Entrustment pattern become a workaround?

**Design questions:**
- Is there a notion of "trusted, recurring operations" — Entrustment once per category, not per-invocation?
- What is the end-to-end latency cost (UI → /ux → ApprovalGate → mission → connector → real effect)?
- Is there an M14 case study — 1 week of operations with active Entrustment — that measures this?

### B7. Constitution = 16 Articles, ~680 lines. Is it read?
**Observation:** The Constitution is a coherent, well-structured document. But 680 lines, in a highly structured format (Principle/Meaning/Architectural Impact/Supported Decisions/Violations), is **not a document read once — it must be internalized by every contributor.**

**Recommendation:**
- Keep the Constitution as the canonical source.
- But create a "SAM Constitution in 5 minutes" summary or a visual onboarding card.
- Each violation pattern should have a test (see B8).

### B8. "Violations" in the Constitution have no automated test
**Observation:** Each Article in the Constitution has a "Violations" section. For example, Article V: "Automatic execution after reasoning." But:
- No test in `tests/` is named `test_constitution_*.py` or `test_article_*.py`.
- No linter detects "presentation layer holds business logic" or "runtime directly imports another runtime".

**Recommendation:**
- A `tests/constitution/` suite with at least one test per Article (ideally enforced as code).
- Or a `scripts/validation/constitution_check.py` that statically analyzes code patterns.

### B9. "Provider agnostic" is more aspirational in M9
**Observation:** Article VIII: "SAM belongs to no provider." M9 actual implementation has `RealGithubConnector`, `RealBrowserConnector`, `RealHttpConnector`, `canonical_email_connector.py`, `canonical_db_connector.py`. These **are** provider-specific implementations.

**However:** The important part is that the **governance path** is agnostic. Connectors are only pluggable adapters, replaceable without changing approval/audit.

**Recommendation:** Article VIII may need clarification: "Provider agnostic" means governance logic is agnostic, NOT "no provider code exists." In fact, much provider code exists.

### B10. M14 vocabulary density
**Observation:** M14 introduces: `AuthoritySource`, `AuthorityVerdict`, `DelegationGrant`, `Entrustment`, `AutonomyLevel`, `ScopedAutonomy`, `AutomaticEscalation`, `AutonomousRecoveryLoop`, `AutonomousAuthority` — all under `src/sam/delegated_authority/`. **8 new concepts in one sprint.**

This may be necessary, but the onboarding cost is high. And Article X (citizen equality) now confronts these 8 concepts, all of which are run. M14 may need a new glossary entry or a dedicated documentation page.

---

## C. Specific Design Tensions Requiring Clarification

| # | Tension | Manifestation | Clarification question |
|---|---|---|---|
| 1 | Citizen equality vs Runtime privilege | Article X vs `runtime_service/` as composition root | Is equality limited to constitutional rights, not architectural power? |
| 2 | Ward as new Citizen vs Citizen = internal | M13, `ward/` package | Is Ward an "external Citizen" that needs to be specified? |
| 3 | Single ApprovalGate vs Application has Coordinator | `approval_gate.py` vs `application/ux/approval.py` | Is there a test proving Application does not bypass the canonical gate? |
| 4 | Universal capability language vs Citizens knowing each other | Article III vs code reality | Is there a test in `citizen/registry/` proving runtime discovery does not direct-import? |
| 5 | Provider agnostic vs Real connectors | Article VIII vs `canonical_*_connector.py` | Does "agnostic" mean governance-agnostic, not "no provider code"? |
| 6 | Evolution by extension vs 99 sub-packages | Article XIII vs filesystem reality | Do backlog folders have enforcement (lint/CI)? |

---

## D. Areas Not Yet Explored (Requires Further Investigation)

- **Approval Pipeline detail** (`execution_runtime/approval_pipeline.py`) — is `ApprovalCoordinator` there or in Application?
- **Citizen Registry implementation** (`citizen/registry/`) — is the Registry actually used, or do Citizens still direct-import?
- **Mission UX state machine** (`application/ux/state.py`) — what is the full set of state transitions?
- **Composition root** (`api/wiring.py`) — what does the DI graph look like; are there circular references?
- **Capability Provider registry** (`environment/providers.py`) — M14 environment-adaptive Option B: is this runtime-loaded or static?
- **Test for Article XVI (presentation principle)** — is there a test in `tests/api/` or `tests/presentation/` proving routes do not hold business logic?
- **ADR-001 through 009** — titles read; contents need review for trade-off decisions.

---

## E. Recommended Next Investigation Order

If further exploration is desired, the following order is most impactful:
1. **Deep-dive `application/ux/approval.py` vs `execution_runtime/approval_gate.py`** — is there a single source of truth for approval, or a second path? Critical for Article V.
2. **Review `api/wiring.py`** — composition root, DI graph.
3. **Review `citizen/registry/` + `citizen/discovery/`** — is the Registry used or mere decoration?
4. **Review ADR-001..009** — what decisions were made, what trade-offs were taken.
5. **Review `tests/constitution/` (if any)** or grep tests for Constitution-related tests.
6. **Review `environment/pipeline.py`** — M14 environment-adaptive: is it running or still design-only?

Or, if a more specific focus is preferred, it can be directed.

---

*— External Design Review, 2026-08-15*
