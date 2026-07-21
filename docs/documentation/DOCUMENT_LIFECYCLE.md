# DOCUMENT\_LIFECYCLE



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This document defines the lifecycle of documentation within the SAM Framework.



Every document progresses through a predictable sequence of maturity.



Lifecycle management ensures that documentation remains current, trustworthy, and traceable throughout its existence.



This document is governed by:



\- CONSTITUTION.md

\- GOVERNANCE.md

\- VERSIONING.md



---



# Philosophy



Documentation is living knowledge.



Documents should evolve intentionally.



A document should never remain permanently unfinished, permanently accepted, or permanently forgotten.



Lifecycle management enables continuous improvement while preserving historical context.



---



# Lifecycle Overview



Every document follows the same lifecycle.



Idea



↓



Draft



↓



Review



↓



Accepted



↓



Implemented (when applicable)



↓



Frozen



↓



Deprecated



↓



Archived



Not every document reaches every stage.



The lifecycle reflects maturity rather than age.



---



# Stage: Idea



Purpose



Capture an architectural concept before detailed writing begins.



Characteristics



informal,



exploratory,



non-authoritative.



Ideas belong in the project backlog.



---



# Stage: Draft



Purpose



Develop the initial document.



Characteristics



work in progress,



subject to change,



not authoritative.



Drafts encourage collaboration.



---



# Stage: Review



Purpose



Evaluate the draft through the official review process.



Characteristics



under active review,



feedback incorporated,



quality improvements expected.



Review prepares documentation for acceptance.



---



# Stage: Accepted



Purpose



Establish the document as official repository knowledge.



Characteristics



approved,



referencable,



stable,



authoritative.



Accepted documents become part of the Framework baseline.



---



# Stage: Implemented



Purpose



Indicate that the documented guidance has been adopted in practice.



Examples



module implemented,



policy enforced,



architecture realized,



playbook operational.



Not every document requires this stage.



Pure policy documents may transition directly to Frozen.



---



# Stage: Frozen



Purpose



Preserve mature documentation.



Characteristics



stable,



rarely modified,



baseline reference.



Changes should occur only for exceptional reasons.



---



# Stage: Deprecated



Purpose



Signal that the document is being replaced.



Characteristics



still available,



not recommended for new work,



successor identified whenever possible.



Deprecation should include migration guidance.



---



# Stage: Archived



Purpose



Preserve historical knowledge.



Characteristics



read-only,



historical,



traceable,



non-authoritative.



Archived documents should remain accessible unless legal or security requirements dictate otherwise.



---



# Lifecycle Transitions



Transitions should occur deliberately.



Examples



Draft → Review



after author completion.



Review → Accepted



after successful review.



Accepted → Frozen



after sustained stability.



Frozen → Deprecated



when superseded.



Deprecated → Archived



after migration is complete.



Each transition should be documented.



---



# Reopening Documents



A Frozen, Deprecated, or Archived document may be reopened.



Reasons include:



architectural evolution,



incorrect assumptions,



new evidence,



governance changes,



security concerns.



Reopened documents begin a new review cycle.



---



# Relationship with Versioning



Lifecycle stage and document version are independent.



Example



Version



1.2.0



Status



Frozen



or



Version



2.0.0



Status



Review



Both dimensions should always be visible.



---



# Relationship with ADR



ADR documents follow the same lifecycle unless an ADR explicitly defines otherwise.



Historical ADRs should never be deleted.



They may become superseded but remain part of repository history.



---



# Repository Maintenance



Repository maintainers should periodically review:



Draft documents,



long-running Reviews,



Deprecated documents,



orphaned documentation,



obsolete references.



Lifecycle maintenance is an ongoing governance responsibility.



---



# Lifecycle Principles



The Framework follows these principles.



Knowledge evolves deliberately.



History is preserved.



Traceability is maintained.



Deprecation precedes archival.



Nothing becomes authoritative without review.



No document is forgotten.



---



# Success Criteria



The lifecycle succeeds when:



every document has a visible maturity stage,



repository knowledge remains current,



historical decisions remain traceable,



obsolete guidance is clearly identified,



contributors understand the status of every document.



---



# Summary



The Document Lifecycle defines how knowledge is born, refined, approved, maintained, and eventually retired.



By treating documentation as living architectural knowledge rather than static files, the SAM Framework preserves clarity, trust, and long-term maintainability throughout the evolution of the repository.

