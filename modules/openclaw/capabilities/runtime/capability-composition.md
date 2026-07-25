# Capability Composition

Version: 1.0

Status: Draft

Capability Type: Runtime Infrastructure

Execution Mode: Workflow Composition

Risk Level: None

Owner: OpenClaw Runtime

Knowledge Type: Implementation

Evidence Level: Designed

Confidence: High

---

# Purpose

Define how individual capabilities are composed into executable operational workflows.

Capability Composition provides the architectural model that enables small, independently testable capabilities to cooperate while preserving modularity, governance, traceability, and lifecycle isolation.

Composition defines relationships between capabilities.

Execution remains the responsibility of the Workflow Engine.

---

# Authority

Primary Reference

- docs/specifications/SAM_FRAMEWORK_v1.0_SPECIFICATION.md

Supporting References

- docs/core/CONSTITUTION.md
- docs/core/EXECUTION_MODEL.md
- docs/GLOSSARY.md

Related Runtime Components

- capability-runtime.md
- capability-registry.md
- capability-contract.md
- workflow-engine.md

---

# Composition Philosophy

A capability performs exactly one operational responsibility.

Complex operational behavior emerges through composition rather than increasingly complex capabilities.

Composition is preferred over capability specialization.

---

# Composition Model

Capabilities are connected through contracts.

```

Capability

↓

Output

↓

Workflow State

↓

Input

↓

Capability

```

Capabilities never communicate directly.

The Workflow Engine manages all data exchange.

---

# Composition Principles

Every composition shall satisfy the following principles:

- loose coupling
- explicit dependencies
- deterministic sequencing
- immutable evidence
- governed execution
- auditability
- replaceability

No composition shall violate these principles.

---

# Composition Units

The smallest executable unit is a single capability.

Higher-level operational behavior is created by combining capabilities into workflows.

Composition never modifies the internal behavior of a capability.

---

# Sequential Composition

Capabilities execute in a predefined order.

Example

```
Health Check

↓

Configuration Validation

↓

Provider Testing

↓

Verification Report
```

Each capability begins only after its predecessor completes successfully.

---

# Conditional Composition

Workflow execution may branch based on runtime conditions.

Example

```
Verification

↓

Healthy?

↓

Yes --------→ Complete

↓

No

↓

Diagnostic Reasoning
```

Branching decisions are evaluated by the Workflow Engine.

---

# Parallel Composition

Independent capabilities may execute simultaneously.

Example

```
Configuration Validation

Workspace Validation

Provider Testing

Filesystem Validation
```

Parallel execution requires:

- no shared mutable state
- independent contracts
- deterministic merge behavior

---

# Iterative Composition

Some workflows require repeated execution.

Example

```
Observe

↓

Verify

↓

Still Unhealthy?

↓

Repeat
```

Iteration shall define explicit termination conditions.

Infinite execution is prohibited.

---

# Nested Composition

A workflow may invoke another workflow.

Example

```
Auto Recovery

↓

Verification Workflow

↓

Health Check

↓

Provider Test

↓

Configuration Validation
```

Nested workflows remain independent execution contexts.

---

# Composite Workflow Example

```
Observe

↓

Health Check

↓

Diagnostics

↓

Reasoning

↓

Decision

↓

Execution Planning

↓

Approval

↓

Execution

↓

Verification

↓

Learning

↓

Archive
```

Each stage is an independent capability.

The composition defines the operational process.

---

# State Propagation

Workflow state propagates between capabilities.

Shared state may include:

- workflow identifier
- execution identifier
- evidence references
- execution status
- verification state
- audit context

Capabilities receive state through their contracts.

They shall not modify shared state directly.

---

# Evidence Flow

Evidence is passed between capabilities through references.

```
Evidence

↓

Evidence Store

↓

Evidence Reference

↓

Next Capability
```

Evidence shall remain immutable after publication.

---

# Failure Propagation

Failures propagate according to workflow policy.

Typical policies include:

Fail Fast

↓

Stop Workflow

Continue

↓

Record Failure

↓

Continue Remaining Steps

Retry

↓

Repeat Capability

Escalate

↓

Transfer Control

Policy selection belongs to the Workflow Engine.

---

# Dependency Rules

Composition shall only use registered capabilities.

Dependencies shall be:

- explicit
- validated
- version compatible
- permission compatible

Hidden runtime dependencies are prohibited.

---

# Composition Validation

Every composition should be validated before execution.

Validation includes:

- dependency graph
- contract compatibility
- permission requirements
- workflow integrity
- cycle detection
- unreachable stages

Invalid workflows shall not execute.

---

# Relationship to Capability Runtime

Capability Runtime executes one capability.

Capability Composition defines how multiple capabilities cooperate.

Execution and composition remain independent concerns.

---

# Relationship to Workflow Engine

Workflow Engine interprets compositions.

Composition defines structure.

Workflow Engine performs execution.

---

# Relationship to Orchestration Language

The Orchestration Language describes compositions declaratively.

Capability Composition defines the conceptual execution graph.

The DSL becomes one possible representation of that graph.

---

# Operational Boundaries

Capability Composition shall never:

- execute capabilities
- evaluate evidence
- perform reasoning
- bypass governance
- allocate runtime resources

Its responsibility is structural composition only.

---

# Future Evolution

Future versions may introduce:

composition/

dynamic-composition.md

policy-based-composition.md

distributed-composition.md

event-driven-composition.md

graph-execution.md

workflow-templates.md

---

# Summary

Capability Composition defines how independent capabilities are assembled into larger operational workflows.

By separating workflow structure from execution behavior, the framework preserves modularity, auditability, replaceability, and long-term architectural flexibility while enabling increasingly sophisticated operational automation.