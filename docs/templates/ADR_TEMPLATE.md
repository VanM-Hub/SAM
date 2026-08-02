<!--

===============================================================================

SAM Framework

Architecture Decision Record Template

===============================================================================



Purpose

-------

Use this template to document architectural decisions that affect the Framework,

its modules, governance, interfaces, dependency rules, or long-term evolution.



An ADR preserves architectural reasoning.



It should explain WHY a decision was made, not merely WHAT was decided.



See:

\- CONSTITUTION.md

\- SAM_ARCHITECTURE.md

\- SPECIFICATION\_FREEZE.md

\- DECISION\_MODEL.md

\- DOCUMENT\_STRUCTURE.md

\- REVIEW\_PROCESS.md



===============================================================================

\-->



# ADR-XXXX â€” <Decision Title>



Version: 0.1.0



Status:

Draft | Accepted | Superseded | Deprecated



Decision Date:



Author:



Reviewers:



Related ADRs:



Related Documents:



Related Modules:



---



<!--

Purpose

-------

State the architectural problem being solved.



Do not describe implementation.



Keep this section concise.

\-->



# Purpose



---



<!--

Context

-------

Describe the architectural context.



Explain:



\- Current situation

\- Constraints

\- Existing architecture

\- Assumptions

\- Business or technical drivers



A reader should understand why this ADR became necessary.

\-->



# Context



---



<!--

Problem Statement

-----------------



Clearly define the architectural problem.



The problem should be objective.



Avoid proposing a solution here.

\-->



# Problem Statement



---



<!--

Decision Drivers

----------------



List the criteria used to evaluate alternatives.



Examples:



\- Simplicity

\- Maintainability

\- Security

\- Performance

\- Extensibility

\- Operational Risk

\- Human Oversight

\-->



# Decision Drivers



---



<!--

Alternatives Considered

-----------------------



Describe every serious alternative.



For each alternative explain:



Advantages



Disadvantages



Reason for rejection



Rejected ideas are valuable historical knowledge.

\-->



# Alternatives Considered



## Alternative A



### Advantages



### Disadvantages



### Assessment



---



## Alternative B



### Advantages



### Disadvantages



### Assessment



---



## Alternative C



### Advantages



### Disadvantages



### Assessment



---



<!--

Decision

--------



Describe the selected architectural decision.



State exactly what has been accepted.



Avoid implementation details.

\-->



# Decision



---



<!--

Architectural Rationale

-----------------------



Explain WHY this decision is considered the best choice.



Reference architectural principles.



Reference the Constitution when applicable.



This is usually the most important section of an ADR.

\-->



# Architectural Rationale



---



<!--

Consequences

------------



Describe both positive and negative consequences.



Architecture always involves trade-offs.



Document them honestly.

\-->



# Consequences



## Positive



\-



## Negative



\-



## Accepted Trade-offs



\-



---



<!--

Impact Analysis

---------------



Describe the expected impact.



Examples:



Framework



Modules



Documentation



Tooling



Users



Repository



Future development

\-->



# Impact Analysis



---



<!--

Dependency Impact

-----------------



Describe changes to dependency direction.



Will this ADR introduce:



new dependencies,



remove dependencies,



change interfaces,



affect layering?



Reference DEPENDENCY\_RULES.md.

\-->



# Dependency Impact



---



<!--

Risk Assessment

---------------



Use the official Risk Model.



Evaluate:



Probability



Impact



Recoverability



Blast Radius



Reversibility



Reference RISK\_MODEL.md.

\-->



# Risk Assessment



| Dimension | Assessment |

|------------|------------|

| Probability | |

| Impact | |

| Recoverability | |

| Blast Radius | |

| Reversibility | |



---



<!--

Trust Assessment

----------------



Summarize evidence supporting the decision.



Reference TRUST\_MODEL.md.



Avoid unsupported assumptions.

\-->



# Trust Assessment



Evidence:



Confidence:



Unknowns:



---



<!--

Implementation Notes

--------------------



Describe implementation guidance.



This section should remain implementation-oriented,

not architectural.



Implementation details may reference modules or playbooks.

\-->



# Implementation Notes



---



<!--

Migration Strategy

------------------



If replacing existing architecture,

describe migration.



If no migration is required,

state so explicitly.

\-->



# Migration Strategy



---



<!--

Success Criteria

----------------



How will we know this decision was successful?



Use measurable outcomes whenever possible.

\-->



# Success Criteria



---



<!--

Future Reassessment

-------------------



Architecture evolves.



Describe situations that should trigger review of this ADR.



Examples:



new technology,



operational failures,



governance changes,



performance limits.

\-->



# Future Reassessment



---



<!--

Related Documents

-----------------



Reference authoritative documents.



Avoid duplication.



Use canonical filenames.

\-->



# Related Documents



\-



---



<!--

Review History

--------------



Record major review milestones.



Do not duplicate Git history.



Focus on architectural review.

\-->



# Review History



| Date | Reviewer | Outcome |

|------|----------|---------|

| | | |



---



<!--

Author Checklist

----------------

\-->



# Author Checklist



\- \[ ] Problem clearly defined

\- \[ ] Alternatives documented

\- \[ ] Decision justified

\- \[ ] Trade-offs documented

\- \[ ] Risks evaluated

\- \[ ] Trust assessment completed

\- \[ ] Related documents referenced

\- \[ ] Terminology follows GLOSSARY.md

\- \[ ] Consistent with CONSTITUTION.md



---



<!--

Common Mistakes

---------------



Avoid these mistakes when writing an ADR.

\-->



# Common Mistakes



\- Describing implementation instead of architecture.

\- Omitting rejected alternatives.

\- Ignoring trade-offs.

\- Recording opinions without evidence.

\- Mixing operational procedures with architectural decisions.

\- Failing to document risks.

\- Creating an ADR for trivial editorial changes.



---



<!--

Completion Checklist

--------------------

\-->



# Completion Checklist



\- \[ ] Metadata complete

\- \[ ] Cross references validated

\- \[ ] Review completed

\- \[ ] Status updated

\- \[ ] Ready for repository publication

