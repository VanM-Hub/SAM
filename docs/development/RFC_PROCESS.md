# RFC Process — Post v1.0

**Version:** v1.0.0  
**Purpose:** Govern changes to SAM after the architecture freeze.

---

## Overview

An **RFC (Request for Comments)** is required for any change that:
- Adds a new major feature or subsystem
- Modifies a frozen public API contract
- Changes the database schema (new migration)
- Introduces a new dependency
- Deprecates or removes a feature
- Alters architectural layering or dependency direction

## RFC Lifecycle

```
DRAFT → REVIEW → APPROVED → IMPLEMENTED → MERGED
  ↑         |          |
  └── REJECTED ────────┘
```

---

## Step 1: Draft

Create a new file at `docs/rfcs/RFC-XXXX-my-feature.md` using the template:

```markdown
# RFC-NNNN: Title

**Status:** DRAFT  
**Author:** Your Name  
**Date:** YYYY-MM-DD

## Summary
One paragraph describing the change.

## Motivation
Why is this change needed? What problem does it solve?

## Design
Detailed technical design:
- New modules / files
- API changes
- Database migrations
- Configuration changes

## Migration
What existing users need to do to adopt this change.

## Alternatives Considered
What other approaches were considered and why this one was chosen.

## Drawbacks
Known risks, trade-offs, or limitations.

## Open Questions
Anything not yet decided.

## Timeline
When this should be implemented (target release).
```

## Step 2: Review

1. Submit RFC as a Pull Request to `docs/rfcs/`
2. Minimum review period: **3 business days**
3. Required reviewers: at least 2 maintainers
4. Comments and discussion happen on the PR
5. Author may update the RFC based on feedback

### Review Criteria

| Criterion | Required |
|---|---|
| Architectural consistency | ✅ Must not violate frozen contracts |
| Backward compatibility | ✅ Unless explicitly breaking for MAJOR version |
| Test coverage | ✅ ≥ 80% for new code |
| Documentation | ✅ RFC + public API docs + migration guide |
| Security impact | ✅ Must be reviewed for new dependencies |

## Step 3: Approval

- **Simple RFC:** Approved by 1 maintainer
- **Complex RFC** (new subsystem, breaking change): Approved by architecture team consensus
- **Architecture freeze break:** Requires unanimous approval from all maintainers

## Step 4: Implementation

1. Update RFC status to `IMPLEMENTED`
2. Implementation follows the RFC design
3. All existing tests must pass
4. New tests must be added
5. Public API documentation updated

## Step 5: Merge

1. Final review of implementation vs RFC
2. RFC status set to `MERGED`
3. Implementation merged to `main`

---

## When RFC Is NOT Required

- Bug fixes
- Performance optimizations (no API change)
- Internal refactoring (no public API change)
- Documentation improvements
- Test additions
- Dependency updates (patch versions)

## RFC Template Location

A template is available at `docs/templates/RFC_TEMPLATE.md`.

---

*Document prepared for SAM v1.0.0 release.*
