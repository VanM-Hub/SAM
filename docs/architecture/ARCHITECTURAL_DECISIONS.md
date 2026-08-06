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
| ADR-008 | Attention Manager Priority Rules | **Superseded** | (no canonical file — superseded) |
| ADR-009 | Goal Arbitration — Weighted Scoring | **Superseded** | (no canonical file — superseded) |
| ADR-010 | Five-Level Autonomy Model | **Superseded** | (no canonical file — superseded) |
| ADR-011 | Trust-Based Federation (Not Identity-Based) | Accepted | `docs/adr/ADR-011_Trust_Based_Federation.md` |
| ADR-012 | Knowledge Sovereignty (PUBLIC/INTERNAL/RESTRICTED) | Accepted | `docs/adr/ADR-012_Knowledge_Sovereignty.md` |
| ADR-013 | Python 3.8+ Compatibility (with Polyfill) | Accepted | `docs/adr/ADR-013_Python_38_Compatibility.md` |
| ADR-014 | CLI-First Interaction Model | **Superseded** | (no canonical file — superseded) |
| ADR-015 | Runtime Hosting Independence | Accepted | `docs/adr/ADR-015_Runtime_Hosting_Independence.md` |
| ADR-016 | Headless Runtime | Accepted | `docs/adr/ADR-016_Headless_Runtime.md` |
| ADR-017 | Runtime State Machine | Accepted | `docs/adr/ADR-017_Runtime_State_Machine.md` |
| ADR-018 | Workspace Layout | Accepted | `docs/adr/ADR-018_Workspace_Layout.md` |
| ADR-019 | Recovery Contract | Accepted | `docs/adr/ADR-019_Recovery_Contract.md` |
| ADR-020 | Lifecycle Events | Accepted | `docs/adr/ADR-020_Lifecycle_Events.md` |
| ADR-021 | Overall Architecture | Accepted | `docs/adr/ADR-021_Overall_Architecture.md` |
| ADR-022 | Runtime Isolation | Accepted | `docs/adr/ADR-022_Runtime_Isolation.md` |
| ADR-023 | Immutable DTO | Accepted | `docs/adr/ADR-023_Immutable_DTO.md` |
| ADR-024 | Preview Only Execution | Accepted | `docs/adr/ADR-024_Preview_Only_Execution.md` |
| ADR-025 | Approval Boundary | Accepted | `docs/adr/ADR-025_Approval_Boundary.md` |
| ADR-026 | Subsystem Independence | Accepted | `docs/adr/ADR-026_Subsystem_Independence.md` |
| ADR-027 | Repository Structure | Accepted | `docs/adr/ADR-027_Repository_Structure.md` |
| ADR-028 | Runtime Kernel | Accepted | `docs/adr/ADR-028_Runtime_Kernel.md` |

---

## Superseded / Obsolete Decisions

The following decisions are recorded historically but are **no longer active**.
They were superseded or proved obsolete by later architecture. Their rationale is
preserved in git history (previous version of this index) for forensics only.

| ADR | Original decision | Why superseded/obsolete |
|-----|-------------------|--------------------------|
| ADR-008 | Attention Manager Priority Rules (first-match confidence→health→latency→cost) | Runtime certification (`P0-001`): "No priority mechanism in scheduler"; resolution follows compatibility + identity ordering, not priority rules. |
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
