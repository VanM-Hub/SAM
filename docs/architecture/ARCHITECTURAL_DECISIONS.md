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

This file was previously `v1.0.0` and held full ADR bodies for ADR-001..014. Under the
one-decision-one-ADR rule, the active decisions ADR-011/012/013 were extracted to
standalone canonical files in `docs/adr/` (Phase C0.5). The remaining non-canonical
bodies (ADR-001..007, 014) were superseded/obsolete or already represented by the
canonical ADR set, and their details are preserved in git history.
