# Documentation Templates



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



This directory contains the official document templates used throughout the SAM Framework.



Templates exist to ensure that every document follows the architectural policies defined by the repository.



A template is not merely a formatting aid.



It is an implementation of the documentation standards established by:



\- DOCUMENTATION\_PHILOSOPHY.md

\- DOCUMENT\_STRUCTURE.md

\- WRITING\_GUIDELINES.md

\- CROSS\_REFERENCE\_RULES.md

\- VERSIONING.md

\- REVIEW\_PROCESS.md

\- DOCUMENT\_LIFECYCLE.md



---



# Philosophy



Documentation should not depend on individual writing style.



Instead, documentation should be produced from a consistent architectural process.



Templates translate documentation policy into repeatable practice.



Every contributor should be able to create documentation that is structurally identical to documentation written by the Framework maintainers.



---



# Design Principles



The template system follows several principles.



\- Policy before template.

\- One responsibility per template.

\- Explain before prescribe.

\- Minimize ambiguity.

\- Encourage architectural thinking.

\- Support long-term maintenance.



---



# Template Structure



Every template is organized into four logical layers.



---



## Layer 1 — Instructional Comments



Instructional comments are written using HTML comments.



Example:



```markdown

<!--

Explain why this section exists.



Describe what information belongs here.



Avoid implementation details.



Reference related documents when appropriate.

\-->

```



These comments are intended for authors.



They are removed or ignored in rendered documentation.



---



## Layer 2 — Metadata



Every document begins with standardized metadata.



Typical fields include:



\- Version

\- Status

\- Owner

\- Last Updated



Additional metadata may be added when appropriate.



Metadata improves governance and traceability.



---



## Layer 3 — Document Skeleton



The skeleton follows DOCUMENT\_STRUCTURE.md.



Typical sections include:



Purpose



Scope



Core Content



Design Principles



Relationships



Future Evolution



Summary



Document types may introduce additional sections where justified.



---



## Layer 4 — Author Guidance



Every template concludes with guidance for contributors.



This may include:



Author Checklist



Common Mistakes



Related Documents



Completion Checklist



These sections improve documentation quality before review begins.



---



# How to Use Templates



Step 1



Choose the template that matches the intended document.



Step 2



Duplicate the template into the appropriate repository location.



Step 3



Replace instructional comments with actual content.



Step 4



Remove any unused placeholder text.



Step 5



Review the document using REVIEW\_PROCESS.md.



Step 6



Submit the document for review.



---



# Choosing the Correct Template



| If you are writing... | Use... |

|------------------------|---------|

| Architecture decision | ADR\_TEMPLATE.md |

| Architectural model | MODEL\_TEMPLATE.md |

| Module specification | MODULE\_TEMPLATE.md |

| Architecture overview | ARCHITECTURE\_TEMPLATE.md |

| Governance document | GOVERNANCE\_TEMPLATE.md |

| Operational procedure | PLAYBOOK\_TEMPLATE.md |

| Operational knowledge | KNOWLEDGE\_TEMPLATE.md |

| Incident report | INCIDENT\_TEMPLATE.md |

| Research document | RESEARCH\_TEMPLATE.md |

| General decision log | DECISION\_RECORD\_TEMPLATE.md |



---



# Template Modification



Templates represent repository standards.



Significant modifications should follow the documentation review process.



Repository-specific customization should preserve compatibility with DOCUMENT\_STRUCTURE.md.



---



# Common Mistakes



Avoid:



Using the wrong template.



Leaving instructional comments in published documents.



Duplicating glossary definitions.



Changing document structure without justification.



Mixing multiple responsibilities into one document.



Skipping metadata.



---



# Related Documents



This directory is governed by:



\- DOCUMENTATION\_PHILOSOPHY.md

\- DOCUMENT\_STRUCTURE.md

\- WRITING\_GUIDELINES.md

\- REVIEW\_PROCESS.md

\- DOCUMENT\_LIFECYCLE.md



---



# Summary



Templates provide a consistent foundation for all documentation within the SAM Framework.



By implementing repository policies in a reusable format, templates improve quality, reduce ambiguity, and help every contributor produce documentation that is architecturally consistent.

