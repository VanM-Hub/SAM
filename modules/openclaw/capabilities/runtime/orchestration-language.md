# Orchestration Language

Version: 1.0

Status: Draft

Capability Type: Runtime Infrastructure

Execution Mode: Declarative Workflow Definition

Risk Level: None

Owner: OpenClaw Runtime

Knowledge Type: Implementation

Evidence Level: Designed

Confidence: High

---

# Purpose

Define the declarative language used to describe executable workflows within the SAM Framework.

The Orchestration Language provides a platform-independent representation of workflow behavior.

It describes *what* should happen.

It does not describe *how* the runtime performs execution.

---

# Authority

Primary Reference

- docs/specifications/SAM_FRAMEWORK_v1.0_SPECIFICATION.md

Supporting References

- docs/core/CONSTITUTION.md
- docs/core/EXECUTION_MODEL.md
- docs/GLOSSARY.md

Related Runtime Components

- workflow-engine.md
- capability-runtime.md
- capability-contract.md
- capability-composition.md
- capability-registry.md

---

# Language Philosophy

Workflow definitions shall be:

- declarative
- deterministic
- human-readable
- machine-executable
- versionable
- auditable

The language shall describe operational intent rather than implementation details.

---

# Design Principles

The language shall:

- separate definition from execution
- reference capabilities by ID
- remain implementation independent
- support composition
- preserve auditability
- preserve governance

---

# Core Concepts

A workflow consists of:

- Metadata
- Inputs
- Variables
- Stages
- Conditions
- Parallel Blocks
- Error Policies
- Outputs

---

# Workflow Metadata

Every workflow shall define:

- Workflow ID
- Version
- Name
- Description
- Owner
- Required Runtime Version
- Specification Version

---

# Capability Invocation

Capabilities are referenced by Capability ID.

Example

```
run:

- capability: openclaw.observation.health-checks

- capability: openclaw.reasoning.diagnostic-engine

- capability: openclaw.execution.execution-planning
```

The language never references implementation classes.

---

# Sequential Execution

Example

```
workflow:

- health-check

- diagnostics

- reasoning

- planning

- approval

- execution

- verification
```

Stages execute in order.

---

# Conditional Execution

Example

```
if:

condition: provider_unhealthy

then:

- provider-testing

else:

- verification
```

Conditions evaluate workflow state rather than implementation state.

---

# Parallel Execution

Example

```
parallel:

- workspace-validation

- configuration-validation

- provider-testing
```

All branches execute independently.

Synchronization occurs automatically before subsequent stages.

---

# Nested Workflow

Example

```
workflow:

- diagnose

- execute:

workflow: recovery-workflow

- verify
```

Nested workflows inherit execution context.

---

# Variables

Workflow variables store execution state.

Examples:

```
variables:

provider: NVIDIA

risk: Medium

workspace: default
```

Variables remain scoped to workflow execution.

---

# Evidence References

Evidence is exchanged through references.

Example

```
inputs:

evidence:

- runtime-report

- provider-status

- configuration-report
```

Capabilities never modify existing evidence.

---

# Error Policy

Each workflow defines error handling behavior.

Example

```
on_failure:

policy: rollback

retry: 3

escalate: operator
```

Policies are interpreted by the Workflow Engine.

---

# Approval Gate

Approval requirements are declarative.

Example

```
approval:

required: true

risk: High
```

Approval execution belongs to the Approval capability.

---

# Rollback

Rollback workflows are defined explicitly.

Example

```
rollback:

workflow: restore-last-backup
```

Rollback remains a workflow rather than embedded runtime behavior.

---

# Verification

Post-execution verification may be declared.

Example

```
verify:

workflow:

- health-check

- provider-testing

- configuration-validation
```

Verification becomes part of the workflow definition.

---

# Audit

Workflow definitions declare required audit events.

Example

```
audit:

capture:

- execution

- evidence

- reasoning

- verification
```

Audit recording remains the responsibility of the runtime.

---

# Workflow Example

```
workflow:

- capability: openclaw.observation.health-checks

- capability: openclaw.diagnostics.runtime

- capability: openclaw.reasoning.engine

- capability: openclaw.execution.planning

- capability: openclaw.governance.approval

- capability: openclaw.execution.apply

- capability: openclaw.execution.verify

- capability: openclaw.learning.knowledge-update
```

This represents the complete operational lifecycle.

---

# Validation

Workflow definitions are validated before execution.

Validation includes:

- syntax
- capability existence
- dependency resolution
- contract compatibility
- permission requirements
- cycle detection
- version compatibility

Invalid workflows shall not execute.

---

# Versioning

Workflow definitions shall declare:

- Language Version
- Specification Version
- Runtime Compatibility

Backward compatibility shall be maintained whenever possible.

---

# Relationship to Workflow Engine

The Orchestration Language defines workflows.

The Workflow Engine executes them.

The language never performs execution.

---

# Relationship to Capability Registry

Capability references are resolved through the Capability Registry.

Workflow definitions never reference implementation locations.

---

# Relationship to Capability Contracts

Workflow definitions interact with capabilities exclusively through their contracts.

Contract compatibility determines workflow validity.

---

# Operational Boundaries

The Orchestration Language shall never:

- execute workflows
- perform reasoning
- bypass governance
- implement runtime behavior
- modify evidence

Its responsibility is declarative workflow definition only.

---

# Future Evolution

Future versions may support:

dsl/

expressions.md

event-triggers.md

dynamic-workflows.md

imports.md

reusable-templates.md

visual-editor.md

policy-library.md

---

# Summary

The Orchestration Language provides the declarative representation of operational workflows within the SAM Framework.

By separating workflow definition from execution, the language enables portable, auditable, versioned, and implementation-independent operational automation across the entire capability ecosystem.