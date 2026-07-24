\# Repository Structure Specification



Version: 1.0



Status: Draft



Document Type: Implementation Specification



Audience:

\- Runtime Developers

\- Capability Developers

\- Contributors

\- Maintainers



Primary Reference



\- docs/specifications/SAM\_FRAMEWORK\_v1.0\_SPECIFICATION.md



Supporting References



\- docs/core/CONSTITUTION.md

\- docs/core/EXECUTION\_MODEL.md

\- docs/GLOSSARY.md



\---



\# Purpose



This document defines the canonical repository structure for the SAM Framework implementation.



The directory layout reflects architectural responsibilities rather than technical layers.



Every directory shall have a single responsibility.



\---



\# Design Principles



Repository organization follows these principles:



\- Capability-first

\- Runtime-centric

\- Explicit boundaries

\- Testable modules

\- Plugin-oriented

\- Documentation close to implementation



The repository structure shall mirror the architecture defined in SAM Framework v1.0.



\---



\# Top-Level Structure



```

openclaw/



docs/

modules/

implementation/



src/

tests/



scripts/



examples/



tools/



assets/



configs/



pyproject.toml

README.md

```



\---



\# src/



Contains executable source code.



```

src/



core/

runtime/

registry/

workflow/

contracts/

dsl/

storage/

events/

audit/

knowledge/

memory/

shared/



capabilities/

plugins/

```



No documentation belongs here.



\---



\# src/core/



Core framework primitives.



Responsibilities:



\- execution context

\- dependency injection

\- lifecycle

\- configuration loading

\- service discovery



Contains no capability-specific logic.



\---



\# src/runtime/



Capability Runtime implementation.



Responsibilities:



\- lifecycle management

\- execution state

\- runtime context

\- execution coordinator



Implements capability-runtime.md.



\---



\# src/registry/



Capability Registry.



Responsibilities:



\- discovery

\- registration

\- dependency resolution

\- version compatibility



Implements capability-registry.md.



\---



\# src/contracts/



Capability contracts.



Responsibilities:



\- interfaces

\- metadata schema

\- validation

\- compatibility



No execution logic.



\---



\# src/workflow/



Workflow Engine.



Responsibilities:



\- workflow graph

\- scheduling

\- state

\- transitions

\- execution policies



Implements workflow-engine.md.



\---



\# src/dsl/



Orchestration Language.



Responsibilities:



\- parser

\- validator

\- serializer

\- compiler



Transforms workflow definitions into execution graphs.



\---



\# src/storage/



Persistent storage abstractions.



Examples:



\- Evidence Store

\- Knowledge Store

\- Audit Store

\- Pattern Store



Storage implementation remains replaceable.



\---



\# src/events/



Event system.



Responsibilities:



\- event bus

\- subscribers

\- publishers

\- dispatch



Entire runtime communicates through events.



\---



\# src/audit/



Audit infrastructure.



Responsibilities:



\- audit records

\- execution trace

\- reasoning trace

\- history



Audit remains append-only.



\---



\# src/knowledge/



Knowledge subsystem.



Responsibilities:



\- institutional knowledge

\- recommendations

\- operational reports



Implements Sprint 4 capabilities.



\---



\# src/memory/



Memory subsystem.



Responsibilities:



\- execution history

\- evidence correlation

\- pattern persistence



Independent from runtime execution.



\---



\# src/shared/



Shared utilities.



Examples:



\- identifiers

\- timestamps

\- exceptions

\- logging

\- serialization



Business logic shall not reside here.



\---



\# src/capabilities/



Built-in capabilities.



Example



```

capabilities/



observation/



diagnostics/



reasoning/



execution/



verification/



recovery/



learning/



governance/

```



Each capability owns its implementation.



\---



\# src/plugins/



External capability plugins.



Plugins shall not modify framework internals.



Discovery occurs through the Capability Registry.



\---



\# tests/



Testing hierarchy.



```

tests/



contracts/



unit/



integration/



workflow/



simulation/



fixtures/

```



Testing mirrors architecture.



\---



\# tests/contracts/



Contract compliance tests.



Highest implementation priority.



Every capability must pass contract tests before integration.



\---



\# tests/unit/



Isolated module tests.



No external dependencies.



\---



\# tests/integration/



Subsystem interaction.



Examples:



Registry ↔ Runtime



Workflow ↔ Runtime



Runtime ↔ Audit



\---



\# tests/workflow/



End-to-end workflow execution.



Focuses on orchestration.



\---



\# tests/simulation/



Operational scenarios.



Examples:



Provider failure



Rollback



Recovery



Reasoning



Autonomous execution



\---



\# scripts/



Developer utilities.



Examples:



bootstrap



lint



format



generate-registry



verify-contracts



\---



\# examples/



Reference implementations.



Examples:



Simple Capability



Workflow



Provider Plugin



Recovery Workflow



\---



\# tools/



Development tooling.



Examples:



registry-inspector



workflow-visualizer



audit-viewer



knowledge-export



\---



\# configs/



Runtime configuration.



Examples:



runtime.toml



providers.toml



logging.toml



Capabilities never modify files directly.



\---



\# Dependency Direction



```

Capabilities



↓



Contracts



↓



Runtime



↓



Workflow



↓



Core

```



Dependencies shall point downward only.



Circular dependencies are prohibited.



\---



\# Repository Evolution



Future directories may include:



distributed/



remote/



cluster/



marketplace/



sdk/



telemetry/



without restructuring existing modules.



\---



\# Summary



The repository structure directly mirrors the SAM architectural model.



Every directory has one responsibility.



Architecture and implementation remain aligned.

