# SAM Audit Specification

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
- EXECUTION_SPECIFICATION.md

---

# Scope

Audit is specified within this document as the conceptual representation of operational records and their traceability.

Audit defines how an operational event is represented conceptually so that it can be traced. It does not determine decisions and does not run operations.

Audit is not Approval. Audit does not decide.

Audit is not Execution. Audit does not perform.

This document does not redefine Citizen, Capability, Registry, Contract, Approval, Execution, Runtime, or Governance.

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
- Execution Specification
- Citizen Specification
- Capability Specification

Audit derives its authority from the Constitution and the Canonical Architecture. It extends none of them. It adds no identity, capability, contract, approval, or execution semantics.

---

# Purpose

The purpose of Audit is to make operational activity traceable.

Audit answers the question: what happened?

Audit records, in a conceptual form, the operational events that have occurred, so that they can be followed back to their origin. It does not decide, execute, or govern.

---

# Audit Identity

Every Audit Record possesses a distinct identity.

Audit Identity consists of:

- Audit ID: a global identifier that distinguishes this Audit Record from all others.
- Execution Reference: a reference to the Execution that produced the activity.
- Approval Reference: a reference to the Approval that authorized the activity.
- Contract Reference: a reference to the Contract governing the activity.
- Capability Reference: a reference to the Capability involved.

Audit Identity does not prescribe an implementation format. It describes the conceptual elements required to identify an Audit Record.

---

# Audit Record

An Audit Record is the conceptual representation of an operational event.

An Audit Record SHALL be able to reference:

- Identity: the Audit Identity of the record.
- Context: the context in which the activity occurred.
- References: the Execution, Approval, Contract, and Capability references.
- Outcome: the conceptual outcome of the activity.
- Timestamp: a conceptual notion of when the activity occurred, not a specific time format.

These elements are conceptual. This specification does not mandate a JSON structure or any other representation.

---

# Audit Lifecycle

Every Audit Record follows a lifecycle. The current state SHALL be observable.

Lifecycle states:

- Recorded
- Verified
- Archived

Legal transitions:

- Recorded -> Verified
- Recorded -> Archived
- Verified -> Archived

Archived is terminal. An archived Audit Record SHALL NOT transition to any other state.

---

# Traceability Rules

Every Audit Record SHALL be traceable back to its originating objects.

Each Audit Record SHALL reference:

- The Execution that produced the activity.
- The Approval that authorized it.
- The Contract that governed it.
- The Capability that was involved.

Traceability is achieved through references. This Specification does not redefine Execution, Approval, Contract, or Capability. It only requires that a record can be followed back to them.

---

# Failure Behaviour

Audit SHALL reflect a defined failure rather than an inconsistent record.

Defined failures:

- Missing Reference: a required reference is absent.
- Broken Traceability: a record cannot be followed back to its origin.
- Incomplete Record: the record lacks required elements.
- Invalid Record: the record is malformed or invalid.
- Duplicate Record: an identical record already exists.
- Archived Reference: a referenced object has been archived and can no longer be verified.

All failures are observable and defined by this specification.

---

# Interoperability

Two independently implemented Audit Engines SHALL be able to produce mutually comprehensible Audit Records if both satisfy this specification.

To interoperate, an Audit Engine SHALL:

- Recognize Audit Identity (ID, Execution, Approval, Contract, Capability references).
- Produce records that reference the defined elements.
- Follow the defined lifecycle transitions.
- Return the defined failures.

Interoperability is achievable from this specification alone, without shared implementation.

---

# Boundaries

Audit records and provides traceability only.

Audit is NOT:

- Registry. Audit does not discover or resolve Capabilities.
- Contract. Audit does not define the structure of communication.
- Approval. Audit does not decide whether an operation is permitted.
- Execution. Audit does not run an operation.
- Governance. Audit does not create or change governance.

Audit only records and provides traceability.

---

# Relationship with Execution

The relationship between Audit and Execution is explicit:

- Execution produces operational activity.
- Audit represents that activity.
- Audit does not affect the outcome of Execution.

Audit observes and records. It has no influence over what Execution produces.

---

# Relationship with Approval

The relationship between Audit and Approval is explicit:

- Approval is a decision.
- Audit only references that decision.
- Audit does not change or evaluate the decision.

Audit treats an Approval as a fact to be referenced, not as something to judge.

---

# Final Statement

Audit records operational activity and makes it traceable.

It does not decide, execute, define, or govern. It observes and records.

An Audit Engine that satisfies this specification is interchangeable with any other Audit Engine that also satisfies it.
