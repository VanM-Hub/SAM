# SAM Constitution

Version: 1.0.0

Status: Foundational

Authority: Highest

Scope: Entire Project SAM

Canonical: true

Supersedes: docs/history/architecture/SAM_CONSTITUTION.md (Historical Design Reference); docs/core/CONSTITUTION.md (Draft, Superseded, deleted in C1-C)

Mission Source: MISSION.md

Depends On: MISSION.md (legitimacy)

Owner: Project SAM

---

# Preamble

Project SAM exists to provide a trustworthy governance layer for intelligent systems.

Artificial Intelligence will continue to evolve.

Models will change.

Providers will change.

Programming languages will change.

Deployment topology will change.

Technology will change.

The Constitution exists so that the identity of SAM does not.

This document defines the principles that every architecture decision,

runtime, provider, agent, workflow, and future subsystem must obey.

Everything else may evolve.

The Constitution should not.

---

# Constitutional Foundation

Mission is the reason SAM exists.

The Constitution does not create the Mission.

The Constitution derives its legitimacy from the Mission.

The Constitution exists to preserve and fulfill the Mission.

Mission is the highest authority.

Everything else exists to preserve and fulfill the Mission.

If implementation conflicts with the Constitution, the Constitution governs.

If the Constitution must be amended, an amendment must never betray the Mission.

---

# Article I — Governance over Intelligence

## Principle

Governance always has higher priority than intelligence.

## Meaning

SAM does not exist to create intelligence.

SAM exists to govern how intelligence is used.

Intelligence without governance cannot be trusted.

## Architectural Impact

Every intelligent action must be governed by explicit rules,

contracts, approval, and audit.

## Supported Decisions

- Approval Runtime exists.

- Audit Runtime exists.

- Policy Runtime exists.

- Intelligence never bypasses governance.

## Violations

- LLM making autonomous decisions without policy.

- Agent executing tasks without approval.

- Hidden execution paths.

---

# Article II — Trust is the Primary Output

## Principle

The primary product of SAM is trust.

## Meaning

Execution is not success.

Correct governance is success.

Every result produced by SAM must be explainable,

repeatable,

auditable,

and attributable.

## Architectural Impact

Every Runtime must produce traceable outputs.

## Supported Decisions

- Certification

- Audit

- Monitoring

- Approval

- Immutable DTO

## Violations

- Hidden state

- Untraceable decisions

- Unknown execution path

---

# Article III — Capability is the Universal Language

## Principle

Capabilities are the common language of SAM.

## Meaning

Citizens communicate through capabilities,

never through implementation details.

## Architectural Impact

Discovery, Registry, Selection,

Routing,

Planning,

Scheduling,

and Coordination operate on capabilities.

## Supported Decisions

Provider abstraction.

Agent abstraction.

Runtime abstraction.

## Violations

Runtime depending directly on implementation.

---

# Article IV — Registry over Direct Dependency

## Principle

Citizens discover,

never assume.

## Meaning

A Citizen should never know another Citizen directly.

Communication happens through Registry and Discovery.

## Architectural Impact

Loose coupling.

Replaceable implementations.

Distributed future.

## Violations

Workflow Runtime importing Memory Runtime directly.

---

# Article V — Approval before Execution

## Principle

Nothing executes before explicit approval.

## Meaning

Execution is always intentional.

## Architectural Impact

Execution Runtime must always be approval-gated.

## Violations

Automatic execution after reasoning.

---

# Article VI — Immutable Contracts

## Principle

Contracts never mutate.

## Meaning

Communication depends on immutable structures.

## Architectural Impact

DTOs are immutable.

Descriptors are immutable.

Contracts are immutable.

## Violations

Mutable DTO.

Runtime changing received contract.

---

# Article VII — Deterministic by Default

## Principle

Same input.

Same contracts.

Same policies.

Same output.

## Meaning

Determinism has higher priority than convenience.

## Architectural Impact

Runtime behavior must be reproducible.

## Violations

Hidden randomness.

Implicit context.

Time-dependent logic without explicit contract.

---

# Article VIII — Provider Agnostic

## Principle

SAM belongs to no provider.

## Meaning

Providers are replaceable.

Governance is permanent.

## Architectural Impact

OpenAI,

Anthropic,

Gemini,

DeepSeek,

OpenClaw,

Ollama,

future providers

are implementations only.

## Violations

Business logic depending on provider-specific APIs.

---

# Article IX — Runtime Independence

## Principle

Every Runtime is independently evolvable.

## Meaning

A Runtime may be replaced,

distributed,

or upgraded without changing other Runtimes.

## Architectural Impact

Runtime communication occurs through contracts.

## Violations

Circular Runtime dependency.

---

# Article X — Citizen Equality

## Principle

Every Citizen follows the same constitutional rules.

## Meaning

Runtime,

Agent,

Provider,

Connector,

Model,

Skill,

Tool,

Workflow,

Mission,

and future Citizens

share the same constitutional rights and obligations.

## Architectural Impact

Shared descriptor.

Shared capability.

Shared lifecycle.

Shared certification.

## Violations

Special-case architecture.

---

# Article XI — Audit Everything

## Principle

Every meaningful action must be attributable.

## Meaning

Every decision should answer:

Who?

Why?

When?

Under which policy?

Using which capability?

## Architectural Impact

Audit identity.

Artifact traceability.

Certification.

## Violations

Anonymous execution.

---

# Article XII — Separation of Responsibility

## Principle

Every Citizen has one primary responsibility.

## Meaning

Mission defines purpose.

Workflow defines process.

Policy defines rules.

Approval authorizes.

Execution executes.

Audit records.

No Citizen performs another Citizen's responsibility.

## Violations

Workflow performing approval.

Execution modifying policy.

---

# Article XIII — Evolution without Breaking Foundation

## Principle

Architecture evolves.

Constitution remains.

## Meaning

New Runtime.

New Agent.

New Provider.

New Model.

New Deployment.

None should require changing constitutional principles.

## Architectural Impact

Backward-compatible evolution.

Stable contracts.

## Violations

Architecture redesign requiring constitutional changes.

---

# Article XIV — Explainability before Optimization

## Principle

Optimization must never reduce explainability.

## Meaning

A faster system that cannot explain itself is less valuable.

## Architectural Impact

Decision justification.

Rule trace.

Evidence chain.

## Violations

Opaque optimization.

---

# Article XV — Constitution over Implementation

## Principle

Implementation serves the Constitution.

Never the opposite.

## Meaning

When implementation conflicts with constitutional principles,

implementation must change.

The Constitution must not.

---

# Article XVI — Presentation Principle

## Principle

Human interfaces are Presentation Layers.

Presentation Layers shall never contain business logic.

Presentation Layers shall never become runtime coordinators.

Presentation Layers communicate only through Runtime Service.

All runtime orchestration belongs to Runtime Service.

## Meaning

A Presentation Layer exists only to visualize, configure, approve, and observe.

It does not own intelligence.

It does not own execution.

It does not own orchestration.

It composes the user interface from information provided by Runtime Service and the runtime family.

## Architectural Impact

Presentation Layer communicates exclusively through Runtime Service.

Presentation Layer holds no business logic.

Presentation Layer performs no approval decision.

Presentation Layer performs no provider or connector dispatch.

All execution remains in Execution Runtime, behind Approval.

## Violations

A Presentation Layer becoming a runtime.

A Presentation Layer owning an engine or pipeline.

A Presentation Layer storing business state.

A Presentation Layer bypassing Runtime Service.

---

# Constitutional Hierarchy

Mission

â†“

Constitution

â†“

Philosophy

â†“

Governance

â†“

Architecture

â†“

Specification

â†“

Roadmap

â†“

Implementation

---

# Constitutional Test

Every architectural proposal should answer:

Does this change continue to serve the Mission?

If the answer is "No",

the proposal should be reconsidered.

If the answer is "Yes",

then evaluate:

Does this improve governance?

Does this preserve determinism?

Does this increase trust?

Does this preserve loose coupling?

Does this preserve immutable contracts?

Does this improve auditability?

Does this remain provider agnostic?

Does this preserve citizen equality?

If any answer is "No",

the proposal should be reconsidered.

---

# Final Statement

SAM is not defined by its programming language.

SAM is not defined by its AI model.

SAM is not defined by its provider.

SAM is not defined by its deployment topology.

SAM is defined by this Constitution.

Everything else may evolve.

The Constitution remains.

