# Runtime Flow

Version: 1.0

Status: Draft

Owner: OpenClaw Module

Related Documents

Knowledge

- ../knowledge/cli.md
- ../knowledge/runtime.md
- ../knowledge/workspace.md
- ../knowledge/configuration.md
- ../knowledge/providers.md
- ../knowledge/models.md
- ../knowledge/agents.md

Architecture

- components.md
- data-flow.md

Framework

- docs/core/EXECUTION_MODEL.md
- docs/core/THINKING_PROTOCOL.md

---

# Purpose

This document describes the execution flow of an OpenClaw operation.

Unlike the Knowledge documents, which define architectural concepts, this document explains how those concepts interact during execution.

The Runtime Flow represents the coordination sequence performed by the Runtime.

---

# Architectural Principles

The Runtime coordinates execution.

Other components provide capabilities.

No component should bypass the Runtime during normal operation.

Execution should remain observable, deterministic where practical, and traceable.

---

# High-Level Flow

```
User
 │
 ▼
CLI
 │
 ▼
Runtime
 │
 ├──────────────► Workspace
 │
 ├──────────────► Configuration
 │
 ├──────────────► Provider
 │                     │
 │                     ▼
 │                  Model
 │                     │
 ▼                     │
Agent ◄────────────────┘
 │
 ▼
Result
```

The Runtime is the central coordinator of the execution flow.

---

# Execution Stages

## Stage 1 — Request Reception

The process begins when a user submits a request through the CLI.

Responsibilities:

- parse user input,
- validate syntax,
- determine requested operation.

If the request cannot be interpreted, execution terminates before entering the Runtime.

---

## Stage 2 — Runtime Initialization

The Runtime begins execution by preparing its operational context.

Typical activities include:

- initializing internal state,
- selecting the active Workspace,
- preparing execution resources.

The Runtime does not yet perform AI operations.

---

## Stage 3 — Workspace Resolution

The Runtime resolves the active Workspace.

Workspace resolution provides:

- operational context,
- persistent state,
- configuration scope.

If no valid Workspace exists, execution cannot continue.

---

## Stage 4 — Configuration Resolution

The Runtime loads the effective Configuration.

Configuration determines:

- Provider selection,
- Model selection,
- execution options,
- operational behavior.

Configuration expresses intent.

The Runtime implements that intent.

---

## Stage 5 — Provider Selection

The Runtime selects the appropriate Provider according to the active Configuration.

Provider responsibilities include:

- authentication,
- capability exposure,
- request forwarding.

The Runtime does not communicate directly with Models.

---

## Stage 6 — Model Invocation

The selected Provider invokes the requested Model.

The Model performs inference.

The Runtime remains responsible for execution coordination throughout this stage.

---

## Stage 7 — Agent Processing

The Runtime delivers Model responses to the active Agent.

The Agent:

- interprets results,
- performs reasoning,
- prepares operational output.

The Agent may request additional Runtime operations if required.

---

## Stage 8 — Response Generation

The Runtime prepares the final response.

The CLI presents the result to the user.

Execution is complete.

---

# Error Propagation

Errors should propagate upward through the architecture.

Example:

```
Model
 ▲
Provider
 ▲
Runtime
 ▲
CLI
 ▲
User
```

Lower layers should not attempt to present user-facing messages directly.

Presentation belongs to the CLI.

---

# Observability

Each execution stage should be observable.

Operational telemetry may include:

- execution stage,
- timestamps,
- provider selection,
- workspace identifier,
- configuration profile,
- execution outcome.

Observability supports diagnostics without altering Runtime behavior.

---

# Failure Boundaries

Different failures belong to different architectural layers.

Examples:

CLI

- invalid command

Workspace

- missing context

Configuration

- invalid settings

Provider

- unavailable service

Model

- inference failure

Agent

- reasoning failure

Correct classification simplifies diagnostics.

---

# Relationship with Data Flow

Runtime Flow describes execution order.

Data Flow describes information movement.

The two documents are complementary and should be read together.

---

# Summary

Runtime Flow defines how OpenClaw coordinates execution from user request to final response.

The Runtime acts as the orchestration layer, ensuring that Workspace, Configuration, Providers, Models, and Agents collaborate through clearly defined architectural boundaries.