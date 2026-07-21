<!--

===============================================================================

SAM Framework

Model Documentation Template

===============================================================================



Purpose

-------

Use this template for documents that define a conceptual model within the

SAM Framework.



A Model describes how the Framework understands, evaluates, or represents

a specific domain.



Examples:



\- TRUST\_MODEL.md

\- RISK\_MODEL.md

\- MEMORY\_MODEL.md

\- DECISION\_MODEL.md

\- EXECUTION\_MODEL.md



A Model is not an implementation.



It defines concepts, relationships, rules, and reasoning.



See:



\- DOCUMENT\_STRUCTURE.md

\- WRITING\_GUIDELINES.md

\- ARCHITECTURE.md

\- CONSTITUTION.md



===============================================================================

\-->



# <MODEL\_NAME>



Version:



Status:



Owner:



Last Updated:



Related ADRs:



Related Documents:



Related Modules:



---



<!--

Purpose

-------



Describe WHY this model exists.



Describe which architectural problem it solves.



Do not describe algorithms or implementation.

\-->



# Purpose



---



<!--

Scope

-----



Clearly define what belongs to this model

and what does NOT belong.



A good model has clear boundaries.

\-->



# Scope



Included



\-



Excluded



\-



---



<!--

Problem Statement

-----------------



Describe the architectural problem this model addresses.



The reader should understand why the model is necessary.

\-->



# Problem Statement



---



<!--

Core Concepts

-------------



Define the major concepts used by this model.



Do NOT redefine glossary terms.



Reference GLOSSARY.md whenever appropriate.

\-->



# Core Concepts



| Concept | Description |

|----------|-------------|

| | |



---



<!--

Model Overview

--------------



Describe the overall model.



Explain how concepts interact.



Use diagrams when appropriate.

\-->



# Model Overview



---



<!--

Model Components

----------------



Break the model into logical components.



Each component should have a single responsibility.

\-->



# Model Components



## Component



Purpose



Responsibilities



Inputs



Outputs



Relationships



---



<!--

Reasoning Process

-----------------



Describe how this model reasons.



Explain the logical flow.



Do not describe implementation code.

\-->



# Reasoning Process



```text

Observe



↓



Interpret



↓



Evaluate



↓



Decision



↓



Result

```



---



<!--

Decision Rules

--------------



Describe the rules governing this model.



Use normative language:



Must



Should



May



Must Not

\-->



# Decision Rules



---



<!--

Inputs

-------



Describe information consumed by the model.

\-->



# Inputs



---



<!--

Outputs

--------



Describe what the model produces.



Examples:



Score



Decision



Recommendation



Classification



Risk Level



Trust Level

\-->



# Outputs



---



<!--

Assumptions

-----------



Document assumptions explicitly.



Never hide assumptions.

\-->



# Assumptions



---



<!--

Limitations

-----------



Every model has limitations.



Document them honestly.

\-->



# Limitations



---



<!--

Relationships

-------------



Explain how this model interacts with other models.



Example:



TRUST\_MODEL



↓



DECISION\_MODEL



↓



EXECUTION\_MODEL

\-->



# Relationships



Depends On



\-



Referenced By



\-



Complements



\-



Extends



\-



---



<!--

Dependency Considerations

-------------------------



Reference DEPENDENCY\_RULES.md.



Ensure dependency direction follows Framework architecture.

\-->



# Dependency Considerations



---



<!--

Future Evolution

----------------



Describe expected future extensions.



Avoid speculative implementation details.

\-->



# Future Evolution



---



<!--

Related Documents

-----------------



List canonical filenames only.

\-->



# Related Documents



\-



---



<!--

Author Checklist

----------------

\-->



# Author Checklist



\- \[ ] Purpose clearly defined

\- \[ ] Scope documented

\- \[ ] Concepts explained

\- \[ ] No glossary duplication

\- \[ ] Relationships documented

\- \[ ] Limitations included

\- \[ ] Assumptions documented

\- \[ ] Cross references validated

\- \[ ] Consistent with CONSTITUTION.md



---



<!--

Common Mistakes

---------------

\-->



# Common Mistakes



\- Mixing implementation with concepts.

\- Redefining glossary terminology.

\- Omitting assumptions.

\- Ignoring model boundaries.

\- Using inconsistent terminology.

\- Describing algorithms instead of architectural reasoning.

\- Forgetting relationships to other models.



---



<!--

Completion Checklist

--------------------

\-->



# Completion Checklist



\- \[ ] Metadata complete

\- \[ ] Review completed

\- \[ ] Version updated

\- \[ ] Status updated

\- \[ ] Ready for publication



---



# Summary



Summarize the purpose of the model.



Reinforce its responsibility within the Framework.



Reference related models when appropriate.

