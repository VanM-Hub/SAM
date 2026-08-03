# SAM Architecture

**Version:** 1.0
**Status:** Canonical
**Authority:** Derived from the Constitution; realizes Governance
**Canonical:** true
**Scope:** Architecture defines how Governance is realized as a system (structure, layers, dependencies, responsibilities, interactions, and deployment abstraction) for Project SAM.
**Owner:** Project SAM
**Depends On:**
- MISSION
- CONSTITUTION
- PHILOSOPHY
- GOVERNANCE
- GLOSSARY
- Model Layer (TRUST_MODEL, RISK_MODEL, DECISION_MODEL, MEMORY_MODEL)

> **Canonical via Canonical Promotion Protocol (AD-028, Stage 4).**
> This document is the single authoritative source for the Architecture of Project SAM.
> Earlier architecture documents (`ARCHITECTURE.md`, `SAM_ARCHITECTURE_MASTER.md`) are superseded / historical and are archived under `docs/history/architecture/`.

---

## Scope Statement

Architecture defines how Governance is realized as a system: the structure, layers, dependencies, responsibilities, and interactions of SAM, and the abstraction across deployment platforms.

Architecture does not define the Mission, the Constitution, or Governance. It depends on them.

Architecture explains how components are arranged, how responsibilities are separated, and how long-term evolution is preserved.

---

## Dependency Direction

SAM is layered. Each layer depends only on the layers above it and on the Foundation (Identity, Governance, Model Layer).

```
MISSION
 ↓
CONSTITUTION
 ↓
PHILOSOPHY
 ↓
GOVERNANCE
 ↓
MODEL LAYER
 ↓
ARCHITECTURE
 ↓
(implemented by Runtime, Citizens, Providers, Connectors)
```

Architecture never depends on README, ROADMAP, ADR, or implementation details.

---

## The Architectural Unit: Citizen

The fundamental architectural unit of SAM is the **Citizen**: a constitutional participant that publishes Capabilities, obeys Contracts, participates in Governance, and remains auditable.

A Citizen is the modern realization of the older "Module", "Protected Object", and "Component" concepts.

Every Citizen owns one bounded governance responsibility.

---

## Architectural Layers

SAM is organized into layers of responsibility. Each layer has one primary responsibility.

### Layering Model

At the architectural (realization) level, the system is arranged so that:

```
Governance (authority)
 ↓
Model Layer (reasoning behavior)
 ↓
Architecture (structure)
 ↓
Citizens / Runtimes (capability units)
 ↓
Providers / Connectors (external access)
 ↓
Presentation (human interface)
```

Layers communicate only through Contracts and Capability-based discovery (Registry), never through implementation knowledge.

---

## Responsibility Matrix

| Architectural element | Responsibility | Must not |
|---|---|---|
| Mission | Purpose of existence | Implementation |
| Constitution | What must never change | Evolution of identity |
| Governance | How authority is allocated | Definition of identity |
| Model Layer | Explain operational behavior | Redefine identity |
| Runtime | Govern one bounded capability domain | Take strategic decisions |
| Citizen | Be a governed constitutional participant | Possess architectural privilege |
| Provider / Connector | Implement external access / communication | Exercise governance |
| Presentation | Visualize / configure / approve / observe | Contain business logic |
| Execution | Apply an approved decision | Act without approval |

---

## Approved Execution Flow (Golden Rule, modernized)

Every operational change follows the approved sequence, derived from Governance and Mission:

```
Mission → Governance check → Approval → Execution → Verification → Audit
```

Nothing executes before explicit approval. Execution is intentional.

---

## Platform Independence

SAM belongs to no platform and no provider.

Windows, Linux, Docker, Kubernetes, and embedded runtimes are hosting adapters.

Providers (including AI providers) are replaceable implementations.

Platform knowledge lives in adapters, never in the core.

---

## Knowledge, Memory, Reasoning

Knowledge and Memory are governed operational resources consumed by reasoning.

They are not sources of governance. They evolve independently from reasoning.

---

## Contract and Registry

All collaboration between Citizens occurs through immutable Contracts.

Citizens discover one another through the Registry (Capability-based), never through direct implementation dependency.

---

## Design Principles

SAM architecture follows these principles, inherited from the Foundation:

- Framework-before-implementation (realized: Model Layer / Runtime before platform code)
- Composition-before-coupling (Capability-based collaboration)
- Knowledge-before-automation
- Documentation-before-implementation
- Citizen-modules-before-monolith
- Evidence-before-assumption
- Human-before-automation
- Retire terminology, preserve meaning (AP-010)

---

## Architectural Stability and Evolution

Architecture changes slowly. Implementation changes commonly. Knowledge changes continuously.

New capabilities are introduced by extension — adding Citizens, Runtimes, or Connectors — not by modifying the architectural core.

The identity of SAM outlives every implementation.

---

## Historical Lineage (recorded, not erased)

The architecture of SAM is the result of an unbroken conceptual evolution. Key predecessors:

- **Framework → Model Layer** (reasoning concepts became the Model Layer)
- **Runtime Kernel → Runtime** (execution capability kernel became the Runtime)
- **Modules / Protected Objects → Citizen** (external modules and protected units became constitutional Citizens)
- **Playbooks → Workflow** (repeatable procedures became Workflow)
- **Automation → Execution** (automated action became approval-gated Execution)
- **Operations Layer → Presentation** (operator-facing layer became Presentation)
- Earlier documents that captured this evolution — the framework-oriented and the guardian-runtime-oriented architecture sketches — remain as historical artifacts of this lineage.

This lineage shows that SAM evolved by semantic continuity, never by architectural reboot.
