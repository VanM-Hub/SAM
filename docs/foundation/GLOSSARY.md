# SAM Glossary

Version: 1.0.0
Status: Foundational
Authority: Constitutional Vocabulary

> The Glossary provides authoritative vocabulary for Project SAM.
> It does not define governance rules, constitutional principles, or architectural decisions.
> Those remain authoritative only in their respective documents.

---

# Purpose

This glossary defines the official meaning of the core concepts used throughout Project SAM.

These definitions are normative.

Architectural decisions,
Runtime implementations,
Specifications,
Documentation,
and future extensions should use these definitions consistently.

If industry terminology conflicts with this glossary,
the glossary takes precedence within Project SAM.

---

# Agent

## Definition

An autonomous Citizen responsible for performing one or more Missions through declared Capabilities.

## Industry Difference

An Agent is not an AI model.

An Agent is not an LLM.

An Agent is not a chatbot.

Within SAM, an Agent is a constitutional participant.

## Relationships

Mission
↓

Workflow
↓

Agent
↓

Runtime
↓

Provider

---

# Approval

## Definition

The constitutional process that authorizes an action before execution.

Approval determines permission.

Execution performs action.

These are different responsibilities.

---

# Artifact

## Definition

An immutable representation of the outcome of a Mission.

Artifacts may represent:

documents,

code,

reports,

plans,

execution results,

analysis,

or any governed output.

As established by the Constitution, Artifacts are governed outputs, never a source of governance themselves.

---

# Audit

## Definition

The immutable record explaining why,
how,
when,
and under which authority something occurred.

Audit transforms actions into evidence.

---

# Bridge

## Definition

A read-only translation layer that exposes Runtime information without exposing Runtime implementation.

Bridges never own business logic.

---

# Capability

## Definition

The formal description of a governed ability that a constitutional participant can perform.

Capability is implementation independent.

Capability is the universal language of SAM.

Authoritative Source: CONSTITUTION

---

# Certification

## Definition

The constitutional process verifying that a Citizen satisfies required governance principles.

As established by the Constitution and Governance, Certification evaluates constitutional compliance rather than usefulness.

---

# Citizen

## Definition

Any constitutional participant that enjoys the rights and obligations of Project SAM.

A Citizen publishes Capabilities, obeys Contracts, participates in governance, and remains auditable.

Citizens include:

Runtime

Agent

Provider

Connector

Model

Skill

Tool

Workflow

Mission

and future constitutional entities.

Citizen is the highest architectural abstraction.

---

# Connector

## Definition

A Citizen responsible for connecting SAM to external systems through governed interfaces.

As established by the Constitution, a Connector implements communication; it does not itself hold governance.

---

# Contract

## Definition

An immutable agreement defining communication between Citizens.

Contracts define expectations.

Not implementation.

---

# Constitution

## Definition

The non-negotiable principles that define the identity of Project SAM and set what must never change.

The Constitution derives its legitimacy from the Mission and exists to preserve and fulfill it. It is the highest authority.

Authoritative Source: CONSTITUTION

---

# Descriptor

## Definition

The immutable identity document describing a Citizen.

A Descriptor typically includes:

Identity

Version

Metadata

Capabilities

Certification

Compatibility

---

# Desktop

## Definition

A user-facing interface to SAM.

As established by the Constitution, a Desktop consumes governance rather than being part of it.

Other interfaces such as CLI,
REST,
or IDE integrations have equivalent architectural status.

---

# Discovery

## Definition

The governed process of locating Citizens through Capabilities.

Discovery never performs execution.

---

# DTO

## Definition

An immutable data transfer object.

DTOs carry information.

They never contain business behavior.

---

# Execution

## Definition

The constitutional act of applying an approved decision to the outside world.

Execution changes reality.

Approval authorizes it.

---

# Governance

## Definition

The system by which authority is allocated, exercised, and audited within Project SAM.

Governance determines who may do what and how authority is granted and revoked, in service of the Vision. It does not define identity.

Authoritative Source: GOVERNANCE

---

# Health

## Definition

The current operational condition of a Citizen.

Health reflects operational readiness.

Not business success.

---

# Identity

## Definition

The enduring character of Project SAM that remains stable while technology changes.

Identity is expressed through the Mission, Constitution, and Vision, and outlives any implementation.

Authoritative Source: MISSION + CONSTITUTION + VISION

---

# Intelligence

## Definition

The capability to produce reasoning,
analysis,
planning,
or inference.

Intelligence is governed by SAM.

It does not govern SAM.

---

# Knowledge

## Definition

Structured information available to Citizens for governed decision making.

Knowledge is descriptive.

Not procedural.

---

# Lifecycle

## Definition

The governed sequence of states through which a Citizen progresses.

Lifecycle provides predictable evolution.

---

# Memory

## Definition

Governed contextual information representing historical state.

Memory preserves context.

Not governance.

---

# Mission

## Definition

The highest-level declaration of desired business outcome.

A Mission defines:

objective,

constraints,

approval requirements,

expected artifacts,

success criteria,

and governance expectations.

Mission defines purpose.

Not implementation.

---

# Model

## Definition

A computational intelligence implementation capable of providing reasoning or generation.

As established by the Constitution, Models implement intelligence rather than define governance.

---

# Monitoring

## Definition

Continuous observation of Citizen state.

Monitoring observes.

It does not control.

---

# Philosophy

## Definition

The reasoning that guides thinking when the Constitution does not give an explicit answer.

Philosophy explains how Project SAM approaches principled decisions; it is not the source of identity.

Authoritative Source: CONSTITUTION

---

# Policy

## Definition

The formal rules governing permitted behavior.

Policies determine what is allowed.

Approval determines whether permission is granted.

---

# Presentation

## Definition

The user-facing layer through which humans interact with SAM.

Presentation visualizes, configures, approves, and observes; it holds no business logic and communicates through Runtime Service.

Authoritative Source: CONSTITUTION

---

# Provider

## Definition

A Citizen implementing access to external computational capabilities.

Examples include:

LLM providers,

database providers,

filesystem providers,

container providers,

future providers.

As established by the Constitution, Providers implement capabilities rather than exercise governance.

---

# Registry

## Definition

The authoritative catalog of Citizens and Capabilities.

Registry enables discovery.

Registry never performs business logic.

---

# Runtime

## Definition

A constitutional unit responsible for governing one bounded capability domain.

Runtime is not merely a software module.

Runtime is the primary governance unit.

---

# Skill

## Definition

A reusable governed capability executable by an Agent.

Skills describe how work is performed.

Agents decide when to use them.

---

# Tool

## Definition

An executable external capability exposed to SAM through Providers or Connectors.

Tools perform work.

Governance controls access.

---

# Trust

## Definition

The measurable confidence that a governed decision complies with constitutional principles.

Trust is the primary output of SAM.

---

# Workflow

## Definition

The governed sequence of activities required to complete a Mission.

Workflow defines process.

Not responsibility.

---

# Relationships

Mission

↓

Workflow

↓

Agent

↓

Skill

↓

Runtime

↓

Capability

↓

Provider

↓

Execution

↓

Artifact

↓

Audit

Governance surrounds every layer.

---

# Constitutional Rule

If a future architectural concept cannot be defined using the vocabulary of this glossary,

the glossary should evolve before the architecture does.