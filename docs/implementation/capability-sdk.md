\# Capability SDK



Version: 1.0



Status: Draft



> **Document Type: Implementation Documentation.**
> This document is NOT a Domain Specification. The Capability domain is specified in `docs/specifications/CAPABILITY_SPECIFICATION.md`.



Document Type: Implementation Specification



Audience:

\- Capability Developers

\- Runtime Developers

\- Plugin Developers



Primary Reference



\- docs/specifications/SAM\_FRAMEWORK\_v1.0\_SPECIFICATION.md



Supporting References



\- docs/core/CONSTITUTION.md

\- docs/core/EXECUTION\_MODEL.md

\- modules/openclaw/capabilities/runtime/capability-contract.md

\- modules/openclaw/capabilities/runtime/capability-runtime.md

\- modules/openclaw/capabilities/runtime/capability-registry.md



\---



\# Purpose



This document defines the Software Development Kit (SDK) used to implement capabilities within the SAM Framework.



The SDK standardizes capability structure, lifecycle integration, metadata, validation, execution, evidence generation, and registration.



Every capability shall conform to this SDK.



\---



\# Design Principles



The SDK shall provide:



\- consistent lifecycle

\- strong typing

\- dependency injection

\- contract compliance

\- testability

\- plugin compatibility

\- runtime independence



Capabilities implement business logic.



The runtime manages execution.



\---



\# Capability Architecture



```

Capability



│



├── Metadata



├── Validation



├── Execute



├── Evidence



└── Result

```



Every capability follows the same structure.



\---



\# Base Class



```python

from abc import ABC, abstractmethod



class Capability(ABC):



&#x20;   metadata: CapabilityMetadata



&#x20;   @abstractmethod

&#x20;   async def validate(

&#x20;       self,

&#x20;       context: ExecutionContext

&#x20;   ) -> ValidationResult:

&#x20;       ...



&#x20;   @abstractmethod

&#x20;   async def execute(

&#x20;       self,

&#x20;       context: ExecutionContext

&#x20;   ) -> CapabilityResult:

&#x20;       ...

```



The base class intentionally exposes a minimal interface.



Additional functionality is provided by the runtime.



\---



\# Metadata



Every capability declares immutable metadata.



Example



```python

metadata = CapabilityMetadata(



&#x20;   id="openclaw.health.runtime",



&#x20;   name="Runtime Health Check",



&#x20;   version="1.0.0",



&#x20;   owner="OpenClaw",



&#x20;   risk\_level="Low",



&#x20;   permissions=\["runtime.read"],



&#x20;   rollback\_supported=False



)

```



Metadata is loaded by the Capability Registry.



\---



\# Validation



Validation executes before business logic.



Example



```python

async def validate(self, context):



&#x20;   if context.runtime is None:



&#x20;       return ValidationResult.invalid(



&#x20;           "Runtime unavailable"



&#x20;       )



&#x20;   return ValidationResult.valid()

```



Validation shall never modify system state.



\---



\# Execution



Business logic resides exclusively inside execute().



Example



```python

async def execute(self, context):



&#x20;   status = await context.runtime.health()



&#x20;   return CapabilityResult.success(



&#x20;       data=status



&#x20;   )

```



Capabilities shall never manipulate workflow state directly.



\---



\# Dependency Injection



Dependencies are supplied through ExecutionContext.



Example



```python

class ExecutionContext:



&#x20;   runtime



&#x20;   registry



&#x20;   evidence



&#x20;   audit



&#x20;   knowledge



&#x20;   logger

```



Capabilities never instantiate infrastructure services.



\---



\# Evidence Generation



Evidence is published through the Evidence Store.



Example



```python

evidence = Evidence(



&#x20;   source=self.metadata.id,



&#x20;   type="runtime.health",



&#x20;   payload=status



)



await context.evidence.publish(



&#x20;   evidence



)

```



Evidence becomes immutable after publication.



\---



\# Audit Events



Capabilities record significant events.



Example



```python

await context.audit.record(



&#x20;   event="CapabilityExecuted",



&#x20;   capability=self.metadata.id



)

```



Audit recording is append-only.



\---



\# Logging



Capabilities use structured logging.



Example



```python

context.logger.info(



&#x20;   "Runtime health check",



&#x20;   capability=self.metadata.id



)

```



Logging shall never replace audit events.



\---



\# Error Handling



Recoverable failures return structured results.



Example



```python

return CapabilityResult.failure(



&#x20;   reason="Provider unreachable"



)

```



Unexpected exceptions propagate to the Runtime.



\---



\# Registration



Capabilities register through the Registry.



Example



```python

registry.register(



&#x20;   RuntimeHealthCapability



)

```



Registration loads metadata but does not instantiate the capability.



\---



\# Execution Example



```python

runtime.execute(



&#x20;   capability="openclaw.health.runtime",



&#x20;   context=context



)

```



The Runtime resolves the capability through the Registry.



\---



\# Plugin Support



Third-party capabilities implement the same base class.



Example



```python

class MyProviderCapability(



&#x20;   Capability



):



&#x20;   ...

```



No special plugin API is required.



\---



\# Testing



Each capability should provide:



\- contract tests

\- validation tests

\- execution tests

\- evidence tests

\- audit tests



Example



```python

def test\_metadata():



&#x20;   assert capability.metadata.id

```



\---



\# Capability Lifecycle



```

Instantiate



↓



Validate



↓



Execute



↓



Generate Evidence



↓



Publish Audit



↓



Return Result



↓



Dispose

```



The Runtime owns lifecycle management.



\---



\# Operational Boundaries



Capabilities shall never:



\- modify workflow state

\- call other capabilities directly

\- bypass the Runtime

\- bypass the Registry

\- bypass Audit

\- bypass Evidence



Capabilities remain isolated execution units.



\---



\# Future Evolution



Future SDK versions may add:



\- hooks

\- middleware

\- interceptors

\- streaming execution

\- progress reporting

\- cancellation tokens



without breaking existing capabilities.



\---



\# Summary



The Capability SDK provides a uniform programming model for every capability in the SAM Framework.



By enforcing a common structure, dependency injection, metadata, validation, evidence generation, and lifecycle integration, the SDK enables consistent, testable, and extensible capability implementations.

