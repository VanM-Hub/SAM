<!--

===============================================================================

SAM Framework

Architecture Documentation Template

===============================================================================



Purpose

-------

Use this template to describe the architecture of a Framework,

Subsystem, Module, Service, or other significant architectural unit.



Architecture documentation explains structure, responsibilities,

boundaries, dependencies, and design rationale.



Architecture documentation should remain implementation-independent.



Implementation details belong elsewhere.



See:



\- SAM_ARCHITECTURE.md

\- ARCHITECTURAL_DECISIONS.md

\- Architecture_Rulebook.md

\- DOCUMENT\_STRUCTURE.md

\- WRITING\_GUIDELINES.md



===============================================================================

\-->



# <ARCHITECTURE NAME>



Version:



Status:



Owner:



Last Updated:



Related ADRs:



Related Modules:



Related Documents:



---



<!--

Purpose

-------



Describe why this architecture exists.



Explain the responsibility of the architectural unit.



Do not describe implementation.

\-->



# Purpose



---



<!--

Scope

-----



Clearly define architectural boundaries.



Explain what belongs to this architecture

and what intentionally does not.

\-->



# Scope



Included



\-



Excluded



\-



---



<!--

Problem Statement

-----------------



Describe the architectural problem

that this architecture solves.



Avoid discussing implementation.

\-->



# Problem Statement



---



<!--

Architectural Goals

-------------------



Describe the desired outcomes.



Examples:



Scalability



Maintainability



Reliability



Modularity



Extensibility



Operational Safety

\-->



# Architectural Goals



---



<!--

Architectural Principles

------------------------



Reference the Constitution.



Only list principles that directly influence

this architecture.

\-->



# Architectural Principles



\-



---



<!--

System Context

--------------



Describe where this architecture fits

within the overall Framework.



Readers should immediately understand

its position inside SAM.

\-->



# System Context



---



<!--

Architecture Overview

---------------------



Provide a high-level explanation.



A simple diagram is encouraged.

\-->



# Architecture Overview



```text

+----------------------+

| Framework            |

+----------+-----------+

&#x20;          |

&#x20;          v

+----------------------+

| Architecture         |

+----------+-----------+

&#x20;          |

&#x20;          v

+----------------------+

| Modules              |

+----------------------+

```



---



<!--

Layers

------



Describe architectural layers.



Each layer should have one responsibility.

\-->



# Layers



| Layer | Responsibility |

|--------|----------------|

| | |



---



<!--

Major Components

----------------



List the major architectural components.



For each component describe:



Purpose



Responsibilities



Interfaces



Dependencies

\-->



# Major Components



## Component



Purpose



Responsibilities



Interfaces



Dependencies



---



<!--

Interactions

------------



Describe how components communicate.



Focus on responsibilities

rather than implementation.



Sequence diagrams may be used.

\-->



# Interactions



---



<!--

Dependency Model

----------------



Reference DEPENDENCY\_RULES.md.



Document dependency direction.



Document prohibited dependencies.



Explain why.

\-->



# Dependency Model



Allowed



\-



Forbidden



\-



Rationale



\-



---



<!--

Interfaces

-----------



Describe architectural interfaces.



Avoid implementation details.



Describe contracts instead.

\-->



# Interfaces



---



<!--

Constraints

------------



Describe important constraints.



Examples:



Performance



Security



Governance



Operational



Compliance



Technology

\-->



# Constraints



---



<!--

Assumptions

-----------



Document assumptions explicitly.



Never hide assumptions.

\-->



# Assumptions



---



<!--

Trade-offs

-----------



Architecture always involves trade-offs.



Document both gains and sacrifices.



Reference ADRs where appropriate.

\-->



# Trade-offs



Advantages



\-



Disadvantages



\-



Accepted Trade-offs



\-



---



<!--

Risk Considerations

-------------------



Reference RISK\_MODEL.md.



Identify architectural risks.



Do not repeat implementation risks.

\-->



# Risk Considerations



---



<!--

Evolution Strategy

------------------



Describe how the architecture

is expected to evolve.



Focus on direction,

not implementation tasks.

\-->



# Evolution Strategy



Short-term



\-



Medium-term



\-



Long-term



\-



---



<!--

Relationships

-------------



Document architectural relationships.



Depends On



Referenced By



Extends



Complementary Documents



Related Modules



Related ADRs

\-->



# Relationships



Depends On



\-



Referenced By



\-



Extends



\-



Related Modules



\-



Related ADRs



\-



---



<!--

Related Documents

-----------------



Use canonical filenames.



Avoid duplicate explanations.

\-->



# Related Documents



\-



---



<!--

Author Checklist

----------------

\-->



# Author Checklist



\- \[ ] Purpose clearly defined

\- \[ ] Scope documented

\- \[ ] Architecture boundaries identified

\- \[ ] Components described

\- \[ ] Dependencies documented

\- \[ ] Risks documented

\- \[ ] Trade-offs documented

\- \[ ] Cross references validated

\- \[ ] Consistent with CONSTITUTION.md

\- \[ ] Consistent with DEPENDENCY\_RULES.md



---



<!--

Common Mistakes

---------------

\-->



# Common Mistakes



\- Mixing architecture with implementation.

\- Missing architectural boundaries.

\- Ignoring dependency direction.

\- Omitting trade-offs.

\- Redefining Framework concepts.

\- Documenting technologies instead of responsibilities.

\- Forgetting architectural rationale.



---



<!--

Completion Checklist

--------------------

\-->



# Completion Checklist



\- \[ ] Metadata complete

\- \[ ] Review completed

\- \[ ] Version assigned

\- \[ ] Status assigned

\- \[ ] Cross references verified

\- \[ ] Ready for publication



---



# Summary



Summarize the architecture in a few paragraphs.



Reinforce:



its responsibility,



its boundaries,



its role inside the Framework,



and its relationship with the rest of the architecture.

