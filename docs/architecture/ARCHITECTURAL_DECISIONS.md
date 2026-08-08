# Architectural Decisions — Reference Index

**Version:** 2.0.0
**Status:** REFERENCE (index only — NOT authority)
**Purpose:** A single index over all Architecture Decision Records (ADRs). It does **not**
contain unique decisions. Each decision lives in exactly one canonical ADR file under
`docs/adr/`. This index maps every ADR to its file and status.

> **Canonical rule (from Van):** *Satu keputusan = Satu ADR = Satu sumber kebenaran.*
> If a decision is active, it MUST have a file in `docs/adr/`. This index never holds
> a decision that lives nowhere else.

---

## ADR Index

| ADR | Decision | Status | Canonical file |
|-----|----------|--------|----------------|
| ADR-000 | Deployment Topology | Accepted | `docs/adr/ADR-000_Deployment_Topology.md` |
| ADR-001 | Approval Decision Model | Accepted | `docs/adr/ADR-001_Approval_Decision_Model.md` |
| ADR-002 | Capability Resolution Policy | Accepted | `docs/adr/ADR-002_Capability_Resolution_Policy.md` |
| ADR-003 | Idempotency Realization Model | Accepted | `docs/adr/ADR-003_Idempotency_Realization_Model.md` |
| ADR-004 | Failure Propagation Model | Accepted | `docs/adr/ADR-004_Failure_Propagation_Model.md` |
| ADR-005 | Execution Ordering Model | Accepted | `docs/adr/ADR-005_Execution_Ordering_Model.md` |
| ADR-006 | External Access Boundaries | Accepted | `docs/adr/ADR-006_External_Access_Boundaries.md` |
| ADR-007 | Verification Point Placement | Accepted | `docs/adr/ADR-007_Verification_Point_Placement.md` |
| ADR-008 | Consolidated Runtime & Platform Architecture Decisions | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` |
| ADR-009 | Goal Arbitration — Weighted Scoring | **Superseded** | (no canonical file — superseded) |
| ADR-010 | Five-Level Autonomy Model | **Superseded** | (no canonical file — superseded) |
| ADR-011 | Trust-Based Federation (Not Identity-Based) | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-012 | Knowledge Sovereignty (PUBLIC/INTERNAL/RESTRICTED) | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-013 | Python 3.8+ Compatibility (with Polyfill) | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-014 | CLI-First Interaction Model | **Superseded** | (no canonical file — superseded) |
| ADR-015 | Runtime Hosting Independence | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-016 | Headless Runtime | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-017 | Runtime State Machine | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-018 | Workspace Layout | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-019 | Recovery Contract | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-020 | Lifecycle Events | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-021 | Overall Architecture | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-022 | Runtime Isolation | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-023 | Immutable DTO | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-024 | Preview Only Execution | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-025 | Approval Boundary | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-026 | Subsystem Independence | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-027 | Repository Structure | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |
| ADR-028 | Runtime Kernel | **Accepted** | `docs/adr/ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` *(consolidated into ADR-008)* |

---

## Superseded / Obsolete Decisions

The following decisions are recorded historically but are **no longer active**.
They were superseded or proved obsolete by later architecture. Their rationale is
preserved in git history (previous version of this index) for forensics only.

| ADR | Original decision | Why superseded/obsolete |
|-----|-------------------|--------------------------|
| ADR-009 | Goal Arbitration Weighted Scoring | Replaced by ADR-005 Strict Linear Ordering (approval-arrival order, deterministic `ordering_validator.py`). No weighted-scoring arbitration remains. |
| ADR-010 | Five-Level Autonomy (OBSERVE→...→AUTONOMOUS) | Replaced by approval-gated execution: "Nothing executes before explicit approval" (SAM_ARCHITECTURE). No autonomy scale remains. |
| ADR-014 | CLI-First (no GUI, no REST) | Obsolete: SAM now has a Presentation layer (`src/sam/presentation/`) + web templates; CLI-first constraint is no longer held. |

---

## How to read this index

1. To find the authority for any architectural topic, start at the **CANONICAL** ADR
   listed above, then follow `docs/adr/<file>`.
2. Active decisions live **only** in `docs/adr/`.
3. Superseded/obsolete decisions are historical; never implement from them.
4. Full architecture authority: `docs/architecture/SAM_ARCHITECTURE.md`.
5. Navigation across all repository documents: `ATLAS.md` (root).

---

## Migration note

This file previously held full ADR bodies for ADR-001..014. Under the
one-decision-one-ADR rule, the active decisions ADR-011/012/013 were extracted to
standalone canonical files in `docs/adr/` (Phase C0.5). The remaining non-canonical
bodies (ADR-001..007, 014) were superseded/obsolete or already represented by the
canonical ADR set, and their details are preserved in git history.

## Consolidation note

Under the one-decision-one-ADR rule, the active Runtime/Platform decisions (ADR-011..013, ADR-015..028) were consolidated into a single canonical baseline `ADR-008_Consolidated Runtime & Platform Architecture Decisions.md` (Decision Authority: Chief Architect). Their individual historical files are preserved in git history.
