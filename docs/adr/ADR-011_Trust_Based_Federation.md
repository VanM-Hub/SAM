# ADR-011 — Trust-Based Federation (Not Identity-Based)

**Version:** 1.0.0
**Status:** Accepted
**Decision Date:** Sprint 31
**Author:** SAM Architecture
**Reviewers:** (recorded during migration from ARCHITECTURAL_DECISIONS.md)
**Related ADRs:** ADR-012 (Knowledge Sovereignty)
**Related Documents:** SAM_ARCHITECTURE.md, CONSTITUTION.md, TRUST_MODEL.md
**Related Modules:** `src/sam/federation/`

---

# Purpose

Define how clusters decide which peers to trust within a federation.

# Context

SAM clusters need to determine which peers are reliable enough to interact with.
The decision must balance adaptability against the risk of trusting unreliable peers.

# Problem Statement

Choose a trust model for federation that does not depend on static identity or
pre-shared certificates, while remaining robust to unreliable or malicious peers.

# Decision Drivers

- Adaptability to changing peer behavior
- Penalizing unreliable peers automatically
- Operational safety
- Simplicity of evaluation

# Alternatives Considered

## Alternative A — Static Identity / Certificate-Based Trust

### Advantages
- Simple to reason about
- Deterministic access control

### Disadvantages
- Requires identity provisioning
- Does not adapt to behavioral change

### Assessment
Rejected: too rigid; identity does not reflect actual reliability.

---

## Alternative B — Dynamic Trust Scoring with Decay (selected)

### Advantages
- Adapts to observed behavior
- Automatically penalizes unreliable peers
- No identity provisioning required

### Disadvantages
- Requires ongoing monitoring
- Trust values drift over time

### Assessment
Selected: aligns with SAM's adaptive and auditable principles.

---

# Decision

Use **dynamic trust scoring with decay (not static identity or certificates)** to
decide which peers to trust. Trust scores adjust based on observed behavior and
automatically decay over time.

**Status: ✅ Implemented** — implemented as `src/sam/federation/trust.py`
("Trust Negotiation — Sprint 31. Trust scores per cluster with dynamic adjustment
based on historical accuracy, reliability, and behavior").

# Architectural Rationale

Dynamic scoring keeps the federation adaptive; unreliable peers are penalized
automatically without manual intervention. This preserves SAM's principle that trust
reflects governed conduct, not static identity.

# Consequences

## Positive
- Adaptive trust evaluation
- Automatic penalization of unreliable peers
- No certificate/identity provisioning

## Negative
- Trust values drift and require decay tuning
- Requires behavioral evidence to be collected

## Accepted Trade-offs
- Trust is approximate and probabilistic, not binary.

---

# Impact Analysis

- **Framework:** adds a trust-evaluation unit within federation.
- **Modules:** `federation/trust.py` and related federation modules.
- **Documentation:** TRUST_MODEL.md remains the conceptual reference.

# Dependency Impact

Introduces no new external dependency. Federation logic lives within `src/sam/federation/`.

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

Evidence: implemented and tested in `src/sam/federation/trust.py`.
Confidence: High.
Unknowns: long-term decay parameter tuning.

---

# Implementation Notes

Reference implementation: `src/sam/federation/trust.py` (docstring: "Trust Negotiation — Sprint 31").
Constants include `DEFAULT_TRUST = 0.5`, `TRUST_DECAY_RATE = 0.01` per day.

# Migration Strategy

No migration required; decision already implemented.

# Success Criteria

Peers with poor historical accuracy are automatically deprioritized; trust scores remain explainable and auditable.

# Future Reassessment

Reassess if federation is extended to multi-tenant production deployments requiring stricter trust guarantees.

---

# Related Documents

- SAM_ARCHITECTURE.md
- TRUST_MODEL.md
- ADR-012 (Knowledge Sovereignty)

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
