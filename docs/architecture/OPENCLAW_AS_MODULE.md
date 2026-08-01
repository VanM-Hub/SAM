# OPENCLAW\_AS\_MODULE



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This document explains why OpenClaw is implemented as a Module rather than becoming part of the Framework itself.



This is an architectural decision.



It defines the relationship between SAM and OpenClaw and protects the framework from becoming coupled to a single platform.



This document should be read together with:



\- SAM_ARCHITECTURE.md

\- FRAMEWORK\_VS\_MODULE.md

\- MODULE\_INTERFACE.md

\- DEPENDENCY\_RULES.md



---



# Background



SAM was conceived as an AI Operations Framework.



At the same time, OpenClaw was identified as the first real-world platform that could benefit from such a framework.



This naturally raises a question:



Should OpenClaw become the Framework?



The answer is intentionally **No.**



OpenClaw is the first implementation.



It is not the architecture itself.



---



# The Architectural Decision



Decision



OpenClaw SHALL be implemented as an independent Module.



The Framework SHALL remain completely unaware of OpenClaw-specific implementation details.



Status



Accepted.



This decision establishes the architectural direction for every future platform.



---



# Why This Decision Exists



The purpose of SAM is larger than OpenClaw.



SAM aims to become an AI Operations Framework capable of supporting many operational domains.



Examples include:



Docker



Linux



Windows



GitHub



Kubernetes



Cloud Platforms



Database Systems



Network Infrastructure



If OpenClaw were embedded into the Framework, every future platform would inherit unnecessary coupling.



The Framework would gradually become an OpenClaw Framework instead of a general AI Operations Framework.



---



# OpenClaw Is a Domain



OpenClaw represents one operational domain.



It has:



its own terminology



its own configuration



its own APIs



its own providers



its own logs



its own workflows



its own operational problems



These characteristics belong inside a Module.



They are not universal concepts.



---



# The Framework Should Not Know OpenClaw



The Framework should never answer questions such as:



How is an OpenClaw workspace organized?



What does openclaw.json contain?



How is provider routing configured?



How are workers restarted?



Which models are available?



Those questions belong exclusively to the OpenClaw Module.



---



# The Module Teaches the Framework



The Framework provides reasoning.



The Module provides expertise.



Example



Framework asks:



"What evidence is available?"



OpenClaw Module replies:



"The configuration file contains an invalid provider definition."



Framework concludes:



"The configuration is inconsistent with expected behavior."



This separation allows the Framework to reason consistently across completely different platforms.



---



# Replaceability



Imagine OpenClaw disappears.



The Framework should continue to function.



Only one capability is lost:



Knowledge of OpenClaw.



Now imagine replacing OpenClaw with another platform.



The Framework should require no architectural modification.



Only a new Module should be added.



This is a primary design objective.



---



# Why Not a Plugin?



OpenClaw could technically be implemented as a plugin.



However, the architectural concept of a Module is intentionally broader.



A Module includes:



Knowledge



Research



Diagnostics



Vocabulary



Playbooks



Examples



Tests



Documentation



Architecture



Automation



A plugin typically focuses on executable functionality.



A Module represents an operational domain.



---



# Why OpenClaw Comes First



OpenClaw is selected as the first Module because it exercises many capabilities that the Framework must eventually support.



These include:



AI provider management



Configuration management



Operational diagnostics



Evidence gathering



Workspace organization



Agent orchestration



Model validation



Knowledge evolution



By solving OpenClaw first, the Framework gains practical experience without sacrificing architectural neutrality.



---



# Future Modules



OpenClaw establishes the pattern.



Future modules should follow the same architectural contract.



Examples



Docker Module



Linux Module



GitHub Module



Windows Module



Kubernetes Module



Cloud Module



Each module should implement the Module Interface while remaining independent from one another.



---



# Responsibilities of the OpenClaw Module



The OpenClaw Module owns:



OpenClaw architecture



Configuration knowledge



Provider behavior



Model catalogs



Operational diagnostics



Known issues



Recovery procedures



Research



Playbooks



Compatibility information



Examples



Tests



The Framework owns none of these responsibilities.



---



# Responsibilities of the Framework



The Framework owns:



Decision Model



Thinking Protocol



Risk Evaluation



Trust Evaluation



Evidence Evaluation



Execution Strategy



Vocabulary



Governance



Architecture



The Framework should not know whether the information originated from OpenClaw, Docker, or any future Module.



---



# Architectural Benefits



Treating OpenClaw as a Module provides several advantages.



Platform Independence



The Framework remains reusable.



Scalability



New platforms can be introduced without redesign.



Replaceability



OpenClaw can evolve independently.



Maintainability



Knowledge remains localized.



Testability



Modules can be tested separately.



Clarity



Architectural responsibilities remain explicit.



These properties become increasingly valuable as the repository grows.



---



# Risks



The primary risk is accidental coupling.



Examples include:



Framework imports OpenClaw code.



Framework understands openclaw.json.



Framework embeds provider knowledge.



Framework parses OpenClaw logs.



Framework knows OpenClaw CLI syntax.



Each of these situations violates the architectural boundary.



Whenever such coupling appears, architecture should be reviewed.



---



# Long-Term Vision



One day the repository may contain dozens of Modules.



SAM Framework



â†“



OpenClaw Module



Docker Module



Linux Module



GitHub Module



Windows Module



Kubernetes Module



Cloud Module



Database Module



Network Module



Each Module expands operational expertise.



None expands the Framework itself.



This distinction enables long-term sustainability.



---



# Decision Criteria for Future Modules



A new platform should become a Module when:



it introduces platform-specific knowledge,



it has its own operational vocabulary,



it requires dedicated diagnostics,



it has unique playbooks,



it can evolve independently,



it benefits from reusable framework reasoning.



If these conditions are satisfied, the platform should not be integrated into the Framework.



It should become its own Module.



---



# Summary



OpenClaw is not the center of SAM.



OpenClaw is the first expert that joins SAM.



The Framework remains platform-independent.



The Module remains domain-specific.



This architectural separation preserves the long-term vision of SAM as a reusable AI Operations Framework rather than a framework dedicated to a single product.

