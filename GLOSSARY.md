# GLOSSARY



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This document defines the official vocabulary of the SAM Framework.



Every architectural document, module, playbook, research paper, and implementation should use these terms consistently.



When a term is defined here, its meaning should remain stable across the entire repository.



If a term requires a different meaning, the change should be introduced through an Architecture Decision Record (ADR).



---



# Why a Glossary Exists



Large projects gradually develop their own language.



Without a shared vocabulary:



\- contributors interpret concepts differently,

\- documentation becomes inconsistent,

\- architectural discussions become ambiguous,

\- implementation slowly diverges from design.



The glossary establishes one common language.



---



# Framework



The platform-independent core of SAM.



The Framework defines how intelligent operational reasoning is performed.



It owns:



\- reasoning

\- decision models

\- governance

\- architecture

\- operational philosophy



It never owns platform-specific knowledge.



---



# Module



A self-contained operational domain implementing one specific platform.



Examples include:



\- OpenClaw

\- Docker

\- Linux

\- Kubernetes



Modules provide expertise.



They do not define framework behavior.



---



# Knowledge



Verified or observed information about one operational domain.



Knowledge includes:



\- documentation

\- provider behavior

\- known issues

\- configuration

\- research

\- compatibility



Knowledge answers:



"What is true?"



---



# Reasoning



The process of interpreting knowledge.



Reasoning transforms evidence into conclusions.



Reasoning belongs to the Framework.



---



# Evidence



Information supporting a conclusion.



Evidence may originate from:



official documentation



runtime observations



configuration analysis



diagnostic results



reproducible experiments



Evidence always carries a confidence level.



---



# Trust



The degree of confidence assigned to available evidence.



Trust is not certainty.



Trust represents the reliability of available information.



---



# Risk



The probability and potential impact of an undesirable outcome.



Risk evaluation considers:



likelihood



severity



recoverability



operational impact



Risk belongs to the Framework.



---



# Playbook



A documented operational procedure.



Playbooks transform knowledge into repeatable actions.



Knowledge explains.



Playbooks instruct.



---



# Automation



The execution of approved operational procedures.



Automation consumes:



Framework



Modules



Knowledge



Playbooks



Automation should never replace reasoning.



---



# Governance



The rules governing how SAM evolves.



Governance includes:



principles



repository conventions



documentation standards



decision process



Governance protects architectural consistency.



---



# Architecture



The structural organization of the Framework.



Architecture defines:



layers



boundaries



dependencies



interfaces



Architecture explains structure.



ADR explains why that structure exists.



---



# Architecture Decision Record (ADR)



A permanent record explaining an important architectural decision.



Each ADR should document:



the decision,



its rationale,



alternatives considered,



consequences.



ADR preserves architectural history.



---



# Layer



A responsibility boundary within the architecture.



Each layer owns exactly one primary responsibility.



Layers should remain independent.



---



# Dependency



A relationship where one component relies on another.



Dependencies must always follow the architectural direction defined in DEPENDENCY\_RULES.md.



---



# Interface



A stable architectural contract between the Framework and Modules.



Interfaces define communication.



They do not expose implementation details.



---



# Capability



A service provided by a Module.



Examples:



configuration validation,



provider inspection,



diagnostics,



knowledge retrieval.



Capabilities describe what a Module can do.



Not how it does it.



---



# Operational Domain



A distinct area of expertise represented by one Module.



Each operational domain evolves independently.



Examples:



OpenClaw



Docker



GitHub



Windows



---



# Repository



The authoritative knowledge base of the SAM project.



Repository contents supersede temporary discussions.



Accepted knowledge belongs in the repository.



---



# Vocabulary



The collection of officially defined terms used throughout SAM.



Vocabulary enables precise communication between contributors, documentation, and implementations.



---



# Cross References



This glossary complements:



\- VISION.md

\- MISSION.md

\- PRINCIPLES.md

\- GOVERNANCE.md

\- ARCHITECTURE.md

\- LAYERS.md

\- MODULE\_INTERFACE.md



Future documents should reference this glossary rather than redefining existing terms.



---



# Summary



A shared vocabulary is a prerequisite for a shared architecture.



The glossary exists to ensure that every contributor, module, and document speaks the same language.



As SAM evolves, new terms may be added, but existing definitions should change only through deliberate architectural decisions.

