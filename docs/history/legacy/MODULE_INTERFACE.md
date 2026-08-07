# MODULE\_INTERFACE



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This document defines the architectural contract between the SAM Framework and every Module.



It does not specify programming interfaces.



Instead, it defines responsibilities, expectations, and communication boundaries.



Every module must satisfy this contract before it becomes an official SAM Module.



---



# Philosophy



The Framework defines how to think.



Modules define what is known.



Frameworks are permanent.



Modules are replaceable.



Therefore:



Framework owns intelligence.



Modules own expertise.



This distinction is fundamental.



---



# Why an Interface Exists



Without an interface, modules eventually become extensions of the framework.



When that happens:



the framework becomes platform-specific,



modules become tightly coupled,



architectural stability disappears.



The interface exists to prevent this.



---



# Framework Responsibilities



The Framework owns:



Decision Models



Thinking Protocol



Risk Model



Trust Model



Execution Philosophy



Governance



Architectural Rules



Documentation Standards



Vocabulary



Framework components must never require platform knowledge.



---



# Module Responsibilities



Every module owns its operational domain.



This includes:



Platform Knowledge



Provider Knowledge



Configuration Knowledge



Diagnostics



Playbooks



Examples



Known Issues



Research



Tests



Modules answer questions that only domain experts can answer.



---



# Communication Contract



Framework



↓



Requests capabilities



↓



Module



↓



Provides domain-specific information



↓



Framework



↓



Evaluates and reasons



↓



Human



Framework never performs platform reasoning directly.



---



# Module Inputs



A module receives requests from the framework.



Typical requests include:



Describe platform state



Validate configuration



Explain provider behavior



Identify known issues



Suggest diagnostics



Recommend playbooks



The framework defines the request.



The module provides domain knowledge.



---



# Module Outputs



Modules return structured information.



Examples include:



Observed Facts



Evidence



Diagnostic Results



Known Limitations



Possible Actions



Confidence Level



References



Modules should avoid making final decisions.



Decision-making belongs to the framework.



---



# Knowledge Ownership



Modules own knowledge.



Framework owns reasoning.



Example



Framework asks



"What risks exist?"



Module responds



"The provider rejects this configuration."



Framework concludes



"The operational risk is High."



The framework interprets.



The module informs.



---



# Module Independence



Every module should be installable independently.



Removing one module should not require modifying:



Framework



Architecture



Governance



Other Modules



Replaceability is a design goal.



---



# Standard Module Structure



Every module should follow a consistent internal organization.



Example



module/



README.md



architecture/



knowledge/



providers/



diagnostics/



playbooks/



research/



tests/



examples/



Additional directories are permitted when justified.



---



# Required Capabilities



Every official module should provide:



Platform Description



Knowledge Base



Operational Vocabulary



Diagnostics



Playbooks



Research References



Examples



Testing Strategy



If one of these areas is missing, the module should explain why.



---



# Optional Capabilities



Modules may also provide:



Automation



Migration Guides



Compatibility Tables



Performance Data



Benchmark Results



Provider Comparisons



These capabilities improve module quality but are not mandatory.



---



# Framework Expectations



The Framework expects modules to be:



Self-contained



Well documented



Replaceable



Versioned



Testable



Evidence-driven



Transparent



Modules should not rely upon undocumented behavior.



---



# Error Handling



Modules should distinguish between:



Verified Facts



Observed Behavior



Assumptions



Unknown Conditions



Experimental Findings



The framework requires uncertainty to be explicit.



Unknown information should never be presented as certainty.



---



# Interface Stability



The interface should evolve slowly.



New capabilities should be additive whenever possible.



Breaking changes require:



Architectural Review



ADR



Migration Strategy



Compatibility Assessment



Stable interfaces protect long-term maintainability.



---



# Version Compatibility



Modules should declare compatibility with framework versions.



Example



Framework 1.x



↓



Compatible Module Interface v1



Future interface versions should prioritize backward compatibility whenever practical.



---



# Trust Boundary



The Framework trusts modules to provide accurate domain knowledge.



Modules trust the framework to evaluate that knowledge consistently.



Neither layer should assume responsibilities belonging to the other.



This separation preserves architectural integrity.



---



# Summary



Modules are not extensions of the framework.



Modules are independent domain experts.



The framework provides reasoning.



Modules provide expertise.



The interface between them protects both architectural stability and long-term scalability.

