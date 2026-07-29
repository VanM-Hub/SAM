# Provider Model



Version: 1.0



Status: Draft



Owner: OpenClaw Module



Related Documents



Knowledge



\- ../knowledge/providers.md

\- ../knowledge/models.md

\- ../knowledge/runtime.md

\- ../knowledge/configuration.md



Architecture



\- components.md

\- runtime-flow.md

\- data-flow.md



Framework



\- docs/DEPENDENCY\_RULES.md

\- docs/MODULE\_INTERFACE.md

\- docs/ARCHITECTURE.md



---



# Purpose



This document describes how the Runtime interacts with AI Providers.



Unlike `providers.md`, which defines what a Provider is, this document explains the architectural interaction model between the Runtime, Providers, and Models.



The goal is to maintain a stable Runtime architecture regardless of the number or type of supported Providers.



---



# Architectural Principle



Providers are integration adapters.



The Runtime depends on provider capabilities rather than provider implementations.



This separation allows OpenClaw to evolve independently from external AI ecosystems.



---



# High-Level Model



```

&#x20;                Runtime

&#x20;                   │

&#x20;                   ▼

&#x20;         Provider Interface

&#x20;       ┌────────┼────────┐

&#x20;       ▼        ▼        ▼

&#x20;   Provider A Provider B Provider C

&#x20;       │        │        │

&#x20;       ▼        ▼        ▼

&#x20;    Models   Models   Models

```



The Runtime communicates only with the Provider Interface.



Individual Providers implement that interface.



---



# Responsibilities



## Runtime



Responsible for:



\- selecting the Provider,

\- invoking Provider operations,

\- handling Provider responses,

\- coordinating execution.



The Runtime should never contain provider-specific logic.



---



## Provider



Responsible for:



\- authentication,

\- request translation,

\- capability exposure,

\- response normalization,

\- error reporting.



Providers adapt external systems to the OpenClaw architecture.



---



## Model



Responsible only for inference.



Models never communicate directly with the Runtime.



Provider mediation is mandatory.



---



# Provider Interface



Every Provider should expose a consistent conceptual interface.



Typical capabilities include:



\- availability

\- authentication status

\- supported models

\- model invocation

\- capability discovery

\- error reporting



The exact implementation is outside the scope of this document.



---



# Provider Selection



Provider selection is determined by Configuration.



The Runtime should not hard-code Provider selection.



Selection should remain explicit, deterministic, and observable.



---



# Error Isolation



Provider failures should remain isolated.



Examples include:



\- authentication failure,

\- network failure,

\- rate limiting,

\- unsupported model,

\- provider outage.



These failures should not require changes to Runtime architecture.



---



# Model Discovery



Providers expose one or more Models.



The Runtime should obtain Model availability through the Provider rather than maintaining provider-specific knowledge.



This reduces duplication and improves maintainability.



---



# Capability Discovery



Different Providers expose different capabilities.



Examples include:



\- text generation,

\- vision,

\- tool calling,

\- embeddings,

\- reasoning modes,

\- streaming.



Capability discovery should occur through the Provider abstraction rather than Provider-specific Runtime logic.



---



# Dependency Direction



The dependency hierarchy is:



```

Runtime

&#x20;   │

&#x20;   ▼

Provider Interface

&#x20;   │

&#x20;   ▼

Provider Implementation

&#x20;   │

&#x20;   ▼

External AI Service

```



Dependencies always point downward.



External services never become architectural dependencies of the Runtime.



---



# Extensibility



Adding a new Provider should require:



\- implementing the Provider interface,

\- registering Provider metadata,

\- exposing supported Models.



No Runtime redesign should be necessary.



---



# Failure Scenarios



Typical Provider-related failures include:



\- authentication rejected,

\- unavailable endpoint,

\- invalid configuration,

\- incompatible model,

\- timeout,

\- service degradation.



Diagnostics should identify the Provider responsible without affecting unrelated Providers.



---



# Relationship with Data Flow



The Provider Model describes architectural interaction.



Data Flow describes how requests and responses move through those interactions.



Both documents should be read together.



---



# Future Evolution



As the number of supported Providers grows, this architecture may expand into:



architecture/provider/



README.md



provider-interface.md



capability-discovery.md



authentication.md



streaming.md



error-model.md



The conceptual model described here will remain stable while implementation-specific knowledge evolves independently.



---



# Summary



The Provider Model establishes a stable architectural boundary between the Runtime and external AI ecosystems.



By depending on a Provider abstraction rather than individual implementations, OpenClaw achieves extensibility, maintainability, and long-term architectural stability.

