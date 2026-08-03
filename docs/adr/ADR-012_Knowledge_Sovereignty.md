# ADR-012 — Knowledge Sovereignty (PUBLIC/INTERNAL/RESTRICTED)

**Version:** 1.0.0
**Status:** Accepted
**Decision Date:** Sprint 31
**Author:** SAM Architecture
**Reviewers:** (recorded during migration from ARCHITECTURAL_DECISIONS.md)
**Related ADRs:** ADR-011 (Trust-Based Federation)
**Related Documents:** SAM_ARCHITECTURE.md, CONSTITUTION.md, MEMORY_MODEL.md
**Related Modules:** `src/sam/federation/sovereignty.py`

---

# Purpose

Define how clusters control which knowledge they are willing to share with other peers.

# Context

Not all clusters want to share all knowledge. Different knowledge has different
sensitivity, and sharing decisions must respect each cluster's autonomy.

# Problem Statement

Provide a tiered sovereignty model so that clusters can classify knowledge by
sharing scope while keeping control over restricted content.

# Decision Drivers

- Respecting cluster autonomy
- Supporting multi-tenant deployments
- Granular control over restricted content
- Simplicity of classification

# Alternatives Considered

## Alternative A — All-Share (No Sovereignty)

### Advantages
- Simplest model

### Disadvantages
- Ignores cluster autonomy
- Unsafe for sensitive knowledge

### Assessment
Rejected: unacceptable for multi-tenant scenarios.

---

## Alternative B — Three-Tier Sovereignty with Optional Whitelist (selected)

### Advantages
- Respects cluster autonomy
- Supports multi-tenant deployments
- Optional whitelist for RESTRICTED content

### Disadvantages
- Requires explicit classification of knowledge
- Whitelist must be maintained

### Assessment
Selected: matches SAM's autonomy and safety principles.

---

# Decision

Use a **three-tier knowledge sovereignty model — PUBLIC / INTERNAL / RESTRICTED —**
with an optional whitelist for RESTRICTED content. Clusters decide per knowledge
item which tier applies.

**Status: ✅ Implemented** — implemented as `src/sam/federation/sovereignty.py`
("Knowledge Sovereignty — Sprint 31"; includes `POLICY_PUBLIC`, `POLICY_INTERNAL`,
`POLICY_RESTRICTED` constants and a `SovereigntyPolicy` dataclass, with cluster-based
sharing policies).

# Architectural Rationale

Three-tier sovereignty balances sharing against control, respects each cluster's
autonomy, and is necessary for multi-tenant deployments. The optional whitelist
provides fine-grained control for the most sensitive tier.

# Consequences

## Positive
- Autonomous sharing decisions per cluster
- Fine-grained control for restricted content
- Enables multi-tenant deployments

## Negative
- Knowledge items must be classified
- Whitelist maintenance overhead for RESTRICTED items

## Accepted Trade-offs
- Sovereignty classification is a policy decision, not automatic.

---

# Impact Analysis

- **Framework:** adds a sovereignty layer within federation.
- **Modules:** `federation/sovereignty.py`.
- **Documentation:** MEMORY_MODEL.md remains the conceptual reference.

# Dependency Impact

Introduces no new external dependency. Federation sovereignty lives within `src/sam/federation/`.

# Risk Assessment

| Dimension | Assessment |
|------------|------------|
| Probability | Low |
| Impact | Low-Medium |
| Recoverability | High |
| Blast Radius | Federation peers only |
| Reversibility | High |

---

# Trust Assessment

Evidence: implemented and tested in `src/sam/federation/sovereignty.py`.
Confidence: High.
Unknowns: evolution of classification rules across deployments.

---

# Implementation Notes

Reference implementation: `src/sam/federation/sovereignty.py` (docstring: "Knowledge Sovereignty — Sprint 31").
Enumerates `POLICY_PUBLIC`, `POLICY_INTERNAL`, `POLICY_RESTRICTED` with cluster-based sharing policies.

# Migration Strategy

No migration required; decision already implemented.

# Success Criteria

Clusters can independently classify knowledge into the three tiers and enforce
sharing restrictions per policy.

# Future Reassessment

Reassess if federation is extended to more granular or dynamic knowledge-sharing policies.

---

# Related Documents

- SAM_ARCHITECTURE.md
- MEMORY_MODEL.md
- ADR-011 (Trust-Based Federation)

---

# Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| (migrated) | SAM Architecture | Accepted |

---

# Author Checklist

- [x] Problem clearly defined
- [x] Alternatives documented
- [x] Decision justified
- [x] Trade-offs documented
- [x] Risks evaluated
- [x] Trust assessment completed
- [x] Related documents referenced
- [x] Terminology follows GLOSSARY.md
- [x] Consistent with CONSTITUTION.md

---

# Common Mistakes

N/A — this ADR documents an existing implemented decision.

---

# Completion Checklist

- [x] Metadata complete
- [x] Cross references validated
- [x] Review completed
- [x] Status updated
- [x] Ready for repository publication
