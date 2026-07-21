# ARCHITECTURE



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This document defines the architectural foundation of the SAM Framework.



It explains:



\- how the framework is organized

\- why the architecture is designed this way

\- how responsibilities are separated

\- how future modules integrate into the framework

\- how long-term scalability is preserved



This document is the architectural reference for every future component.



---



# Architectural Philosophy



SAM is designed around one fundamental idea:



**The framework should outlive every implementation.**



Platforms evolve.



Models change.



Providers disappear.



Technologies become obsolete.



The framework should remain.



Therefore, platform-specific knowledge must never become part of the framework itself.



---



# Design Objectives



The architecture pursues six primary objectives.



## 1. Independence



The framework must not depend on any specific platform.



No component inside the framework should require knowledge of:



\- OpenClaw

\- Docker

\- Linux

\- Windows

\- Kubernetes



Those belong to modules.



---



## 2. Separation of Responsibilities



Every architectural layer owns one responsibility.



Knowledge belongs to modules.



Reasoning belongs to the framework.



Architecture belongs to documentation.



Governance belongs to the project.



No responsibility should exist in multiple locations.



---



## 3. Long-Term Maintainability



The framework should remain understandable after many years.



New contributors should be able to navigate the repository without understanding its historical evolution.



Architecture should explain itself.



---



## 4. Controlled Growth



The framework should grow by extension rather than modification.



Instead of changing existing components, new capabilities should normally be introduced through modules.



This minimizes architectural instability.



---



## 5. Explainability



Every major component should answer:



Why does it exist?



What responsibility does it own?



What does it deliberately not own?



Architectural boundaries should always be explicit.



---



## 6. Replaceability



Every module should be replaceable without affecting the framework.



If replacing one module requires changing the framework, the architecture has failed.



---



# High-Level Architecture



The SAM Framework is organized into layered responsibilities.



```



Vision



↓



Mission



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



```



Each layer depends only on layers above it.



No layer may bypass architectural boundaries.



---



# Framework Overview



The framework contains reusable concepts.



It defines:



\- reasoning

\- decision models

\- operational principles

\- trust

\- risk

\- execution philosophy



The framework does **not** contain operational knowledge for specific platforms.



---



# Modules



Modules provide domain expertise.



Examples include:



OpenClaw



Docker



Linux



Windows



GitHub



Kubernetes



Each module is responsible for translating framework concepts into platform-specific operations.



---



# Knowledge



Knowledge is separated from reasoning.



Reasoning determines how decisions are made.



Knowledge provides the evidence required for those decisions.



This distinction allows knowledge to evolve independently from reasoning.



---



# Playbooks



Playbooks transform knowledge into repeatable operational procedures.



Knowledge answers:



"What do we know?"



Playbooks answer:



"What should we do?"



---



# Automation



Automation is intentionally placed at the bottom of the architecture.



Automation is considered the final consumer of every previous architectural layer.



Automation without knowledge is dangerous.



Automation without governance is irresponsible.



Automation without reasoning is unpredictable.



Therefore automation depends upon the entire framework.



---



# Architectural Layers



Every layer provides services to lower layers.



Higher layers never depend upon lower layers.



The dependency direction always flows downward.



Vision



↓



Architecture



↓



Framework



↓



Modules



↓



Knowledge



↓



Automation



This creates a stable architectural hierarchy.



---



# Platform Independence



The framework intentionally knows nothing about:



OpenClaw



Docker



Linux



Windows



Provider APIs



Configuration formats



Log syntax



Authentication mechanisms



These concerns belong entirely to modules.



This design allows new modules to be introduced without redesigning the framework.



---



# Framework Responsibilities



The framework owns:



decision principles



thinking protocol



trust model



risk model



memory model



execution philosophy



governance integration



documentation conventions



The framework never owns platform implementations.



---



# Module Responsibilities



Every module owns:



platform knowledge



diagnostics



providers



models



configuration



playbooks



research



examples



tests



Modules should remain independent from one another.



OpenClaw should not require Docker.



Docker should not require Linux.



Each module should remain self-contained.



---



# Architectural Stability



Architecture changes should be rare.



Implementation changes should be common.



Knowledge changes should be continuous.



The architecture therefore acts as the most stable layer of the entire framework.



---



# Extension Strategy



New capabilities should normally be introduced by adding modules rather than modifying framework components.



Preferred approach:



Framework



↓



New Module



Avoid:



Framework



↓



Framework Modification



Repeated modification eventually creates architectural erosion.



---



# Architectural Principles



The architecture follows these principles:



Framework before implementation.



Composition before coupling.



Knowledge before automation.



Documentation before implementation.



Modules before monolith.



Evidence before assumption.



Human before automation.



These principles are inherited from PRINCIPLES.md.



---



# Relationship with Governance



Architecture defines structure.



Governance defines evolution.



The architecture explains where components belong.



Governance explains how those components change over time.



The two documents complement each other.



---



# Relationship with ADR



Architecture describes the current design.



Architecture Decision Records explain why the design exists.



Architecture answers:



"What is the framework?"



ADR answers:



"Why is the framework designed this way?"



---



# Summary



The architecture of SAM is intentionally conservative.



Stability is preferred over novelty.



Clear boundaries are preferred over convenience.



Modules evolve rapidly.



The framework evolves deliberately.



This balance enables long-term growth without sacrificing architectural integrity.

