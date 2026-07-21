markdown

# REPOSITORY\_CONVENTION



Version: 1.0

Status: Accepted

Owner: SAM Framework

Last Updated: 2026-07-21



---



# Purpose



This document defines how the SAM repository is organized.



A consistent repository structure improves:



\- discoverability

\- maintainability

\- collaboration

\- scalability



The repository should be understandable without requiring prior knowledge of its history.



---



# Repository Philosophy



The repository is designed around domains rather than file types.



Each directory should represent a responsibility.



Examples:



Framework



Architecture



Modules



Documentation



Assets



Templates



Tests



This separation allows the framework to grow without becoming difficult to navigate.



---



# Repository Layers



The repository consists of six logical layers.



Layer 1



Vision \& Governance



Defines why the project exists and how it evolves.



Files include:



\- VISION.md

\- MISSION.md

\- PRINCIPLES.md

\- GOVERNANCE.md

\- REPOSITORY\_CONVENTION.md

\- GLOSSARY.md



---



Layer 2



Architecture



Defines the structural design of the framework.



Contains:



\- docs/architecture/

\- docs/core/

\- docs/models/

\- docs/adr/



---



Layer 3



Framework



Contains platform-independent concepts.



Examples:



\- Decision Model

\- Thinking Protocol

\- Risk Engine

\- Trust Model

\- Memory Model

\- Execution Model



The framework must not depend on any platform.



---



Layer 4



Modules



Contains platform-specific implementations.



Examples:



\- OpenClaw

\- Docker

\- Linux

\- Windows

\- GitHub

\- Kubernetes



Every module owns its own:



\- architecture/

\- knowledge/

\- playbooks/

\- diagnostics/

\- capabilities/



---



Layer 5



Documentation \& Standards



Defines how the framework is documented and evolved.



Contains:



\- docs/documentation/

\- docs/templates/

\- docs/specifications/



---



Layer 6



Supporting Resources



Assets, templates, examples, utilities, and reference material.



Contains:



\- docs/assets/

\- docs/backlog/

\- scripts/



These resources support development but do not define framework behavior.



---



# Directory Responsibilities



Every directory has one responsibility.



Directories should never become miscellaneous storage locations.



If a directory begins collecting unrelated content, a new directory should be introduced.



---



# Documentation Rules



Every important document should answer three questions.



Why does this exist?



What problem does it solve?



How does it relate to the rest of the framework?



Documentation should emphasize reasoning rather than merely describing implementation.



---



# File Naming



File names should:



be descriptive



remain stable



avoid abbreviations unless widely recognized



Examples:



GOOD



ARCHITECTURE.md



DECISION\_MODEL.md



TRUST\_ENGINE.md



OPENCLAW\_MODULE.md



BAD



doc1.md



notes.md



temp.md



misc.md



---



# Directory Naming



Directory names should represent domains.



Preferred:



framework/



modules/



docs/



assets/



templates/



tests/



Avoid names such as:



misc/



new/



temp/



backup/



old/



stuff/



---



# Module Convention



Each module should follow a consistent internal structure.



Example:

modules/

â””â”€â”€ openclaw/

â”œâ”€â”€ README.md

â”œâ”€â”€ MODULE\_SPECIFICATION.md

â”œâ”€â”€ architecture/

â”‚ â””â”€â”€ README.md

â”œâ”€â”€ knowledge/

â”‚ â””â”€â”€ README.md

â”œâ”€â”€ playbooks/

â”‚ â””â”€â”€ README.md

â”œâ”€â”€ diagnostics/

â”‚ â””â”€â”€ README.md

â””â”€â”€ capabilities/

â”œâ”€â”€ README.md

â””â”€â”€ runtime/

â””â”€â”€ (capability runtime files)



text



The exact contents may evolve, but the philosophy should remain consistent.



---



# Documentation Metadata



Major documents should begin with metadata.



Recommended format:



Version



Status



Owner



Last Updated



This allows documentation to remain manageable over long development cycles.



---



# Cross References



Documents should reference related documents whenever appropriate.



Example:



VISION



â†“



MISSION



â†“



PRINCIPLES



â†“



ARCHITECTURE



â†“



ADR



â†“



FRAMEWORK



â†“



MODULES



This creates a navigable knowledge graph rather than isolated documents.



---



# Source of Truth



The repository is the authoritative source of project knowledge.



Accepted decisions should not exist only inside:



chat conversations



temporary notes



private documents



Once accepted, knowledge belongs in the repository.



---



# Versioning Philosophy



Repository history should tell the story of the framework.



Commits should be:



small



meaningful



reviewable



Examples:



feat: establish governance foundation



docs: define framework vision



adr: adopt framework-first architecture



Avoid commits such as:



update



misc changes



fix



changes



Commit messages should describe intent rather than activity.



---



# Documentation Lifecycle



Documents evolve through four stages.



Draft



â†“



Review



â†“



Accepted



â†“



Archived



Historical documents should not be deleted.



Instead, they should be archived to preserve project history.



---



# Architectural Stability



Architecture should evolve more slowly than implementation.



Framework changes require stronger justification than module changes.



Modules are expected to evolve frequently.



The framework should remain comparatively stable.



---



# Repository Evolution



The repository should grow by extending existing structures rather than introducing parallel systems.



When a new capability is introduced, contributors should first ask:



Can this fit within the existing architecture?



If the answer is yes, extend.



If not, justify the change through an ADR.



---



# Definition of Done



A repository contribution is considered complete only when:



documentation is updated



cross references remain valid



naming follows conventions



architecture remains consistent



future contributors can understand the change



Implementation alone is never considered sufficient.



---



# Summary



The repository is more than a storage location.



It is the permanent knowledge base of the SAM Framework.



Every file should improve understanding.



Every directory should have a clear purpose.



Every change should move the framework toward greater clarity, reliability, and maintainability.

