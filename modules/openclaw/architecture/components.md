# Components

Version: 1.0

Status: Draft

Owner: OpenClaw Module

Related Documents

Knowledge

- ../knowledge/environment.md
- ../knowledge/workspace.md
- ../knowledge/configuration.md
- ../knowledge/runtime.md
- ../knowledge/providers.md
- ../knowledge/models.md
- ../knowledge/agents.md
- ../knowledge/cli.md

Architecture

- runtime-flow.md
- data-flow.md

Framework

- docs/ARCHITECTURE.md
- docs/DEPENDENCY_RULES.md

---

# Purpose

This document explains how the major OpenClaw components cooperate to perform work.

Definitions of the individual components are intentionally omitted and instead referenced from the Knowledge layer.

---

# Architectural Philosophy

OpenClaw follows a layered architecture.

Each component has a single primary responsibility.

Interaction occurs only through defined boundaries.

Components should not bypass intermediate layers.

---

# Primary Components

## User Interface Layer

Current implementation:

- CLI

Future implementations may include:

- GUI
- REST API
- MCP Server
- IDE Integration

These interfaces communicate only with the Runtime.

They should never communicate directly with Providers.

---

## Runtime Layer

The Runtime coordinates execution.

Responsibilities include:

- command orchestration
- configuration loading
- workspace initialization
- provider selection
- model invocation
- lifecycle management

The Runtime is the central coordinator rather than the owner of all business logic.

---

## Workspace Layer

Workspace provides execution context.

The Runtime always executes inside one Workspace.

Workspace contains:

- operational state
- configuration
- identities
- module artifacts

---

## Configuration Layer

Configuration determines Runtime behavior.

Configuration never performs execution.

Runtime interprets Configuration.

---

## Provider Layer

Providers expose AI capabilities.

Providers hide implementation-specific communication.

Runtime communicates with Providers through stable abstractions.

---

## Model Layer

Models perform inference.

Models never communicate directly with the CLI.

They are accessed exclusively through Providers.

---

## Agent Layer

Agents perform reasoning.

Agents consume Runtime services.

Agents should remain independent from Provider implementation details.

---

# Dependency Direction

Dependency flows downward.

```
CLI
 ↓
Runtime
 ↓
Workspace
 ↓
Configuration
 ↓
Provider
 ↓
Model
```

Lower layers never depend on higher layers.

---

# Interaction Rules

Components communicate only through their defined interfaces.

Examples:

CLI

↓

Runtime

✓

Runtime

↓

Provider

✓

Provider

↓

CLI

✗

Workspace

↓

Runtime

✗

Model

↓

Configuration

✗

---

# Architectural Benefits

This organization provides:

- modularity
- replaceability
- observability
- testability
- maintainability

without introducing cyclic dependencies.

---

# Relationship with Runtime Flow

This document explains the structural view.

Runtime execution is described in:

runtime-flow.md

---

# Summary

The OpenClaw architecture consists of independent components connected through well-defined responsibilities.

Each component performs one primary function while interacting through stable architectural boundaries.