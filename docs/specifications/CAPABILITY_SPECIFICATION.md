# SAM Capability Specification

Version: 1.0

Status: Foundational

Authority: Derived from the Constitution

Depends On:

- CONSTITUTION.md
- GLOSSARY.md
- CITIZEN_SPECIFICATION.md

---

# Scope

Capability is specified within this document as the universal language of Project SAM.

The meanings of Mission, Constitution, Governance, Citizen, and the Model Layer remain authoritative in their respective documents.

This document explains the Capability domain and does not redefine those concepts.

---

# Purpose

This document defines the specification of Capabilities, derived from the Constitution.

Capabilities are the universal language used by Citizens to describe what they can provide.

Citizens communicate through Capabilities.

Never through implementation.

---

# Definition

A Capability is a formal, immutable declaration of an ability that a Citizen offers to the ecosystem.

Capabilities describe behavior.

They never describe implementation.

---

# Why Capability Exists

Implementations change.

Providers change.

Models change.

Languages change.

Deployment topology changes.

Capabilities remain stable.

Therefore Capability becomes the architectural contract shared by every Citizen.

---

# Constitutional Principles

Every Capability shall be:

- immutable
- versioned
- uniquely identifiable
- discoverable
- certifiable
- auditable
- implementation independent
- backward compatible whenever practical

---

# Capability Identity

Each Capability possesses a globally unique identifier.

Recommended format:

```
<domain>.<category>.<capability>
```

Examples:

```
memory.lookup
memory.snapshot
knowledge.search

workflow.build

mission.validate

policy.evaluate

provider.chat

provider.embedding

connector.github

execution.execute

audit.record
```

Identity never contains implementation names.

Correct:

provider.chat

Incorrect:

openai_chat

---

# Capability Descriptor

Every Capability publishes an immutable descriptor.

Descriptor contains:

Capability ID

Name

Description

Owner Citizen

Version

Inputs

Outputs

Constraints

Compatibility

Certification

Lifecycle

Metadata

---

# Capability Versioning

Capabilities evolve independently from implementations.

Recommended format:

Major.Minor.Patch

Examples:

memory.lookup@1.0.0

memory.lookup@1.2.0

Major changes indicate contract incompatibility.

Minor changes extend compatibility.

Patch changes fix implementation without modifying contract.

---

# Capability Contracts

Every Capability exposes exactly one public contract, as established by the Constitution and the Glossary.

This specification does not redefine the Contract; it states how a Capability relates to a Contract.

Contract never exposes internal implementation.

---

# Capability Categories

Capabilities generally belong to one of the following domains.

Governance

Mission

Workflow

Policy

Approval

Runtime

Memory

Knowledge

Cognitive

Execution

Audit

Artifact

Provider

Connector

Desktop

Monitoring

Certification

Future domains may be introduced.

---

# Capability Lifecycle

Recommended lifecycle:

Declared

Registered

Certified

Available

Deprecated

Retired

Deprecated capabilities remain discoverable.

Retired capabilities are removed from active discovery.

---

# Discovery

Capabilities are discovered through Registry.

Never through implementation.

Discovery process:

Capability Request

↓

Registry

↓

Matching

↓

Compatibility Check

↓

Capability Descriptor

↓

Contract

↓

Citizen

---

# Registry

Registry stores capability metadata.

Registry never executes capabilities.

Registry enables:

lookup

filter

version resolution

compatibility checks

dependency analysis

---

# Capability Dependencies

Capabilities may depend on other Capabilities.

They never depend directly on implementation.

Example:

workflow.build

↓

requires

↓

memory.lookup

↓

requires

↓

knowledge.search

Each dependency remains explicit.

---

# Compatibility

Compatibility is evaluated at Capability level.

Not implementation level.

Compatible Capabilities should continue working even when implementation changes.

---

# Certification

Capabilities should be independently certifiable.

Certification verifies:

descriptor integrity

contract validity

determinism

immutability

discoverability

governance compliance

compatibility

Certification never measures performance.

---

# Capability Health

Capability Health reflects operational readiness.

Suggested values:

Healthy

Degraded

Unavailable

Unknown

Health belongs to runtime operation.

Not business success.

---

# Capability Discovery Rules

Citizens shall never assume another Citizen exists.

Citizens request Capabilities.

Registry resolves providers.

This eliminates direct architectural coupling.

---

# Capability Replacement

A Capability may receive a new implementation provided:

Contract remains compatible.

Certification succeeds.

Descriptor remains valid.

Identity remains unchanged.

Replacing implementation should not affect consumers.

---

# Capability Evolution

Capabilities evolve through extension.

Not replacement.

Preferred order:

Patch

↓

Minor

↓

Major

Breaking compatibility requires explicit architectural review.

---

# Runtime Relationship

Runtime owns Capabilities.

Runtime is not the Capability.

Capability survives Runtime implementation replacement.

---

# Citizen Relationship

Every Citizen publishes Capabilities.

Every interaction occurs through Capabilities.

Capability is therefore the universal language of Citizens.

---

# Provider Relationship

Providers implement Capabilities.

Providers never redefine Capabilities.

---

# Model Relationship

Models satisfy Capability requests.

Models do not own Capability definitions.

---

# Future Distributed Architecture

In future distributed deployments:

Runtime Registry

↓

Capability Registry

↓

Remote Discovery

↓

Capability Resolution

↓

Remote Runtime

Architecture should remain unchanged.

Only deployment changes.

---

# Constitutional Rule

Implementation may evolve.

Capability identity should remain stable.

Capability is part of the constitutional architecture.

Implementation is not.

---

# Capability Test

A new architectural concept becomes a Capability only if:

It represents an ability.

It can be described independently.

It can be versioned.

It can be certified.

It can be discovered.

It can expose a contract.

It can evolve independently.

Otherwise,

it is probably implementation rather than Capability.

---

# Final Statement

Capability is the universal language of Project SAM.

Citizens cooperate through Capabilities.

Runtimes govern Capabilities.

Providers implement Capabilities.

The Constitution protects Capabilities.

Everything else is implementation.