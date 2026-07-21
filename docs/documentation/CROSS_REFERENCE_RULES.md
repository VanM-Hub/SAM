# CROSS\_REFERENCE\_RULES



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This document defines how documentation within the SAM Framework references other documentation.



Cross references are architectural relationships.



They are not merely navigation aids.



Every reference communicates dependency, context, ownership, extension, or rationale.



Consistent cross references transform the repository from a collection of documents into a connected knowledge system.



---



# Philosophy



Documentation should form a knowledge graph.



Each document is a node.



Each reference is an edge.



Understanding a document should naturally lead readers toward related knowledge.



No important architectural document should exist in isolation.



---



# Objectives



Cross references exist to:



improve discoverability,



reduce duplication,



strengthen traceability,



clarify dependencies,



preserve architectural context,



support long-term maintainability.



---



# Guiding Principles



The Framework follows these principles.



Reference instead of duplicate.



Prefer authoritative sources.



Keep relationships explicit.



Maintain directional consistency.



Avoid circular explanations.



Architecture should remain navigable.



---



# Types of Relationships



Every reference represents one specific relationship.



---



## Depends On



The current document requires another document to be understood correctly.



Example



MODULE\_INTERFACE.md



depends on



ARCHITECTURE.md



---



## References



The document cites another document for additional explanation.



Understanding does not require reading the referenced document.



---



## Complements



Both documents describe different aspects of the same architectural concept.



Example



TRUST\_MODEL.md



complements



RISK\_MODEL.md



---



## Extends



The current document expands an existing concept.



Example



OPENCLAW\_AS\_MODULE.md



extends



FRAMEWORK\_VS\_MODULE.md



---



## Implements



The document describes a concrete implementation of higher-level policy.



Example



MODULE\_TEMPLATE.md



implements



DOCUMENT\_STRUCTURE.md



---



## Governed By



The document is constrained by higher-level policy.



Example



EXECUTION\_MODEL.md



is governed by



CONSTITUTION.md



---



## Related ADR



Architecture Decision Records connected to this document.



Example



ADR-001



Architectural Layering



---



# Canonical References



References should always use canonical filenames.



Correct



ARCHITECTURE.md



Incorrect



Architecture



Architecture Guide



Main Architecture



Consistency improves navigation.



---



# Reference Direction



References should generally flow downward through architectural layers.



Constitution



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



Implementation



Lower layers should not redefine higher layers.



---



# Bidirectional Awareness



Not every reference must be physically bidirectional.



However,



architectural relationships should be discoverable.



Repository tooling may later generate reverse-reference indexes automatically.



---



# Avoid Circular Reasoning



Documents may reference each other.



They should never depend upon each other to define the same concept.



Incorrect



Document A defines B.



Document B defines A.



Correct



One document owns the definition.



The other references it.



---



# Single Source of Truth



Every architectural concept should have one authoritative document.



Examples



Trust



↓



TRUST\_MODEL.md



Risk



↓



RISK\_MODEL.md



Operational Memory



↓



MEMORY\_MODEL.md



Other documents should reference these sources instead of redefining them.



---



# Cross References and the Glossary



Definitions should originate from GLOSSARY.md.



Documents should reference the glossary rather than repeating definitions.



Vocabulary belongs to the glossary.



Context belongs to individual documents.



---



# Relationship Sections



Major architectural documents should contain a dedicated Relationships section.



Typical entries include:



Depends On



Governed By



Related ADR



Related Modules



Complementary Documents



Future Extensions



This improves repository navigation.



---



# References in Templates



Official templates should include a standard Related Documents section.



Template consistency supports automated tooling in the future.



---



# External References



External references should be used sparingly.



Preferred order:



Official project documentation



Relevant standards



Peer-reviewed publications



Vendor documentation



Community resources



External references should never replace internal architectural documentation.



---



# Future Automation



The Framework may automatically generate:



dependency graphs,



document maps,



knowledge graphs,



impact analysis,



reference validation,



or orphan document detection.



Consistent cross references enable these capabilities.



---



# Anti-Patterns



Avoid:



duplicating definitions,



ambiguous references,



broken references,



provider-specific assumptions,



hidden dependencies,



undocumented relationships.



Every architectural dependency should be visible.



---



# Relationship with Architecture



Cross references should mirror architectural boundaries.



If documentation dependencies violate architectural layering,



the architecture should be reviewed.



Documentation often reveals architectural problems before implementation does.



---



# Relationship with Governance



Cross references are governed by:



CONSTITUTION.md



GOVERNANCE.md



DOCUMENT\_STRUCTURE.md



WRITING\_GUIDELINES.md



Changes affecting repository-wide reference behavior require architectural review.



---



# Success Criteria



The repository satisfies this standard when:



important concepts have authoritative sources,



relationships are explicit,



navigation is predictable,



duplication is minimized,



architectural dependencies remain visible,



future tooling can analyze document relationships.



---



# Summary



Cross references transform documentation into a connected architectural knowledge system.



By treating references as explicit architectural relationships rather than simple hyperlinks, the SAM Framework preserves context, improves maintainability, and enables future automation such as dependency analysis and knowledge graph generation.

