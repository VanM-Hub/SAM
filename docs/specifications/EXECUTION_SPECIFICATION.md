# SAM Execution Specification

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
- APPROVAL_SPECIFICATION.md

---

# Scope

Execution is specified within this document as the running of an operation that has received an Approval decision.

Execution defines the behavior of carrying out an already-approved operation. It does not determine whether the operation is permitted.

Execution is not Approval. Execution does not decide authorization.

Execution is not Registry. Execution does not discover or resolve.

Execution is not Contract. Execution does not define communication.

This document does not redefine Citizen, Capability, Registry, Contract, Approval, Runtime, or Governance.

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
- Approval Specification
- Citizen Specification
- Capability Specification

Execution derives its authority from the Constitution and the Canonical Architecture. It extends none of them. It adds no identity, capability, contract, or approval semantics.

---

# Purpose

The purpose of Execution is to perform an operation that has been approved.

Execution answers the question: the operation is permitted; now it is carried out.

Execution is the observable behavior between an Approval decision and a result. It does not decide, discover, or define; it performs.

---

# Execution Identity

Every Execution possesses a distinct identity.

Execution Identity consists of:

- Execution ID: a global identifier that distinguishes this Execution from all others.
- Approval Reference: a reference to the Approval that authorized this operation.
- Contract Reference: a reference to the Contract governing the operation.
- Capability Reference: a reference to the Capability being executed.

Execution Identity does not prescribe an implementation format. It describes the conceptual elements required to identify an Execution.

---

# Execution Request

An Execution Request is the conceptual input to Execution.

Required Input:

- Referenced Approval
- Referenced Contract
- Referenced Capability

Optional Input:

- Additional input required by the referenced Contract or Capability.

The Execution Request refers to an Approval, a Contract, and a Capability as defined by their respective Specifications. It does not redefine them.

---

# Execution Result

Execution produces a result.

Result states:

- Completed: the operation finished successfully.
- Failed: the operation finished unsuccessfully.
- Cancelled: the operation was stopped before completion.
- Timed Out: the operation exceeded its allowed duration.

The result is the outcome of executing the operation. This specification does not prescribe how the result is computed.

---

# Execution Lifecycle

Every Execution follows a lifecycle. The current state SHALL be observable.

Lifecycle states:

- Created
- Queued
- Running
- Completed
- Failed
- Cancelled
- Archived

Legal transitions:

- Created -> Queued
- Created -> Cancelled
- Queued -> Running
- Queued -> Cancelled
- Running -> Completed
- Running -> Failed
- Running -> Cancelled
- Running -> Timed Out
- Completed -> Archived
- Failed -> Archived
- Cancelled -> Archived

Archived is terminal. An archived Execution SHALL NOT transition to any other state.

---

# Failure Behaviour

Execution SHALL return a defined failure rather than an unintended outcome.

Defined failures:

- Missing Approval: no Approval is referenced.
- Invalid Approval: the referenced Approval is not valid for this operation.
- Missing Contract: the referenced Contract is absent.
- Capability Unavailable: the Capability cannot be performed.
- Execution Timeout: the operation exceeded its allowed duration.
- Execution Failure: the operation did not complete successfully.

All failures are observable and defined by this specification.

---

# Idempotency

Idempotency defines when an Execution may be repeated.

Behavioral rules:

- An operation may be repeated when repeating it produces the same outcome as performing it once.
- An operation SHALL NOT be repeated when repetition could produce a different or unintended outcome.
- A Completed Execution SHALL NOT be re-executed as a new Execution unless the operation is idempotent.

Idempotency is a property of the operation under its Contract. This specification does not dictate a technical mechanism for achieving idempotency.

---

# Interoperability

Two independently implemented Execution Engines SHALL produce compatible behavior if both satisfy this specification.

To interoperate, an Execution Engine SHALL:

- Recognize Execution Identity (ID, Approval Reference, Contract Reference, Capability Reference).
- Accept the defined Execution Request.
- Produce the defined result states.
- Follow the defined lifecycle transitions.
- Return the defined failures.

Interoperability is achievable from this specification alone, without shared implementation.

---

# Boundaries

Execution runs an authorized operation only.

Execution is NOT:

- Registry. Execution does not discover or resolve Capabilities.
- Contract. Execution does not define the structure of communication.
- Approval. Execution does not decide whether the operation is permitted.
- Audit. Execution does not record audit events.
- Governance. Execution does not create or change governance.

Execution only performs an operation that has been authorized.

---

# Relationship with Audit

The relationship between Execution and Audit is explicit:

- Execution produces operational information that Audit may record.
- Execution does not perform Audit.

Execution generates the observable information about an operation. Audit consumes that information. Execution has no responsibility to record, retain, or report it.

---

# Final Statement

Execution carries out an approved operation.

It does not decide, discover, define, or record. It performs, and produces an observable outcome.

An Execution Engine that satisfies this specification is interchangeable with any other Execution Engine that also satisfies it.
