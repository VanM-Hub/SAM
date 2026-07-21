<!--

===============================================================================

SAM Framework

Module Documentation Template

===============================================================================



Purpose

-------

Use this template to document a Framework Module.



A Module is a self-contained capability that extends the Framework through

well-defined interfaces while respecting dependency rules and architectural

boundaries.



A Module owns behavior.



It does not own Framework policy.



See:



\- FRAMEWORK\_VS\_MODULE.md

\- MODULE\_INTERFACE.md

\- DEPENDENCY\_RULES.md

\- ARCHITECTURE.md

\- CONSTITUTION.md



===============================================================================

\-->



# <MODULE NAME>



Version:



Status:



Owner:



Maintainers:



Last Updated:



Related ADRs:



Related Models:



Related Documents:



---



<!--

Purpose

-------



Describe the responsibility of this module.



State what capability it provides.



Keep this section focused on responsibility,

not implementation.

\-->



# Purpose



---



<!--

Scope

-----



Clearly define module boundaries.



Document both included and excluded responsibilities.



A module should have one primary responsibility.

\-->



# Scope



## Included



\-



## Excluded



\-



---



<!--

Problem Statement

-----------------



Explain why this module exists.



Describe the capability gap that it fills.



Avoid implementation details.

\-->



# Problem Statement



---



<!--

Responsibilities

----------------



List the responsibilities owned by this module.



Each responsibility should be explicit.



Responsibilities should not overlap with other modules.

\-->



# Responsibilities



\-



---



<!--

Capabilities

------------



Describe the observable capabilities provided

by this module.



Capabilities are externally visible behavior.

\-->



# Capabilities



| Capability | Description |

|------------|-------------|

| | |



---



<!--

Public Interface

----------------



Describe the contract exposed by the module.



Do not document internal implementation.



Focus on expected behavior.

\-->



# Public Interface



## Inputs



\-



## Outputs



\-



## Events



\-



## Errors



\-



---



<!--

Dependencies

------------



List only direct dependencies.



Reference DEPENDENCY\_RULES.md.



Document why each dependency exists.



Avoid unnecessary coupling.

\-->



# Dependencies



| Dependency | Reason |

|------------|--------|

| | |



---



<!--

Dependency Constraints

----------------------



Document forbidden dependencies.



Explain architectural reasoning.



Examples:



Must Not depend on UI.



Must Not depend on OpenClaw.



Must Not bypass Framework Services.

\-->



# Dependency Constraints



Allowed



\-



Forbidden



\-



---



<!--

Internal Components

-------------------



Describe the major internal components.



Focus on responsibilities.



Do not describe implementation details.

\-->



# Internal Components



## Component



Purpose



Responsibilities



Relationships



---



<!--

Interactions

------------



Describe interaction with the Framework

and other modules.



Sequence diagrams may be included.



Focus on contracts rather than implementation.

\-->



# Interactions



---



<!--

Operational Behavior

--------------------



Describe runtime behavior.



Examples:



Initialization



Shutdown



Health Monitoring



Recovery



Background Tasks

\-->



# Operational Behavior



---



<!--

Configuration

-------------



Describe externally configurable behavior.



Configuration should not redefine architecture.

\-->



# Configuration



---



<!--

Failure Handling

----------------



Describe expected failures.



Document recovery expectations.



Reference PLAYBOOK documents where applicable.

\-->



# Failure Handling



---



<!--

Observability

-------------



Describe how the module exposes operational visibility.



Examples:



Logs



Metrics



Health Checks



Events



Tracing

\-->



# Observability



---



<!--

Security Considerations

-----------------------



Describe security assumptions,

privileges,

sensitive resources,

trust boundaries.

\-->



# Security Considerations



---



<!--

Risk Considerations

-------------------



Summarize architectural risks.



Reference RISK\_MODEL.md.



Avoid implementation-specific vulnerabilities.

\-->



# Risk Considerations



---



<!--

Evolution Strategy

------------------



Describe expected future evolution.



Do not create speculative roadmap items.



Focus on architectural direction.

\-->



# Evolution Strategy



---



<!--

Relationships

-------------



Describe relationships with:



Framework



Models



Modules



ADRs



Playbooks

\-->



# Relationships



Depends On



\-



Referenced By



\-



Related Models



\-



Related ADRs



\-



---



<!--

Related Documents

-----------------

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

\- \[ ] Responsibilities identified

\- \[ ] Public interface documented

\- \[ ] Dependencies justified

\- \[ ] Forbidden dependencies listed

\- \[ ] Failure handling described

\- \[ ] Risks documented

\- \[ ] Cross references validated

\- \[ ] Consistent with CONSTITUTION.md



---



<!--

Common Mistakes

---------------

\-->



# Common Mistakes



\- Mixing Framework responsibilities into the module.

\- Documenting implementation instead of behavior.

\- Creating hidden dependencies.

\- Omitting dependency rationale.

\- Ignoring operational behavior.

\- Forgetting observability requirements.

\- Defining multiple unrelated responsibilities.



---



<!--

Completion Checklist

--------------------

\-->



# Completion Checklist



\- \[ ] Metadata complete

\- \[ ] Review completed

\- \[ ] Version assigned

\- \[ ] Status assigned

\- \[ ] Cross references verified

\- \[ ] Ready for publication



---



# Summary



Summarize the module in a concise form.



Reinforce:



its responsibility,



its public contract,



its architectural boundaries,



and its role within the Framework.

