# Capability Registry



Version: 1.0



Status: Draft



Capability Type: Runtime Architecture



Execution Mode: System



Risk Level: Low



Owner: OpenClaw Module



Related Documents



Capabilities



\- capability-runtime.md

\- capability-contract.md



Sprint 2



\- health-checks.md

\- provider-testing.md



Sprint 4



\- operational-reports.md



Framework



\- docs/models/DECISION\_MODEL.md



---



# Purpose



Maintain a central registry of all available capabilities.



The Capability Registry provides capability discovery, metadata management, dependency resolution, and version control.



---



# Registry Information



Each registered capability includes the following metadata:



| Field | Description | Example |

| :--- | :--- | :--- |

| `id` | Unique capability identifier. | `health-check` |

| `version` | Semantic version. | `1.2.0` |

| `owner` | Module or team responsible. | `OpenClaw Module` |

| `description` | Human-readable summary. | `Perform health checks on OpenClaw components` |

| `type` | Capability category. | `Observation`, `Execution`, `Reasoning` |

| `dependencies` | Capabilities required. | `diagnostic-automation` |

| `permissions` | Required permissions (read/write). | `read:workspace` |

| `risk\_level` | Operational risk classification. | `Low`, `Medium`, `High` |

| `contract` | Reference to contract definition. | `contracts/health-check.json` |

| `status` | Lifecycle status of the capability. | `active`, `deprecated`, `disabled` |



---



# Discovery Methods



Capabilities may be discovered by:



\- **ID**: Direct lookup.

\- **Type**: Filter by capability type.

\- **Domain**: Filter by operational domain (e.g., `provider`, `runtime`).

\- **Dependency**: Find capabilities that depend on this capability.



---



# Registry Lifecycle



Capabilities registered in the registry go through a lifecycle:

REGISTERED → ACTIVE → DEPRECATED → DISABLED → REMOVED





\- **REGISTERED**: Capability metadata is recorded.

\- **ACTIVE**: Capability is available for execution.

\- **DEPRECATED**: Capability is scheduled for replacement. New workflows should avoid it.

\- **DISABLED**: Capability is temporarily unavailable.

\- **REMOVED**: Capability is permanently removed from the registry.



---



# Dependency Resolution



When a workflow requests a capability, the Registry:



1\.  Resolves the capability ID to a specific version (latest, or pinned).

2\.  Checks that all dependencies are available.

3\.  Validates that dependencies are active and compatible.



---



# Version Management



Registry supports:



\- **Semantic Versioning**: MAJOR.MINOR.PATCH.

\- **Version Pinning**: Workflows may pin to a specific version.

\- **Compatibility Matrix**: Declares compatible versions between dependent capabilities.



---



# Security \& Permissions



Capabilities may require specific permissions to execute:



\- `read:configuration`

\- `write:workspace`

\- `read:runtime`

\- `execute:provider`

\- `modify:system`



The Registry enforces that only capabilities with the appropriate permissions are invoked by workflows.



---



# Relationship with Runtime



The Runtime queries the Registry to:



\- Load capability metadata.

\- Validate capability versions.

\- Resolve dependencies.



---



# Relationship with Audit



All registry changes (registration, deprecation, version updates) are audited.



---



# Future Evolution



Future versions may support:



\- Remote Registries for multi-node deployments.

\- Automatic discovery of capabilities via plugins.

\- Runtime capability update without restarting the system.



---



# Summary



The Capability Registry acts as the central catalog for all SAM capabilities, providing discovery, metadata, dependency resolution, and version management to ensure consistent and secure capability execution.





