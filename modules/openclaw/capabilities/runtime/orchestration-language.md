```markdown

# Orchestration Language



Version: 1.0



Status: Draft



Capability Type: Runtime Architecture



Execution Mode: System



Risk Level: Low



Owner: OpenClaw Module



Related Documents



Capabilities



\- workflow-engine.md

\- capability-composition.md

\- capability-contract.md

\- capability-registry.md



Sprint 3



\- approval-gate.md

\- rollback.md



Framework



\- docs/core/EXECUTION\_MODEL.md

\- docs/models/DECISION\_MODEL.md



---



# Purpose



Define a Domain-Specific Language (DSL) for describing capability workflows in a human-readable and machine-executable format.



The Orchestration Language enables declarative workflow definitions. Workflows are defined as structured YAML (or JSON).



---



# Language Principles



\- **Declarative**: Specify *what* to execute, not *how*.

\- **Readable**: Operators can understand the flow without reading code.

\- **Validatable**: Syntax and structure can be validated before execution.

\- **Extensible**: Can evolve to support new patterns.



---



# Language Structure



## Top-Level Fields



| Field | Description |

| :--- | :--- |

| `name` | Workflow name. |

| `description` | Workflow purpose. |

| `version` | Workflow version. |

| `capabilities` | List of capabilities required by this workflow. |

| `parameters` | Global parameters for the workflow. |

| `steps` | Ordered list of execution steps. |

| `on\_error` | Error handling strategy for the entire workflow. |



---



## Step Definition



Each step includes:



| Field | Description |

| :--- | :--- |

| `id` | Unique step identifier. |

| `capability` | Capability ID or reference. |

| `inputs` | Map of input parameters (can reference previous steps). |

| `on\_success` | Next step ID to execute on success. |

| `on\_failure` | Next step ID to execute on failure. |

| `on\_timeout` | Action on timeout. |

| `retry` | Retry configuration (max attempts, backoff). |



---



## Data Reference Syntax



Step outputs can be referenced using a variable syntax:

{{ step\_id.output\_field }}



text



Example:



```yaml

inputs:

&#x20; diagnosis: {{ diagnose.result }}

&#x20; plan: {{ plan.output }}

Example Workflow

yaml

name: "Provider Recovery Workflow"

description: "Automatically diagnose and recover from Provider failures"

version: "1.0.0"



parameters:

&#x20; provider\_name:

&#x20;   type: string

&#x20;   required: true

&#x20; workspace\_path:

&#x20;   type: string

&#x20;   required: true



capabilities:

&#x20; - health-checks

&#x20; - provider-testing

&#x20; - diagnostic-reasoning-engine

&#x20; - self-healing-executor



steps:

&#x20; - id: "diagnose"

&#x20;   capability: "diagnostic-reasoning-engine"

&#x20;   inputs:

&#x20;     symptom: "Provider unresponsive"

&#x20;     workspace: "{{ workspace\_path }}"

&#x20;   on\_success: "plan"

&#x20;   on\_failure: "escalate"



&#x20; - id: "plan"

&#x20;   capability: "execution-planning"

&#x20;   inputs:

&#x20;     diagnosis: "{{ diagnose.output }}"

&#x20;     provider: "{{ provider\_name }}"

&#x20;   on\_success: "approve"



&#x20; - id: "approve"

&#x20;   capability: "approval-gate"

&#x20;   inputs:

&#x20;     plan: "{{ plan.output }}"

&#x20;     risk\_level: "medium"

&#x20;   on\_success: "execute"

&#x20;   on\_failure: "abort"



&#x20; - id: "execute"

&#x20;   capability: "self-healing-executor"

&#x20;   inputs:

&#x20;     plan: "{{ approve.plan }}"

&#x20;   on\_success: "verify"

&#x20;   on\_failure: "rollback"

&#x20;   retry:

&#x20;     max\_attempts: 2

&#x20;     backoff: "exponential"



&#x20; - id: "verify"

&#x20;   capability: "continuous-verification"

&#x20;   inputs:

&#x20;     execution: "{{ execute.output }}"

&#x20;     provider: "{{ provider\_name }}"

&#x20;   on\_success: "complete"

&#x20;   on\_failure: "rollback"



&#x20; - id: "rollback"

&#x20;   capability: "rollback"

&#x20;   inputs:

&#x20;     execution\_id: "{{ execute.id }}"

&#x20;   on\_success: "escalate"



&#x20; - id: "escalate"

&#x20;   capability: "escalation"

&#x20;   inputs:

&#x20;     message: "Provider recovery failed. Manual intervention required."

&#x20;   on\_success: "abort"



on\_error:

&#x20; action: "abort"

&#x20; message: "Workflow aborted due to unrecoverable error."

Workflow Validation

Before execution, the Workflow Engine validates:



Syntax validity (e.g., YAML parsable).



Step references are valid.



Capability IDs exist in the Registry.



Data references ({{ }}) resolve correctly.



No circular dependencies.



Relationship with Workflow Engine

Orchestration Language defines the workflow.



Workflow Engine executes the workflow.



Future Evolution

Future versions may support:



Conditional statements (if/else).



Parallel steps (parallel).



Loops (for/while).



Workflow composition (call another workflow as a step).



Declarative rollback definition.



Summary

The Orchestration Language provides a declarative, readable, and validatable format for defining capability workflows. By using a structured DSL, operators and systems can define complex operational procedures while maintaining consistency, auditability, and ease of maintenance.

