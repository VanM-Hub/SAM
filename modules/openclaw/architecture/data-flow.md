# Data Flow



Version: 1.0



Status: Draft



Owner: OpenClaw Module



Related Documents



Knowledge



\- ../knowledge/cli.md

\- ../knowledge/workspace.md

\- ../knowledge/configuration.md

\- ../knowledge/runtime.md

\- ../knowledge/providers.md

\- ../knowledge/models.md

\- ../knowledge/agents.md



Architecture



\- components.md

\- runtime-flow.md

\- workspace-model.md

\- provider-model.md

\- configuration-model.md

\- agent-model.md



Framework



\- docs/core/THINKING\_PROTOCOL.md

\- docs/core/EXECUTION\_MODEL.md

\- docs/models/MEMORY\_MODEL.md



---



# Purpose



This document describes how information moves through the OpenClaw architecture.



Unlike Runtime Flow, which explains execution order, Data Flow explains how data is created, transformed, consumed, and produced during execution.



---



# Architectural Principles



Data should move through explicit architectural boundaries.



Every transformation should have a responsible component.



Components should exchange well-defined information rather than internal implementation details.



---



# High-Level Data Flow



```

User Input

&#x20;     │

&#x20;     ▼

CLI

&#x20;     │

&#x20;     ▼

Runtime

&#x20;     │

&#x20;     ├────────► Workspace Context

&#x20;     │

&#x20;     ├────────► Effective Configuration

&#x20;     │

&#x20;     ├────────► Provider Request

&#x20;     │                     │

&#x20;     │                     ▼

&#x20;     │               Model Response

&#x20;     │                     │

&#x20;     ▼                     │

Agent Reasoning ◄───────────┘

&#x20;     │

&#x20;     ▼

Operational Result

&#x20;     │

&#x20;     ▼

CLI Output

```



The Runtime coordinates movement.



Each component transforms information within its own responsibility.



---



# Information Objects



The architecture exchanges several logical information objects.



Examples include:



\- user request,

\- workspace context,

\- effective configuration,

\- provider request,

\- provider response,

\- model output,

\- reasoning context,

\- operational result,

\- diagnostic information.



These are conceptual objects rather than implementation-specific data structures.



---



# Stage 1 — User Request



The process begins with user intent.



The CLI transforms raw user interaction into a structured Runtime request.



Typical transformations include:



\- parsing,

\- validation,

\- normalization.



---



# Stage 2 — Context Acquisition



The Runtime acquires execution context.



Context includes:



\- active Workspace,

\- Effective Configuration,

\- execution metadata.



No inference occurs during this stage.



---



# Stage 3 — Provider Request



The Runtime transforms operational intent into a Provider request.



This transformation hides Runtime implementation details from external AI services.



The Provider receives only the information required to perform inference.



---



# Stage 4 — Model Output



The Provider returns Model output.



The Runtime receives normalized information rather than provider-specific representations.



Normalization improves architectural stability.



---



# Stage 5 — Agent Reasoning



The Agent consumes Model output.



Reasoning may include:



\- interpretation,

\- comparison,

\- decision making,

\- planning,

\- response composition.



The Agent produces an operational result rather than raw Model output.



---



# Stage 6 — Response Delivery



The Runtime prepares the final operational result.



The CLI presents the result to the user.



Presentation may include:



\- formatted text,

\- structured output,

\- diagnostics,

\- warnings,

\- execution metadata.



---



# Data Transformation



Information should become progressively more structured during execution.



```

Raw Input

&#x20;     │

&#x20;     ▼

Validated Request

&#x20;     │

&#x20;     ▼

Operational Context

&#x20;     │

&#x20;     ▼

Provider Request

&#x20;     │

&#x20;     ▼

Model Output

&#x20;     │

&#x20;     ▼

Reasoned Result

&#x20;     │

&#x20;     ▼

User Response

```



Each transformation should have one responsible component.



---



# Ownership of Information



Different components own different information.



CLI



\- user interaction



Workspace



\- persistent operational context



Configuration



\- execution intent



Runtime



\- execution state



Provider



\- external communication



Model



\- inference output



Agent



\- reasoning result



Ownership should remain explicit to reduce ambiguity.



---



# Observability



Information movement should be observable whenever practical.



Useful observations include:



\- request identifiers,

\- execution stages,

\- selected Provider,

\- selected Model,

\- execution duration,

\- diagnostic metadata.



Observability improves troubleshooting without changing architectural responsibilities.



---



# Failure Propagation



Information about failures should travel through the same architectural boundaries as successful execution.



Example:



```

Model Error

&#x20;     │

&#x20;     ▼

Provider

&#x20;     │

&#x20;     ▼

Runtime

&#x20;     │

&#x20;     ▼

CLI

&#x20;     │

&#x20;     ▼

User

```



Each layer may enrich error information but should not obscure its origin.



---



# Relationship with Runtime Flow



Runtime Flow explains **when** components interact.



Data Flow explains **what information** moves between those interactions.



Both views describe the same architecture from different perspectives.



---



# Design Principles



## Explicit Transformation



Every data transformation should have an identifiable owner.



---



## No Hidden Mutation



Information should not be modified by components that do not own it.



---



## Traceability



It should be possible to trace a response back through each transformation stage.



---



## Separation of Responsibilities



Data ownership should remain aligned with architectural responsibilities.



---



# Future Evolution



Future documentation may expand this domain into:



architecture/data-flow/



README.md



request-model.md



response-model.md



context-model.md



diagnostic-data.md



streaming.md



event-flow.md



The conceptual model defined here should remain stable regardless of transport mechanisms or implementation technologies.



---



# Summary



The Data Flow Model describes how information moves through OpenClaw from user request to final response.



By separating information movement from execution coordination, the architecture maintains clear responsibilities, improves observability, and supports future evolution without introducing unnecessary coupling.

