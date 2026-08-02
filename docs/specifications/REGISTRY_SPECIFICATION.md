# SAM Registry Specification

Version: 1.0

Status: Foundational

Authority: Derived from the Constitution

Depends On:

- CONSTITUTION.md
- GLOSSARY.md
- GOVERNANCE.md
- SAM_ARCHITECTURE.md
- CITIZEN_SPECIFICATION.md
- CAPABILITY_SPECIFICATION.md

---

# Scope

The Registry is specified within this document exclusively as the discovery and resolution mechanism of Project SAM.

The Registry does not define identity.

The Registry does not own the meaning of Citizen, Capability, Runtime, Governance, or Contract. Those meanings remain authoritative in their respective documents.

This document states how a Registry discovers and resolves what other documents already define.

---

# Authority

## Authoritative Dependencies

- Mission
- Constitution
- Governance
- Glossary
- Canonical Architecture

## Operational Dependencies

- Citizen Specification
- Capability Specification

The Registry derives its authority from the Constitution and the Canonical Architecture. It does not extend either. It does not add rules to governance, identity, or capability semantics.

---

# Registry Purpose

The purpose of the Registry is to make Capabilities discoverable and resolvable by Citizens.

The Registry answers the question: given a Capability request, which Capability does the requester receive?

This is a behavioral purpose, not an implementation. The Registry does not define how lookups are stored, indexed, or executed. It defines what behavior must be observable.

---

# Registry Object

The Registry holds references to objects already defined elsewhere. It does not redefine them.

The Registry may register:

- Citizen
- Capability
- Descriptor
- Version
- Contract Reference

Each registered object remains defined by its owning specification. The Registry references a Citizen as defined by the Citizen Specification, a Capability as defined by the Capability Specification, and a Contract as defined by the Constitution and the Glossary.

The Registry never stores implementation. It stores the minimum information required to discover and resolve.

---

# Registration Lifecycle

Every registered object follows a lifecycle. The Registry SHALL expose the current lifecycle state of each registered object.

Lifecycle states:

- Register
- Update
- Deprecate
- Suspend
- Remove

Legal transitions:

- Register -> Update
- Register -> Suspend
- Register -> Remove
- Update -> Deprecate
- Update -> Suspend
- Update -> Remove
- Deprecate -> Suspend
- Suspend -> Register
- Suspend -> Update
- Remove is terminal. A removed object SHALL NOT transition to any other state.

A Deprecated object remains discoverable but SHALL NOT be selected as a resolution candidate unless no non-deprecated candidate matches.

A Suspended object SHALL NOT be discoverable for new requests but SHALL remain traceable.

---

# Discovery Protocol

Discovery is the operation by which a Citizen requests Capabilities from the Registry.

Input:

- Capability Request (a reference to a requested Capability, expressed through the Capability Specification)

Output:

- A Capability Descriptor (as defined by the Capability Specification)
- A Contract Reference

Failure:

- Not Found: no registered object matches the request.
- Version Mismatch: a matching object exists, but no registered version is compatible with the requested version.
- Error: the request cannot be processed (malformed, missing, or invalid request).

Discovery SHALL be idempotent. An identical request SHALL produce an identical result.

Discovery SHALL NOT have side effects on the registered objects.

---

# Resolution Rules

Resolution is the selection of a candidate from those that matched discovery.

Resolution follows behavioral rules. It does not prescribe a storage or matching algorithm.

Rules:

- A candidate SHALL match the requested Capability.
- A candidate SHALL have a compatible version.
- A non-deprecated candidate SHALL be preferred over a deprecated candidate.
- A suspended or removed object SHALL NOT be a candidate.
- When multiple candidates are equally valid, the Registry SHALL select exactly one deterministically so that two registries given the same input select the same result.

Resolution SHALL be deterministic given the same registry content and the same request.

---

# Version Compatibility

The Registry handles multiple versions of a Capability according to the Capability Specification versioning semantics.

- The Registry SHALL resolve to a version compatible with the request.
- If multiple compatible versions exist, the Registry SHALL apply the resolution rules to select one.
- Major version changes indicate contract incompatibility; the Registry SHALL NOT satisfy a request with a contract-incompatible version.
- If no compatible version exists, the Registry SHALL return Version Mismatch.

---

# Failure Behaviour

The Registry SHALL return a defined failure instead of silently returning an invalid result.

- Citizen missing: requests from an unregistered Citizen SHALL NOT resolve to a Capability. The Registry SHALL return an Error.
- Capability not found: the Registry SHALL return Not Found.
- Descriptor corrupted: a registered object whose Descriptor is invalid SHALL NOT be a resolution candidate. The Registry SHALL treat it as Failed and return an Error.
- Version not compatible: the Registry SHALL return Version Mismatch.

All failures are observable and defined by this specification.

---

# Interoperability Requirements

Two independently implemented Registries SHALL be interoperable if they satisfy this specification.

To be interoperable, a Registry SHALL:

- Expose the discovery protocol defined here.
- Return the failure types defined here.
- Apply deterministic resolution rules.
- Reference objects from the Citizen and Capability Specifications without redefinition.
- Produce the same resolution result given the same registry content and the same request.

Interoperability is achievable from this specification alone, without shared implementation.

---

# Boundaries

The Registry is discovery and resolution only.

The Registry is NOT:

- Approval. The Registry does not decide whether an operation is approved.
- Execution. The Registry does not run Capabilities.
- Runtime. The Registry does not own or execute Runtimes.
- Audit. The Registry does not record audit events.
- Contract. The Registry does not define Contracts.

The Registry references these domains where needed, but does not take their authority.

---

# Final Statement

The Registry makes discovery and resolution observable and deterministic.

It does not define identity, capability, or contract semantics. It only connects them.

A Registry that satisfies this specification is interchangeable with any other Registry that also satisfies it.
