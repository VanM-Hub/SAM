# ADR-013 — Python 3.8+ Compatibility (with Polyfill)

**Version:** 1.0.0
**Status:** Accepted
**Decision Date:** Sprint 28
**Author:** SAM Architecture
**Reviewers:** (recorded during migration from ARCHITECTURAL_DECISIONS.md)
**Related ADRs:** (none directly)
**Related Documents:** REPOSITORY_CONVENTION.md, pyproject.toml
**Related Modules:** `src/sam/persistence/database.py`

---

# Purpose

Define the supported Python versions and how to bridge newer stdlib features for older runtimes.

# Context

The development team uses Python 3.8, but `asyncio.to_thread` was introduced in Python 3.9.
SAM must remain compatible across the supported Python range.

# Problem Statement

Provide a compatibility strategy so that code may use `asyncio.to_thread` while still
supporting Python 3.8.

# Decision Drivers

- Maximum Python compatibility
- Minimal complexity of the polyfill
- No external dependency

# Alternatives Considered

## Alternative A — Require Python 3.9+

### Advantages
- No polyfill needed
- Simplest code

### Disadvantages
- Excludes Python 3.8 environments
- Contradicts team's 3.8 baseline

### Assessment
Rejected: the team uses Python 3.8.

---

## Alternative B — Polyfill for `asyncio.to_thread` (selected)

### Advantages
- Supports 3.8–3.12
- Polyfill is trivial
- No external dependency

### Disadvantages
- Small compatibility shim to maintain

### Assessment
Selected: maximizes compatibility with minimal cost.

---

# Decision

Support **Python 3.8–3.12** and provide a **polyfill for `asyncio.to_thread`** so the
feature is available on Python 3.8.

**Status: ✅ Implemented** — `asyncio.to_thread` is used in `src/sam/persistence/database.py`;
`pyproject.toml` declares `requires-python = ">=3.8"`.

# Architectural Rationale

Maximum compatibility with the development baseline at trivial cost. A thin polyfill
is preferable to excluding Python 3.8 environments or adding a runtime dependency.

# Consequences

## Positive
- Broad Python version support (3.8–3.12)
- No external dependency for the shim

## Negative
- A small compatibility shim must be maintained

## Accepted Trade-offs
- Slightly more code in the persistence layer.

---

# Impact Analysis

- **Framework:** persists across supported Python versions.
- **Modules:** `src/sam/persistence/database.py`.
- **Tooling:** `pyproject.toml` (`requires-python = ">=3.8"`).

# Dependency Impact

Introduces no external dependency; only a stdlib-based polyfill.

# Risk Assessment

| Dimension | Assessment |
|------------|------------|
| Probability | Low |
| Impact | Low |
| Recoverability | High |
| Blast Radius | Persistence layer |
| Reversibility | High |

---

# Trust Assessment

Evidence: `pyproject.toml` `requires-python = ">=3.8"` and usage in `database.py`.
Confidence: High.
Unknowns: future Python version support policy.

---

# Implementation Notes

Reference: `asyncio.to_thread` in `src/sam/persistence/database.py`;
version guard in `pyproject.toml`.

# Migration Strategy

No migration required; polyfill already in use.

# Success Criteria

SAM runs on Python 3.8 through 3.12 without requiring `asyncio.to_thread`-native support on 3.8.

# Future Reassessment

Reassess if the team's Python baseline rises above 3.8 or a higher minimum is adopted.

---

# Related Documents

- REPOSITORY_CONVENTION.md
- pyproject.toml

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
