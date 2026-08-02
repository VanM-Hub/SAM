# SAM Specification Freeze

**Version:** 1.0

**Status:** Freeze Declaration (documentative)

**Scope:** Entire Project SAM Specification Layer

**Owner:** Project SAM

---

## Declaration

Effective with this declaration, the following layers of Project SAM are **frozen**:

- **Foundation** — Mission, Constitution, Philosophy, Governance, Glossary, Canonical Architecture.
- **Specification Layer** — Citizen, Capability, Registry, Contract, Approval, Execution, Audit.

A frozen document is a **stable baseline**. It is the authoritative reference for all downstream work and may evolve only when a real architectural conflict is discovered — never for the sake of refinement.

---

## Rules

1. **Foundation is frozen.** The Constitution remains the highest authority and does not change without an amendment that never betrays the Mission.
2. **Specification is frozen.** The seven operational specifications form the canonical baseline for implementation.
3. **Evolution through ADR.** All future design decisions — descriptor formats, Approval payloads, Registry schemas, discovery algorithms, health-check mechanisms, Citizen certification, version-negotiation strategies — are expressed through **Architecture Decision Records (ADR)**, not by editing the frozen Specification.
4. **Specification changes only on real architectural conflict.** A Specification is reopened only if a decision reveals a genuine constitutional defect. Cosmetic improvement is not a reason to reopen.

---

## Why This Matters

For the past phases, SAM built its language and constitution. This declaration fixes that baseline so that implementations, Runtimes, Citizens, and Providers can be built against a stable reference.

All subsequent design decisions belong in the ADR layer. A Specification or Foundation change should be the exception, not the routine.

---

## Guidance

- Do **not** solve implementation problems by modifying the Foundation or the Specification.
- Route new design decisions through the **ADR layer**.
- Reopen a frozen document **only** when the change is required to resolve a genuine architectural or constitutional defect.

---

## Reference

- [Constitution](../docs/CONSTITUTION.md)
- [Canonical Architecture](../docs/architecture/SAM_ARCHITECTURE.md)
- [Specifications](../docs/specifications/)
- [Citizen Specification](../docs/CITIZEN_SPECIFICATION.md)
- [ADR Template](../docs/templates/ADR_TEMPLATE.md)
