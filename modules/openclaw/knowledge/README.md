# OpenClaw Knowledge

Version: 1.0

Status: Draft

Owner: SAM Framework

Related Documents

- ../README.md
- ../MODULE_SPECIFICATION.md
- ../architecture/README.md
- ../playbooks/README.md
- ../diagnostics/README.md

Framework References

- docs/models/TRUST_MODEL.md
- docs/models/MEMORY_MODEL.md
- docs/models/DECISION_MODEL.md
- docs/documentation/DOCUMENT_LIFECYCLE.md
- docs/glossary/GLOSSARY.md

---

# Purpose

This directory contains validated operational knowledge about OpenClaw.

Knowledge represents information that has been confirmed through evidence, operational experience, testing, or repeated observation.

Knowledge is intended to reduce uncertainty and improve future operational decisions.

---

# Philosophy

Knowledge is not a collection of notes.

Knowledge is not copied documentation.

Knowledge is not personal opinion.

Knowledge is organizational memory.

Every knowledge document should answer one question:

> "What have we learned that future operators should not have to rediscover?"

---

# Scope

Examples of knowledge maintained in this directory include:

- configuration behavior
- provider characteristics
- workspace organization
- agent lifecycle
- model capabilities
- operational limitations
- best practices
- verified troubleshooting facts
- configuration patterns
- performance observations

Knowledge should describe stable understanding rather than temporary observations.

---

# Relationship with Research

Research and Knowledge serve different purposes.

Research explores uncertainty.

Knowledge preserves validated understanding.

The expected flow is:

Research

↓

Evidence

↓

Validation

↓

Knowledge

Only validated findings should become Knowledge documents.

---

# Relationship with Incidents

Operational incidents often reveal new knowledge.

The expected learning cycle is:

Incident

↓

Root Cause Analysis

↓

Research (if necessary)

↓

Validation

↓

Knowledge

↓

Playbook Improvement

Every significant incident should be evaluated to determine whether it generates new operational knowledge.

---

# Relationship with Playbooks

Knowledge explains **why** something is true.

Playbooks explain **how** to perform an action.

For example:

Knowledge:

- Why provider authentication fails.
- Why workspace corruption occurs.

Playbook:

- Recover provider credentials.
- Repair workspace configuration.

Knowledge informs procedures but does not replace them.

---

# Relationship with Diagnostics

Diagnostics identify and investigate problems.

Knowledge explains recurring patterns identified through diagnostics.

Repeated diagnostic findings should eventually become validated Knowledge.

---

# Knowledge Categories

Future knowledge documents may include categories such as:

## Configuration

Examples:

- configuration structure
- configuration inheritance
- environment variables

## Providers

Examples:

- NVIDIA
- OpenAI
- Anthropic
- Local providers

## Models

Examples:

- supported model families
- capabilities
- limitations

## Agents

Examples:

- identity concepts
- lifecycle
- permissions
- workspace behavior

## Workspaces

Examples:

- directory structure
- configuration
- synchronization

## Runtime

Examples:

- startup behavior
- execution flow
- state management

## CLI

Examples:

- command behavior
- operational recommendations

Additional categories may be introduced through approved governance.

---

# Knowledge Quality

Knowledge documents should:

- be evidence-based
- reference sources
- identify assumptions
- remain implementation-independent where practical
- be understandable by future contributors

Knowledge should avoid speculation.

If uncertainty remains, the topic belongs in Research instead.

---

# Evidence Requirements

Every Knowledge document should reference:

- operational observations
- validated testing
- incident analysis
- official documentation
- trusted external sources

The Trust Model determines evidence quality.

Higher confidence evidence should always be preferred.

---

# Evolution

Knowledge evolves over time.

Possible changes include:

- clarification
- expansion
- correction
- deprecation
- replacement

Knowledge should never be deleted solely because it is outdated.

Historical context remains valuable.

Deprecated knowledge should clearly indicate:

- why it changed
- what replaced it
- when the change occurred

---

# Proposed Directory Structure

Future documents may include:

configuration.md

providers.md

models.md

agents.md

workspaces.md

runtime.md

cli.md

best-practices.md

limitations.md

performance.md

Each document should focus on one coherent topic.

---

# Success Criteria

The Knowledge directory succeeds when contributors can:

- quickly locate validated information,
- distinguish facts from assumptions,
- understand operational behavior,
- reuse prior experience,
- avoid repeating known mistakes.

---

# Summary

The Knowledge directory preserves validated operational understanding of OpenClaw.

Its purpose is to transform individual experience into shared organizational memory, enabling future contributors to make better decisions with less uncertainty.

Knowledge is not merely documentation—it is the accumulated operational intelligence of the OpenClaw Module.