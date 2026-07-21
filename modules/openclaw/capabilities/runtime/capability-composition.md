# Capability Composition



Version: 1.0



Status: Draft



Capability Type: Runtime Architecture



Execution Mode: Orchestration



Risk Level: Low



Owner: OpenClaw Module



Related Documents



Capabilities



\- runtime/capability-runtime.md

\- runtime/capability-registry.md

\- runtime/capability-contract.md

\- runtime/workflow-engine.md

\- runtime/orchestration-language.md



Sprint 3



\- approval-gate.md

\- execution-planning.md



Sprint 5



\- diagnostic-reasoning-engine.md



Framework



\- docs/core/EXECUTION\_MODEL.md

\- docs/models/DECISION\_MODEL.md



---



# Purpose



Define how capabilities are composed into larger operational workflows.



Capability Composition describes the logical relationships between capabilities, how they coordinate, and how they exchange information.



---



# Scope



Capability Composition covers:



\- capability ordering

\- dependency relationships

\- information exchange

\- state management

\- error propagation

\- composition patterns



---



# Composition Principles



Capabilities shall be:



\- **Composable**: Capabilities can be combined into larger workflows.

\- **Independently Testable**: Each capability can be tested in isolation.

\- **Loosely Coupled**: Capabilities depend on contracts, not implementations.

\- **Information-Explicit**: Data flow between capabilities is explicit.

\- **Failure-Aware**: Each capability knows how to report and propagate failures.



No capability shall assume the responsibilities of another.



---



# Composition Patterns



## Sequential Composition



Capabilities execute in a deterministic order.



Example:

Health Check → Diagnostics → Planning → Execution → Verification





The result of one becomes the input for the next.



---



## Conditional Composition



Execution path depends on capability results.



Example:

Verification

│

├── Success → Complete

└── Failure → Rollback





Different paths may execute different capabilities.



---



## Parallel Composition



Capabilities execute independently.



Results are aggregated for final assessment.



Example:

Parallel Health Checks

│

├── Runtime Health

├── Workspace Health

└── Provider Health

│

▼

Aggregated Health Report





---



## Iterative Composition



Capabilities execute in a loop.



Loop condition determines continuation.



Example:

Verify → Health Check → (Failed) → Retry → Health Check → ...





---



# Information Flow



Information between capabilities should be:



\- **Explicit**: Passing data through defined inputs/outputs.

\- **Typed**: Data has a defined schema.

\- **Validated**: Data is checked against the contract.

\- **Traceable**: Data origin and transformations are logged.



Implicit global state or shared memory should be avoided.



---



# Error Handling



Composition should define:



\- **Failure Boundaries**: Where failures can occur and be isolated.

\- **Recovery Strategies**: Retry, fallback, or abort.

\- **Rollback Behavior**: How to undo partial work.

\- **Escalation Paths**: When to involve human operators.



---



# Relationship with Workflow Engine



\- **Capability Composition** defines the *what* (structure, order, conditions).

\- **Workflow Engine** executes the *how* (state, transitions, logging).



---



# Relationship with Capability Contract



Contracts define capability inputs/outputs.



Composition uses contracts to validate data flow between steps.



---



# Future Evolution



Future versions may support:



\- Dynamic composition based on runtime conditions.

\- Adaptive composition based on historical success rates.

\- Visual composition tools.



---



# Summary



Capability Composition defines how individual capabilities coordinate to achieve operational objectives. By specifying relationships, information flow, and error handling, the composition model enables reliable workflow execution while preserving capability independence.

