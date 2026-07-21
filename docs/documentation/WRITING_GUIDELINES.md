# WRITING\_GUIDELINES



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This document defines the official writing style for all documentation within the SAM Framework.



The objective is not literary quality.



The objective is architectural consistency.



Every document should appear as though it was written by a single architectural team, regardless of the number of contributors.



This document complements:



\- DOCUMENTATION\_PHILOSOPHY.md

\- DOCUMENT\_STRUCTURE.md

\- GLOSSARY.md

\- CONSTITUTION.md



---



# Philosophy



Good documentation reduces uncertainty.



Writing should clarify architecture rather than demonstrate vocabulary.



Readers should understand concepts without needing to interpret writing style.



Consistency is more valuable than creativity.



---



# Primary Objectives



Every document should strive for:



clarity,



precision,



consistency,



traceability,



maintainability,



explainability.



Writing exists to communicate architectural intent.



---



# Audience



Documentation serves multiple audiences simultaneously.



Architects



seek reasoning.



Developers



seek implementation guidance.



Operators



seek operational procedures.



Contributors



seek context.



Future maintainers



seek historical understanding.



Every document should remain understandable to all of them.



---



# Language



English is the official documentation language.



Technical terminology should remain consistent with GLOSSARY.md.



Avoid introducing alternative names for established concepts.



Example



Correct



Operational Memory



Incorrect



Persistent Memory



Knowledge Cache



Learning Store



One concept should have one official name.



---



# Tone



Documentation should remain:



professional,



neutral,



objective,



respectful,



precise.



Avoid:



marketing language,



emotional language,



personal opinions,



informal conversation,



humor inside policy documents.



Architecture should speak through facts.



---



# Writing Style



Prefer simple sentences.



One idea per paragraph.



Avoid unnecessary complexity.



Complex architecture does not require complex writing.



Readers should spend cognitive effort understanding the system, not decoding the prose.



---



# Terminology



Official terminology originates from:



GLOSSARY.md



New terminology should not be introduced casually.



If a new architectural concept is required:



review it,



document it,



approve it,



then incorporate it into the glossary.



Shared vocabulary is architectural infrastructure.



---



# Normative Language



The Framework distinguishes between different levels of requirement.



Must



Mandatory requirement.



Should



Strong recommendation.



May



Optional capability.



Must Not



Prohibited behavior.



Avoid ambiguous wording.



Normative language improves consistency.



---



# Definitions



Define concepts before using them extensively.



Avoid assuming prior knowledge.



Definitions should not be repeated across multiple documents.



Instead, reference GLOSSARY.md.



---



# Examples



Examples exist to clarify concepts.



Examples should:



remain concise,



illustrate principles,



avoid implementation-specific details when possible.



Examples should never replace architectural rules.



---



# Diagrams



Use diagrams only when they improve understanding.



Preferred diagrams:



layer diagrams,



reasoning flows,



dependency graphs,



state transitions,



operational workflows.



Every diagram should communicate architectural information.



Avoid decorative graphics.



---



# Lists



Use lists when presenting:



principles,



requirements,



responsibilities,



steps,



comparisons.



Lists should remain concise.



Avoid excessive nesting.



---



# Tables



Tables should compare structured information.



Examples include:



responsibility matrices,



lifecycle stages,



trust levels,



risk dimensions,



module capabilities.



Tables should simplify comparison rather than increase complexity.



---



# Cross References



When another document already defines a concept,



reference it instead of redefining it.



Prefer:



See GLOSSARY.md



instead of copying definitions.



Documentation should remain interconnected.



---



# Avoid Duplication



Duplicate knowledge creates inconsistency.



Each important concept should have one authoritative source.



Other documents should reference that source.



Repository integrity depends upon minimizing duplication.



---



# Explainability



Every architectural statement should answer one or more questions.



What exists?



Why does it exist?



How does it work?



Why was this design chosen?



What alternatives were rejected?



Explainability is more valuable than exhaustive detail.



---



# Assumptions



Assumptions should be explicitly identified.



Never present assumptions as established facts.



Whenever assumptions influence architecture,



they should be documented.



---



# Uncertainty



Unknown information should be acknowledged.



Acceptable phrases include:



Unknown



Not yet determined



Requires further research



Planned future work



Uncertainty is preferable to unsupported certainty.



---



# Consistency



The same concept should be described consistently throughout the repository.



Differences in wording often indicate differences in meaning.



If different meanings are intended,



they should be documented explicitly.



---



# Accessibility



Documentation should remain readable without requiring deep implementation knowledge.



Avoid unexplained abbreviations.



Avoid provider-specific jargon unless necessary.



Define domain-specific concepts before using them.



---



# Future Evolution



Writing standards evolve more slowly than implementation.



Changes to this document should occur only when they improve long-term repository quality.



Style changes should never invalidate existing documentation unnecessarily.



---



# Relationship with Templates



Writing Guidelines define how documentation is written.



Templates define where information is placed.



Both should evolve independently.



---



# Success Criteria



Documentation follows this standard when:



language is consistent,



terminology matches GLOSSARY.md,



tone remains objective,



requirements use correct normative language,



duplication is minimized,



reasoning is clearly explained.



---



# Summary



The Writing Guidelines establish one architectural voice for the entire SAM repository.



By emphasizing clarity, consistency, explainability, and shared terminology, the Framework ensures that documentation remains coherent regardless of contributor, implementation, or project size.

