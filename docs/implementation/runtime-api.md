\# Runtime API Specification



Version: 1.0



Status: Draft



Document Type: Implementation Specification



Audience:

\- Runtime Developers

\- Capability Developers

\- SDK Developers



Primary Reference



\- docs/specifications/SAM\_FRAMEWORK\_v1.0\_SPECIFICATION.md



Supporting References



\- docs/core/CONSTITUTION.md

\- docs/core/EXECUTION\_MODEL.md

\- modules/openclaw/capabilities/runtime/capability-runtime.md

\- modules/openclaw/capabilities/runtime/capability-registry.md

\- modules/openclaw/capabilities/runtime/workflow-engine.md



\---



\# Purpose



This document defines the public Runtime APIs used throughout the SAM Framework.



The Runtime API is the only supported interface between runtime services and capability implementations.



Capabilities interact with services through these APIs.



They never access internal implementation details.



\---



\# Design Principles



Runtime APIs shall be:



\- stable

\- strongly typed

\- asynchronous

\- deterministic

\- auditable

\- implementation independent



Every API returns structured objects.



Exceptions represent unexpected failures only.



\---



\# Runtime Services



The runtime exposes the following service groups.



```

Runtime



├── Registry

├── Workflow

├── Evidence

├── Audit

├── Knowledge

├── Memory

├── EventBus

└── Runtime

```



Each service owns a single responsibility.



\---



\# Registry API



Purpose



Discover and resolve capabilities.



Example



```python

class CapabilityRegistry:



&#x20;   async def register(

&#x20;       self,

&#x20;       capability: type\[Capability]

&#x20;   ) -> None:

&#x20;       ...



&#x20;   async def unregister(

&#x20;       self,

&#x20;       capability\_id: str

&#x20;   ) -> None:

&#x20;       ...



&#x20;   async def get(

&#x20;       self,

&#x20;       capability\_id: str

&#x20;   ) -> CapabilityMetadata:

&#x20;       ...



&#x20;   async def list(self):



&#x20;       ...



&#x20;   async def exists(

&#x20;       self,

&#x20;       capability\_id: str

&#x20;   ) -> bool:

&#x20;       ...

```



Registry APIs manipulate metadata only.



Execution belongs to the Runtime.



\---



\# Runtime API



Purpose



Execute capabilities.



Example



```python

class Runtime:



&#x20;   async def execute(



&#x20;       self,



&#x20;       capability\_id: str,



&#x20;       context: ExecutionContext



&#x20;   ) -> CapabilityResult:



&#x20;       ...

```



The Runtime owns lifecycle management.



Capabilities shall never instantiate themselves.



\---



\# Workflow API



Purpose



Execute workflows.



Example



```python

class WorkflowEngine:



&#x20;   async def start(



&#x20;       self,



&#x20;       workflow: WorkflowDefinition,



&#x20;       context: ExecutionContext



&#x20;   ) -> WorkflowResult:



&#x20;       ...



&#x20;   async def stop(



&#x20;       self,



&#x20;       execution\_id: str



&#x20;   ) -> None:



&#x20;       ...



&#x20;   async def status(



&#x20;       self,



&#x20;       execution\_id: str



&#x20;   ) -> WorkflowStatus:



&#x20;       ...

```



Workflow execution remains deterministic.



\---



\# Evidence API



Purpose



Publish immutable evidence.



Example



```python

class EvidenceStore:



&#x20;   async def publish(



&#x20;       self,



&#x20;       evidence: Evidence



&#x20;   ) -> EvidenceReference:



&#x20;       ...



&#x20;   async def get(



&#x20;       self,



&#x20;       evidence\_id: str



&#x20;   ) -> Evidence:



&#x20;       ...



&#x20;   async def search(



&#x20;       self,



&#x20;       query: EvidenceQuery



&#x20;   ) -> list\[Evidence]:



&#x20;       ...

```



Evidence cannot be modified after publication.



\---



\# Audit API



Purpose



Record operational events.



Example



```python

class AuditStore:



&#x20;   async def record(



&#x20;       self,



&#x20;       event: AuditEvent



&#x20;   ) -> AuditReference:



&#x20;       ...



&#x20;   async def history(



&#x20;       self,



&#x20;       execution\_id: str



&#x20;   ) -> list\[AuditEvent]:



&#x20;       ...

```



Audit is append-only.



\---



\# Knowledge API



Purpose



Persist institutional knowledge.



Example



```python

class KnowledgeStore:



&#x20;   async def store(



&#x20;       self,



&#x20;       knowledge: Knowledge



&#x20;   ) -> KnowledgeReference:



&#x20;       ...



&#x20;   async def find(



&#x20;       self,



&#x20;       query: KnowledgeQuery



&#x20;   ) -> list\[Knowledge]:



&#x20;       ...

```



Knowledge evolves through Sprint 4 mechanisms.



\---



\# Memory API



Purpose



Store operational history.



Example



```python

class MemoryStore:



&#x20;   async def append(



&#x20;       self,



&#x20;       record: MemoryRecord



&#x20;   ) -> None:



&#x20;       ...



&#x20;   async def timeline(



&#x20;       self,



&#x20;       execution\_id: str



&#x20;   ) -> list\[MemoryRecord]:



&#x20;       ...

```



Memory is chronological.



\---



\# Event Bus API



Purpose



Coordinate runtime events.



Example



```python

class EventBus:



&#x20;   async def publish(



&#x20;       self,



&#x20;       event: RuntimeEvent



&#x20;   ) -> None:



&#x20;       ...



&#x20;   async def subscribe(



&#x20;       self,



&#x20;       event\_type: str,



&#x20;       handler



&#x20;   ) -> None:



&#x20;       ...

```



Publishers remain unaware of subscribers.



\---



\# Execution Context



Every runtime API receives the same execution context.



Example



```python

context = ExecutionContext(



&#x20;   runtime=runtime,



&#x20;   registry=registry,



&#x20;   evidence=evidence,



&#x20;   audit=audit,



&#x20;   knowledge=knowledge,



&#x20;   memory=memory,



&#x20;   events=event\_bus,



&#x20;   logger=logger



)

```



ExecutionContext acts as the dependency injection container.



\---



\# Typical Execution Flow



```

Registry.get()



↓



Runtime.execute()



↓



Capability.execute()



↓



Evidence.publish()



↓



Audit.record()



↓



Knowledge.store()



↓



Memory.append()



↓



Workflow.complete()

```



Each step is independently testable.



\---



\# Error Model



Recoverable conditions return structured results.



Unexpected failures raise exceptions.



Example



```python

CapabilityResult.success()



CapabilityResult.failure()



ValidationResult.invalid()

```



Exceptions never represent expected operational outcomes.



\---



\# API Versioning



Every public API shall expose:



\- API Version

\- Compatibility Version

\- Deprecation Status



Breaking changes require a new major version.



\---



\# Operational Boundaries



Runtime APIs shall never:



\- expose internal storage

\- bypass contracts

\- bypass audit

\- bypass evidence

\- expose implementation classes



Only public contracts are stable.



\---



\# Future Evolution



Future Runtime APIs may include:



\- distributed execution

\- remote registry

\- streaming evidence

\- workflow checkpointing

\- event replay

\- telemetry



without breaking existing contracts.



\---



\# Summary



The Runtime API defines the stable programming interface of the SAM Framework.



By exposing explicit services for registry, runtime execution, workflows, evidence, audit, memory, and knowledge, the API preserves architectural boundaries while enabling modular, testable, and extensible implementations.

