# LAYERS



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This document defines the architectural layers of the SAM Framework.



Every component in the repository belongs to exactly one architectural layer.



The objective of layering is to:



\- separate responsibilities

\- reduce coupling

\- improve scalability

\- simplify maintenance

\- preserve architectural stability



Layers define responsibility—not implementation.



---



# Design Philosophy



SAM follows a layered architecture.



Each layer answers a different question.



| Layer | Primary Question |

|--------|------------------|

| Vision | Why does SAM exist? |

| Governance | How should SAM evolve? |

| Architecture | How is SAM organized? |

| Framework | How should SAM think? |

| Modules | How is a platform represented? |

| Knowledge | What do we know? |

| Playbooks | What should we do? |

| Automation | How is work executed? |



Each layer depends only on the layers above it.



---



# Layer 1 — Vision



Purpose



Defines the identity and long-term direction of the project.



Contains



\- Vision

\- Mission



Responsibilities



\- project purpose

\- long-term goals

\- intended audience

\- future direction



Must Never Contain



\- implementation

\- architecture

\- module details



This is the most stable layer of the repository.



---



# Layer 2 — Governance



Purpose



Defines how the framework evolves.



Contains



\- Principles

\- Governance

\- Repository Convention

\- Documentation Standards

\- Versioning Policies



Responsibilities



\- project rules

\- quality standards

\- contribution process

\- architectural governance



Must Never Contain



\- implementation details

\- platform knowledge



Governance applies to every future document.



---



# Layer 3 — Architecture



Purpose



Defines the structural organization of the framework.



Contains



\- Architecture

\- Layers

\- Dependency Rules

\- Module Interface

\- Growth Model

\- ADR



Responsibilities



\- architectural boundaries

\- component responsibilities

\- dependency direction

\- extension strategy



Architecture describes structure.



It does not describe implementation.



---



# Layer 4 — Framework



Purpose



Defines reusable operational intelligence.



Future Components



Decision Engine



Thinking Protocol



Risk Engine



Trust Engine



Memory Model



Execution Model



Responsibilities



\- reasoning

\- evaluation

\- decision support

\- operational philosophy



Framework should remain platform-independent.



Framework never owns operational knowledge.



---



# Layer 5 — Modules



Purpose



Represent operational domains.



Examples



OpenClaw



Docker



Windows



Linux



GitHub



Kubernetes



Responsibilities



\- platform abstraction

\- platform-specific reasoning

\- configuration handling

\- provider integration

\- diagnostics



Modules translate framework concepts into practical operations.



Modules must remain isolated.



---



# Layer 6 — Knowledge



Purpose



Store verified information.



Knowledge includes



documentation



research



known issues



configuration



provider behavior



API characteristics



best practices



Knowledge answers:



"What is true?"



Knowledge should always distinguish between:



Verified



Observed



Assumed



Experimental



Knowledge changes frequently.



Framework should not.



---



# Layer 7 — Playbooks



Purpose



Convert knowledge into repeatable operational procedures.



Examples



Changing providers



Testing APIs



Recovering workers



Updating configuration



Validating installations



Playbooks answer:



"What sequence of actions should be followed?"



Playbooks should reference Knowledge.



They should never duplicate Knowledge.



---



# Layer 8 — Automation



Purpose



Execute approved procedures.



Automation is intentionally placed last.



Automation consumes:



Framework



Modules



Knowledge



Playbooks



Automation should never bypass architectural rules.



Automation must remain observable.



---



# Layer Interaction



The expected interaction flow is:



Vision



↓



Governance



↓



Architecture



↓



Framework



↓



Module



↓



Knowledge



↓



Playbook



↓



Automation



This order reflects increasing operational specificity.



---



# Layer Stability



Layers evolve at different speeds.



| Layer | Expected Stability |

|--------|-------------------|

| Vision | Very High |

| Governance | High |

| Architecture | High |

| Framework | Medium |

| Modules | Medium |

| Knowledge | Low |

| Playbooks | Low |

| Automation | Very Low |



The lower the layer, the more frequently change is expected.



---



# Layer Ownership



Every repository artifact belongs to exactly one layer.



If ownership is unclear, architecture should be reconsidered.



Shared ownership creates architectural ambiguity.



---



# Dependency Principle



Higher layers define concepts.



Lower layers implement concepts.



Higher layers never depend upon lower layers.



Dependency always flows downward.



This rule protects architectural stability.



---



# Architectural Evolution



Future development should introduce new capabilities by extending lower layers whenever possible.



Example



Adding Docker support



↓



New Module



↓



New Knowledge



↓



New Playbooks



↓



Existing Framework unchanged



This minimizes architectural risk.



---



# Summary



Layering is the primary mechanism that keeps SAM understandable as it grows.



Every layer has one responsibility.



Every responsibility has one owner.



Every owner has clearly defined boundaries.



Maintaining these boundaries is more important than reducing the number of files.



Well-defined layers enable the framework to grow for years without becoming a monolithic system.

