# DEPENDENCY\_RULES



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This document defines how dependencies are allowed to flow throughout the SAM Framework.



Dependency rules are one of the primary mechanisms used to preserve long-term architectural stability.



Without explicit dependency rules, architectures gradually become tightly coupled, difficult to maintain, and resistant to change.



---



# Architectural Principle



Dependencies always point downward.



The framework is organized as a hierarchy rather than a network.



Allowed direction:



Vision



↓



Governance



↓



Architecture



↓



Framework



↓



Modules



↓



Knowledge



↓



Playbooks



↓



Automation



A lower layer may depend on higher layers.



A higher layer must never depend on lower layers.



---



# Core Rule



Every dependency must move toward greater specialization.



General concepts may know nothing about specialized implementations.



Specialized implementations may rely upon general concepts.



This principle prevents the framework from becoming platform-specific.



---



# Allowed Dependencies



Vision



Depends on:



Nothing



---



Governance



Depends on:



Vision



---



Architecture



Depends on:



Vision



Governance



---



Framework



Depends on:



Vision



Governance



Architecture



---



Modules



Depends on:



Framework



Architecture



Governance



---



Knowledge



Depends on:



Module



Framework concepts



---



Playbooks



Depends on:



Knowledge



Modules



Framework



---



Automation



Depends on:



Everything above



Automation is always the final consumer.



---



# Forbidden Dependencies



Framework



MUST NOT depend on



OpenClaw



Docker



Linux



Windows



GitHub



Providers



Models



Configuration files



Logs



Runtime state



Authentication mechanisms



Network protocols



These concerns belong exclusively to modules.



---



# Module Isolation



Modules must remain independent.



Examples



OpenClaw



must not depend on



Docker



Linux



Windows



GitHub



Likewise



Docker



must not depend on



OpenClaw.



Shared functionality belongs inside the framework—not copied between modules.



---



# Circular Dependencies



Circular dependencies are prohibited.



Example



Framework



↓



Module



↓



Framework



This is invalid.



Instead:



Framework defines contracts.



Modules implement contracts.



Communication occurs through interfaces.



---



# Shared Code



If two modules require identical functionality, that functionality should be evaluated.



Decision process:



Is it platform-independent?



YES



↓



Move to Framework.



NO



↓



Keep inside module.



Never create direct module-to-module dependencies.



---



# Knowledge Dependencies



Knowledge belongs to modules.



Knowledge should never modify framework behavior.



Knowledge provides evidence.



Framework provides reasoning.



Keeping these concerns separate allows knowledge to evolve rapidly while preserving architectural stability.



---



# Playbook Dependencies



Playbooks consume knowledge.



Playbooks should not redefine knowledge.



Incorrect



Knowledge duplicated inside playbook.



Correct



Playbook references knowledge.



This reduces documentation drift.



---



# Automation Dependencies



Automation is intentionally the most dependent layer.



Automation may consume:



Framework



Modules



Knowledge



Playbooks



Automation should not introduce new architectural concepts.



Its responsibility is execution—not design.



---



# Interface-Based Communication



Communication between framework and modules should occur through stable interfaces.



Framework



↓



Interface



↓



Module



Framework should never call module internals directly.



Modules should expose capabilities through well-defined contracts.



---



# Dependency Review



Before introducing a new dependency, contributors should ask:



Does this dependency violate layer boundaries?



Can the dependency be inverted?



Can an interface replace direct coupling?



Does the dependency reduce replaceability?



Would removing this dependency improve architecture?



If the answer suggests architectural degradation, reconsider the design.



---



# Evolution Strategy



As the framework grows:



Prefer



New Module



over



Framework Modification



Prefer



New Interface



over



Direct Coupling



Prefer



Composition



over



Inheritance



Prefer



Contracts



over



Implementation Sharing



---



# Architectural Smells



The following situations indicate architectural problems.



Framework imports platform-specific code.



Modules communicate directly.



Knowledge modifies framework logic.



Playbooks duplicate documentation.



Automation contains business rules.



Configuration becomes framework logic.



Circular dependencies appear.



These should trigger architectural review.



---



# Exception Policy



Exceptions to these rules should be rare.



Any intentional violation requires:



An Architecture Decision Record (ADR)



A documented rationale



An assessment of long-term impact



A migration strategy if applicable



Architecture should evolve deliberately, not accidentally.



---



# Summary



Dependency direction is one-way.



Framework defines concepts.



Modules implement concepts.



Knowledge supplies evidence.



Playbooks organize procedures.



Automation executes approved actions.



Protecting these dependency rules protects the long-term maintainability of the SAM Framework.

