# VERSIONING



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This document defines the versioning policy for all documentation within the SAM Framework.



Versioning communicates the maturity, stability, compatibility, and evolution of architectural knowledge.



A document version is more than a number.



It is a statement of confidence.



This policy applies to:



\- Governance documents

\- Architecture documents

\- Framework models

\- Module documentation

\- ADRs

\- Playbooks

\- Knowledge documents

\- Templates



---



# Philosophy



Knowledge evolves.



Architecture evolves.



Software evolves.



Documentation must evolve in a controlled, transparent, and traceable manner.



Version numbers exist to communicate change, not merely record it.



---



# Objectives



Versioning exists to:



communicate document maturity,



preserve historical context,



support repository stability,



enable safe collaboration,



track architectural evolution,



simplify review.



---



# Version Format



SAM adopts Semantic Versioning for documentation.



Format:



MAJOR.MINOR.PATCH



Example:



1.0.0



0.5.2



2.3.1



---



# Meaning of Each Component



Major



Architectural or structural change.



May invalidate previous assumptions.



May require updates to related documents.



Minor



New capabilities,



clarifications,



additional sections,



expanded guidance,



without changing the document's core responsibility.



Patch



Editorial improvements,



grammar,



formatting,



reference corrections,



minor clarification,



no architectural impact.



---



# Version 0.x



Version 0 represents active design.



The architecture is still evolving.



Breaking changes are expected.



Documents in version 0 should not be considered permanently stable.



---



# Version 1.0



Version 1.0 indicates:



architectural maturity,



stable terminology,



approved structure,



governance compliance,



cross-reference validation.



Version 1.0 establishes the baseline.



---



# Version Lifecycle



Every document follows the same lifecycle.



Draft



↓



Review



↓



Accepted



↓



Frozen



↓



Deprecated



↓



Archived



Version numbers describe change.



Lifecycle status describes maturity.



Both are required.



---



# Status Definitions



Draft



Work in progress.



May change significantly.



Review



Under architectural review.



Changes remain possible.



Accepted



Approved for repository use.



Frozen



Stable.



Only exceptional changes permitted.



Deprecated



Scheduled for replacement.



Should no longer be referenced in new work.



Archived



Historical record.



Maintained for traceability.



Not considered active guidance.



---



# When to Increment PATCH



Examples include:



grammar correction,



broken cross-reference,



metadata correction,



formatting improvements,



clarified wording,



diagram refinement.



Architectural meaning remains unchanged.



---



# When to Increment MINOR



Examples include:



new explanatory sections,



expanded rationale,



new examples,



additional implementation guidance,



improved diagrams,



clarified operational flow.



The architectural responsibility remains unchanged.



---



# When to Increment MAJOR



Examples include:



architectural redesign,



new responsibilities,



changed architectural boundaries,



new dependency direction,



constitutional impact,



breaking governance changes.



Major updates require architectural review.



---



# Version Compatibility



Documentation should preserve compatibility whenever practical.



Readers should understand:



what changed,



why it changed,



how previous guidance is affected.



Compatibility improves long-term maintainability.



---



# Breaking Changes



Breaking changes occur when:



architectural meaning changes,



repository structure changes,



official terminology changes,



dependency rules change,



module contracts change.



Breaking changes require:



architectural review,



ADR (when applicable),



updated cross references,



repository impact analysis.



---



# Change Documentation



Every meaningful version update should include:



summary,



motivation,



affected documents,



migration guidance (if needed).



Repository history should explain evolution.



---



# Relationship with ADR



Architectural decisions may trigger version changes.



However,



version increments do not replace ADRs.



ADR explains why.



Version communicates what changed.



---



# Relationship with Cross References



When a major document changes,



dependent documents should be reviewed.



Cross references should never silently become outdated.



Repository consistency depends upon synchronized evolution.



---



# Version History



Major architectural documents should maintain a concise version history.



Example:



| Version | Status | Summary |

|----------|--------|---------|

| 0.1.0 | Draft | Initial document |

| 0.5.0 | Review | Expanded lifecycle |

| 1.0.0 | Accepted | Stable baseline |



Version history should summarize evolution rather than duplicate commit history.



---



# Repository Releases



Repository releases represent coherent snapshots of the Framework.



Individual documents may evolve independently.



Official repository releases should identify:



supported architecture,



baseline governance,



compatible modules,



known limitations.



---



# Future Evolution



Future tooling may automatically:



validate document versions,



detect outdated references,



identify incompatible dependencies,



generate migration reports,



recommend review candidates.



Consistent versioning enables repository automation.



---



# Relationship with Governance



Versioning is governed by:



CONSTITUTION.md



GOVERNANCE.md



DOCUMENTATION\_PHILOSOPHY.md



Changes affecting repository-wide versioning policy require architectural review.



---



# Versioning Principles



The Framework follows these principles.



Version numbers communicate meaning.



History should remain traceable.



Breaking changes should be explicit.



Repository stability outweighs convenience.



Architecture evolves deliberately.



Documentation should explain change.



---



# Success Criteria



The versioning policy succeeds when:



document maturity is obvious,



breaking changes are visible,



historical evolution is preserved,



cross references remain consistent,



contributors understand when and why versions change.



---



# Summary



Versioning is the language of architectural evolution.



Within the SAM Framework, version numbers communicate stability, maturity, and compatibility while preserving traceability and enabling long-term maintenance.



Documentation should evolve deliberately, transparently, and consistently with the principles defined by the Constitution.

