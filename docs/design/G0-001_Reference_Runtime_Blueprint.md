# G0-001 — Reference Runtime Blueprint

**Version:** 1.0
**Status:** Blueprint (Read-only architecture design — not an implementation)
**Authority:** Derived from the Foundation; derives from the Canonical Architecture; realizes the Specification Layer.
**Owner:** Project SAM
**Mode:** Read-only architecture design. No technology, language, concurrency pattern, database, serialization format, or transport mechanism is selected or mandated.
**Depends On:**
- MISSION
- CONSTITUTION
- PHILOSOPHY
- GOVERNANCE
- GLOSSARY
- Model Layer (TRUST_MODEL, RISK_MODEL, DECISION_MODEL, MEMORY_MODEL)
- Canonical Architecture (SAM_ARCHITECTURE.md)
- Specification Layer (CITIZEN, CAPABILITY, REGISTRY, CONTRACT, APPROVAL, EXECUTION, AUDIT)

> This blueprint is a **realization design** built strictly from the frozen baseline.
> It introduces **no new rule, no new authority, and no new domain**.
> Every component below exists solely to make observable the behavior already defined by the Architecture and the Specification Layer.
> It is **not** an ADR and does **not** decide technology.

---

## Scope Statement

This blueprint identifies the **conceptual components** of a Reference Runtime that make real the chain:

```
Citizen → Capability → Registry → Contract → Approval → Execution → Audit
```

It assigns a **responsibility** to each component, describes the **interactions** between components, and draws the **boundary** of each responsibility — all without choosing implementation.

This blueprint **does not**:
- Create classes, interfaces, APIs, payloads, algorithms, or pseudocode.
- Select technology, programming language, concurrency pattern, database, serialization format, or transport.
- Create a new ADR.
- Modify the Foundation, the Canonical Architecture, or the Specification Layer.

Any design decision that requires a trade-off is recorded below as a **Candidate ADR** without being resolved.

---

## 1. Runtime Component Map

A Reference Runtime is composed of conceptual components. Each component owns one bounded responsibility derived from one or more frozen documents. Components are named by their responsibility, not by any technology.

| # | Component | Derives From | Primary Responsibility |
|---|---|---|---|
| 1 | **Citizen Host** | Citizen Spec, Canonical Architecture | Host and govern Citizens; own Citizen lifecycle; respect Citizen's bounded governance responsibility |
| 2 | **Capability Manager** | Capability Spec | Own Capability lifecycle; keep Capability as the universal language; survive implementation replacement |
| 3 | **Discovery Resolver** | Registry Spec | Discover and resolve Capabilities on request; return the Capability that satisfies a request |
| 4 | **Contract Enforcer** | Contract Spec, Constitution | Own immutable Contracts; enforce compatibility and version negotiation between interacting Citizens |
| 5 | **Approval Coordinator** | Approval Spec | Coordinate the Approval process; observe and expose Approval lifecycle and decision |
| 6 | **Execution Scheduler** | Execution Spec | Sequence and apply approved operations; observe Execution lifecycle, result, and idempotency |
| 7 | **Audit Recorder** | Audit Spec | Transform operational activity into evidence; preserve traceability from Audit back through the chain |

Each component is a **responsibility container**, not an implementation unit. One component may be realized by zero, one, or many technical modules — that is an implementation decision outside this blueprint.

---

## 2. Responsibility Matrix

| Component | Is Responsible For | Must Not (Boundary) |
|---|---|---|
| **Citizen Host** | Governing Citizens; publishing Capabilities; obeying Contracts; remaining auditable | Possess architectural privilege; take strategic decisions; redefine identity |
| **Capability Manager** | Owning Capability lifecycle; preserving Capability's universal meaning | Redefine Capability semantics; couple to a specific implementation |
| **Discovery Resolver** | Making Capabilities discoverable; resolving a request to a Capability | Store implementation; own identity; redefine Citizen/Capability/Contract |
| **Contract Enforcer** | Owning immutable Contracts; enforcing compatibility & version negotiation | Redefine Capability; decide Approval; perform Execution |
| **Approval Coordinator** | Coordinating the Approval decision; exposing lifecycle & failure | Compute the decision algorithm (spec does not prescribe it); execute anything |
| **Execution Scheduler** | Applying approved operations; sequencing; honoring idempotency | Act without approval; perform verification or audit itself |
| **Audit Recorder** | Turning activity into evidence; preserving traceability | Decide, execute, or govern; invent meaning |

### Responsibility Ownership (one domain / one owner)

| Domain | Owning Component |
|---|---|
| Citizen membership & identity | Citizen Host |
| Universal capability language | Capability Manager |
| Discovery & resolution | Discovery Resolver |
| Structure of interaction | Contract Enforcer |
| Authorization | Approval Coordinator |
| Performance of approved action | Execution Scheduler |
| Recording / traceability | Audit Recorder |

---

## 3. Interaction Flow (Conceptual)

A single operational interaction follows the frozen "Approved Execution Flow" (Golden Rule, modernized) from the Canonical Architecture:

```
Mission → Governance check → Approval → Execution → Verification → Audit
```

Instantiated at the component level:

```
  1. Citizen Host        — a Citizen wants to reach another's Capability
  2. Discovery Resolver  — resolves the request to a matching Capability
  3. Capability Manager  — confirms the Capability is available (lifecycle state)
  4. Contract Enforcer   — supplies the immutable Contract governing the interaction
  5. Approval Coordinator— coordinates authorization of the operation (None executes before approval)
  6. Execution Scheduler — applies the approved operation (only after Approved)
  7. Audit Recorder      — turns the execution into evidence, chained back to the rest
```

The conceptual data flow between components is **responsibility references**, not technical payloads:

```
[Citizen Host] → [Discovery Resolver] → [Capability Manager] → [Contract Enforcer]
                                                                      ↓
      [Audit Recorder] ← [Execution Scheduler] ← [Approval Coordinator]
```

Traceability is preserved **backward**: Audit → Execution → Approval → Contract → Capability → Citizen, with no broken link.

---

## 4. Dependency Diagram

Components depend only toward their frozen source of truth. No component depends on the one below it in a way that creates a cycle.

```
Citizen Host
   ↓
Capability Manager
   ↓
Discovery Resolver
   ↓
Contract Enforcer
   ↓
Approval Coordinator
   ↓
Execution Scheduler
   ↓
Audit Recorder
```

- Every component depends on the Canonical Architecture and the Constitution as its authority.
- Every component depends operationally only on components that appear earlier in the chain (the one "above" it).
- **No cycle.** The dependency direction is single and linear, matching the Specification chain (Citizen → Capability → Registry → Contract → Approval → Execution → Audit).
- Audit is the terminal recorder; it observes the others and does not feed back a dependency they rely on for their own authority.

---

## 5. Candidate ADR Register

The following design decisions emerged during this blueprint and **require a trade-off decision**. They are recorded as **candidates only**; per the directive they are **not resolved** here and **must not** be added to any frozen document.

| # | Candidate ADR | Design Question | Left Open |
|---|---|---|---|
| C-01 | **Concurrency & ordering model** | How the Execution Scheduler sequences concurrent approved operations without violating Contract immutability or Approval ordering | Trade-off between strict ordering and operational throughput |
| C-02 | **Capability resolution policy** | How the Discovery Resolver chooses when multiple Capabilities satisfy one request (exact match vs. version-compatible match) | Trade-off between precision and availability |
| C-03 | **Approval decision computation** | How the Approval Coordinator produces a decision (this is explicitly not prescribed by the Approval Specification) | Trade-off between automated and human-mediated authorization |
| C-04 | **Idempotency realization** | How an operation's idempotency property is made observable without a mandated technical mechanism | Trade-off between explicit idempotency keys and operation-defined semantics |
| C-05 | **Failure propagation** | How a defined failure (Registry / Contract / Approval / Execution) is surfaced to the Audit Recorder while preserving traceability | Trade-off between strict propagation and graceful degradation |
| C-06 | **Runtime deployment topology** | Whether one Runtime hosts all components, or components are distributable across Runtimes / hosts | Trade-off between single-runtime simplicity and multi-runtime distribution |
| C-07 | **Reference boundaries to external access** | Where the Runtime positions Providers / Connectors (external access) relative to the chain | Trade-off between isolation and integration ease |
| C-08 | **Verification point placement** | Where "Verification" in the Golden Rule flow sits as a conceptual step and which component observes it | Trade-off between verification inside Execution and verification as a separate observer |

> **Register policy:** none of C-01…C-08 is decided here. Each is a candidate to be turned into a formal ADR **only** at the point an implementation-facing decision must be made, and each such ADR must not contradict the frozen baseline.

---

## 6. Gap Analysis

The frozen documents provide sufficient authority and behavior for the conceptual Runtime. The following are **deliberate non-gaps** (documented, not to be "fixed" by changing the baseline) and one **structural note**:

### Deliberate non-gaps (resolvable at ADR / implementation, not by spec change)

| Observation | Status | Why it is not a defect |
|---|---|---|
| Descriptor / payload / encoding format is non-deterministic across specs | Documented | Intentionally left to ADR/implementation; does not block two independent runtimes from interoperating behaviorally |
| Health & Certification are conceptual only | Documented | Defined at the concept level; concrete mechanism is an implementation/ADR concern |
| Approval decision computation not prescribed | Documented | Explicitly out of scope of the Approval Specification; a Candidate ADR (C-03) |
| Idempotency mechanism not mandated | Documented | Explicitly a property of the operation under its Contract; a Candidate ADR (C-04) |

### Structural note (housekeeping, not a blocker)

| Area | Note |
|---|---|
| Specification residence | The Citizen Specification currently resides at `docs/CITIZEN_SPECIFICATION.md` (outside `docs/specifications/`) while the other six reside in `docs/specifications/`. This was already recorded during the Stabilization Review as a cosmetic location inconsistency and does not affect the behavior described here. |

---

## 7. Final Statement

This blueprint realizes, at a conceptual level, the full chain **Citizen → Capability → Registry → Contract → Approval → Execution → Audit** using only the responsibilities already present in the frozen Foundation, Canonical Architecture, and Specification Layer.

It introduces **no new authority, no new domain, and no implementation**. It records **eight Candidate ADRs** that remain open for a future, separate decision step.

The Reference Runtime can therefore be built from this blueprint **without modifying any frozen document**, confirming that the Foundation, Architecture, and Specification of Project SAM are realizable as a runtime.
