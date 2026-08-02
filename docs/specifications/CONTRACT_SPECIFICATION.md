# SAM Contract Specification

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
- REGISTRY_SPECIFICATION.md

---

# Scope

The Contract is specified within this document as the structure of communication between Citizens through Capabilities.

A Contract defines the shape of an interaction. It does not define who runs it, who approves it, who discovers the Capability, or who executes it.

This document defines only the structure of communication. It does not redefine Citizen, Capability, Registry, Governance, or Runtime.

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
- Registry Specification

The Contract derives its authority from the Constitution, the Canonical Architecture, and the Registry Specification. It extends none of them. It adds no governance, identity, or capability rules.

---

# Purpose

The purpose of the Contract is to be the interoperable agreement that allows two independent Citizens to communicate through a Capability without sharing implementation.

A Contract makes the boundary between Citizens explicit. It is the guarantee that the sender and the receiver agree on the shape of the interaction.

The Contract exists so that interoperability does not depend on either party's internal implementation.

---

# Contract Identity

Every Contract possesses a distinct identity.

Contract Identity consists of:

- Contract ID: a global identifier that distinguishes this Contract from all others.
- Version: the version of this Contract.
- Capability Reference: a reference to the Capability to which this Contract belongs.

Contract Identity does not prescribe an implementation format. It describes the conceptual elements required to identify and version a Contract.

---

# Contract Structure

Every Contract describes the shape of an interaction. The structure is expressed in conceptual elements, not in any specific encoding.

A Contract SHALL describe:

- Input: the information the interaction expects to receive.
- Output: the information the interaction returns.
- Metadata: descriptive information about the interaction.
- Constraints: the conditions the interaction requires or obeys.
- Compatibility: how this Contract aligns with neighboring versions.
- Error: the failure outcomes the interaction may produce.

These elements are conceptual. This specification does not mandate JSON, protobuf, or any other representation.

---

# Compatibility Rules

Compatibility is a behavioral property of a Contract relative to another version of the same Contract.

Rules:

- Backward compatible: a consumer of an older version works with a newer version.
- Forward compatible: a consumer of a newer version works with an older version.
- Breaking change: a change that breaks backward or forward compatibility.
- Compatible change: a change that preserves compatibility.
- Deprecated contract: a Contract version that remains defined but is no longer preferred for new interactions.

A Contract SHALL declare its compatibility relative to its predecessor. A Consumer SHALL NOT assume compatibility that the Contract does not declare.

---

# Version Negotiation

Version negotiation is how two Citizens select a Contract version to use.

Negotiation follows behavioral rules. It does not prescribe an algorithm.

Rules:

- Both Citizens SHALL agree on a single version before interaction proceeds.
- A version that is compatible with both participants SHALL be chosen.
- If no mutually compatible version exists, negotiation SHALL fail with a defined failure, and no interaction SHALL occur.
- Preference SHALL be given to a non-deprecated version when available.

---

# Failure Behaviour

A Contract interaction SHALL return a defined failure rather than an unintended outcome.

Defined failures:

- Unknown Contract: the Contract is not recognized.
- Unsupported Version: the requested version is not supported.
- Invalid Contract: the Contract is malformed or invalid.
- Malformed Payload: the interaction content does not match the Contract shape.
- Missing Field: required content is absent.
- Incompatible Contract: no mutually compatible version exists.

All failures are observable and defined by this specification.

---

# Interoperability

Two independently implemented Citizens SHALL be able to communicate if both satisfy this specification.

To interoperate, both parties SHALL:

- Agree on Contract Identity (ID, Version, Capability Reference).
- Agree on the conceptual structure (Input, Output, Metadata, Constraints, Compatibility, Error).
- Apply the compatibility and negotiation rules.
- Recognize the defined failures.

Interoperability is achievable from this specification alone, without shared implementation.

---

# Boundaries

The Contract defines the structure of communication only.

The Contract is NOT:

- Registry. The Contract does not discover or resolve Capabilities.
- Approval. The Contract does not decide whether an interaction is approved.
- Runtime. The Contract does not run or manage execution.
- Execution. The Contract does not execute work.
- Audit. The Contract does not record audit events.

The Contract references these domains where needed, but does not take their authority.

---

# Evolution

A Contract evolves through versioning, not through runtime behavior.

Evolution states:

- Compatible: the Contract version preserves compatibility with its predecessor.
- Deprecated: the Contract version remains defined but is no longer preferred.
- Replaced: a newer Compatible version supersedes this Contract.
- Retired: the Contract version is no longer valid for new interactions.

Evolution describes the Contract's standing over time. It does not create a Runtime lifecycle.

---

# Final Statement

The Contract is the interoperable agreement that lets independent Citizens communicate through Capabilities without sharing implementation.

It defines only the structure of communication. It does not run, approve, discover, or execute.

A Contract that satisfies this specification is interchangeable with any other Contract that also satisfies it.
