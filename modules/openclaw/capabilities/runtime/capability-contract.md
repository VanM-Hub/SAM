# Capability Contract



Version: 1.0



Status: Draft



Capability Type: Runtime Architecture



Execution Mode: System



Risk Level: Low



Owner: OpenClaw Module



Related Documents



Capabilities



\- capability-runtime.md

\- capability-registry.md

\- capability-composition.md



Sprint 2



\- health-checks.md

\- configuration-validation.md



Framework



\- docs/models/TRUST\_MODEL.md

\- docs/models/DECISION\_MODEL.md



---



# Purpose



Define the formal contract for every capability.



The contract specifies how a capability interacts with the rest of the system.



Contracts ensure consistent, predictable, and verifiable capability execution.



---



# Contract Structure



A capability contract contains the following sections:



---



## 1. Metadata



| Field | Description |

| :--- | :--- |

| `capability\_id` | Unique identifier. |

| `version` | Semantic version of the contract. |

| `contract\_version` | Version of the contract schema (e.g., "1.0"). |



---



## 2. Inputs



Defines the required and optional inputs for the capability.
inputs:

name: workspace_path
type: string
required: true
description: "Path to the OpenClaw workspace"

name: timeout_seconds
type: integer
required: false
default: 30


---

## 3. Outputs

Defines the output structure.
outputs:

name: status
type: enum
values: ["success", "warning", "failure"]

name: data
type: object
description: "Detailed output data"

name: evidence
type: array
items: { type: object }
description: "Collected evidence"


---

## 4. Required Permissions

permissions:

read:configuration

read:workspace

read:runtime

read:filesystem

execute:provider (read-only)


---

## 5. Risk Classification

risk:
level: Low # Low, Medium, High, Critical
blast_radius: Minimal
rollback_support: true


---

## 6. Audit Events

Events to be recorded during execution:
audit_events:

initialized

executed

completed

failed

retry_attempted


---

## 7. Dependencies

Capabilities required by this capability:
dependencies:

capability_id: diagnostics-automation
version: ">=1.0.0"


---

## 8. Error Handling

Defines common error codes and recovery behavior:
error_handling:
timeout:
action: retry
max_retries: 3
backoff: exponential
invalid_input:
action: fail
message: "Input validation failed"


---

# Contract Validation

Before execution, the Runtime validates:

- Inputs match the contract schema.
- Permissions are satisfied.
- Dependencies are available.
- Risk level is permitted for the current context.

---

# Immutability

Contracts are immutable once published.

Changes to contracts require a new version.

---

# Relationship with Composition

Contracts enable safe composition:

- Composition checks that outputs of one step match inputs of the next.
- Contracts define data types that must be compatible.

---

# Relationship with Audit

Audit records each contract validation step.

---

# Future Evolution

Future versions may support:

- JSON Schema for input/output validation.
- Contract version negotiation.
- Dynamic contract discovery.

---

# Summary

The Capability Contract formalizes the interaction boundaries for every capability. By defining inputs, outputs, permissions, risk, and dependencies, contracts ensure predictable and verifiable capability execution across all workflows.

