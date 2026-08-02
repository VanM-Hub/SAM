# SAM Approval Specification

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
- CONTRACT_SPECIFICATION.md

---

# Scope

The Approval process is specified within this document as the authorization decision that precedes the execution of a Capability.

Approval determines whether an operation may proceed. It does not perform Execution.

Approval defines authorization. It is not discovery (Registry), not communication (Contract), and not execution.

This document does not redefine Citizen, Capability, Registry, Contract, Runtime, or Governance.

---

# Authority

## Authoritative Dependencies

- Mission
- Constitution
- Governance
- Canonical Architecture

## Operational Dependencies

- Registry Specification
- Contract Specification
- Citizen Specification
- Capability Specification

The Approval process derives its authority from the Constitution, Governance, and the Canonical Architecture. It extends none of them. It adds no identity, capability, or contract semantics.

---

# Purpose

The purpose of Approval is to produce a binding authorization decision for an operation before that operation may be executed.

Approval answers the question: may this operation proceed?

Approval is the gate between intent and execution. It does not run the operation; it decides whether the operation is permitted.

---

# Approval Identity

Every Approval possesses a distinct identity.

Approval Identity consists of:

- Approval ID: a global identifier that distinguishes this Approval from all others.
- Decision Context: the context in which the authorization decision is made.
- Contract Reference: a reference to the Contract governing the operation.
- Capability Reference: a reference to the Capability being requested.

Approval Identity does not prescribe an implementation format. It describes the conceptual elements required to identify an Approval.

---

# Approval Request

An Approval Request is the conceptual input to the Approval process.

Required Input:

- Decision Context
- Referenced Contract
- Referenced Capability

Optional Input:

- Referenced Citizen (the Citizen seeking the operation)

The Approval Request refers to a Contract and a Capability as defined by their respective Specifications. It does not redefine them.

---

# Approval Decision

The Approval process produces a decision.

Decision states:

- Approved: the operation may proceed.
- Rejected: the operation may not proceed.
- Expired: the Approval was valid but is no longer valid.
- Cancelled: the Approval was withdrawn before a decision took effect.
- Superseded: a newer Approval replaced this Approval.

The decision is the outcome of the Approval process. This specification does not prescribe how the decision is computed.

---

# Approval Lifecycle

Every Approval follows a lifecycle. The current state SHALL be observable.

Lifecycle states:

- Created
- Pending
- Approved
- Rejected
- Expired
- Archived

Legal transitions:

- Created -> Pending
- Created -> Rejected
- Pending -> Approved
- Pending -> Rejected
- Pending -> Expired
- Pending -> Cancelled
- Approved -> Expired
- Approved -> Archived
- Rejected -> Archived
- Expired -> Archived
- Cancelled -> Archived

Archived is terminal. An archived Approval SHALL NOT transition to any other state.

---

# Failure Behaviour

The Approval process SHALL return a defined failure rather than an unintended decision.

Defined failures:

- Missing Contract: the referenced Contract is absent.
- Unknown Capability: the referenced Capability is not recognized.
- Registry Resolution Failed: the Capability could not be resolved.
- Invalid Request: the Approval Request is malformed.
- Expired Request: the Approval Request is no longer valid.
- Approval Conflict: an Approval State contradicts the requested operation.

All failures are observable and defined by this specification.

---

# Interoperability

Two independently implemented Approval Engines SHALL be able to produce compatible behavior if both satisfy this specification.

To interoperate, an Approval Engine SHALL:

- Recognize Approval Identity (ID, Decision Context, Contract Reference, Capability Reference).
- Accept the defined Approval Request.
- Produce the defined decision states.
- Follow the defined lifecycle transitions.
- Return the defined failures.

Interoperability is achievable from this specification alone, without shared implementation.

---

# Boundaries

The Approval process produces an authorization decision only.

The Approval process is NOT:

- Registry. Approval does not discover or resolve Capabilities.
- Contract. Approval does not define the structure of communication.
- Runtime. Approval does not own or manage a Runtime.
- Execution. Approval does not run an operation.
- Audit. Approval does not record audit events.

Approval references these domains where needed, but does not take their authority.

---

# Relationship with Execution

The relationship between Approval and Execution is explicit:

- Approval completes at the decision.
- Execution begins after Approval completes.
- Approval does not run an operation.

An operation may be executed only after its Approval has produced a decision. A Rejected, Expired, or Cancelled Approval does not permit execution.

---

# Final Statement

The Approval process is the authorization gate between intent and execution.

It produces a binding decision. It does not run the operation, discover the Capability, define the Contract, or record the audit.

An Approval Engine that satisfies this specification is interchangeable with any other Approval Engine that also satisfies it.
