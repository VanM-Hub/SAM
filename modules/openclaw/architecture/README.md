# OpenClaw Architecture

Version: 1.0

Status: Draft

Owner: SAM Framework

Related Documents

- ../README.md
- ../MODULE_SPECIFICATION.md
- ../knowledge/README.md
- ../playbooks/README.md
- ../diagnostics/README.md

Framework References

- docs/architecture/SAM_ARCHITECTURE.md
- docs/architecture/LAYERS.md
- docs/architecture/MODULE_INTERFACE.md
- docs/core/CONSTITUTION.md

---

# Purpose

This document describes the architectural view of OpenClaw as understood by the SAM Framework.

It defines the major operational domains, their relationships, and the architectural boundaries used by this module.

This document intentionally avoids implementation details.

Those belong in Knowledge documents.

---

# Architectural Philosophy

SAM does not own OpenClaw.

SAM observes, documents, and manages OpenClaw.

Therefore this architecture describes:

- operational concepts
- responsibilities
- interactions
- information flow

rather than source code structure.

---

# High-Level Architecture

```
                 SAM Framework
                       â”‚
                       â–¼
              OpenClaw Module
                       â”‚
 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
 â”‚                     â”‚                     â”‚
 â–¼                     â–¼                     â–¼
Knowledge          Playbooks          Diagnostics
 â”‚                     â”‚                     â”‚
 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜
                 â–¼                     â–¼
          OpenClaw Runtime        Operational Data
```

The Framework governs the Module.

The Module interprets the Runtime.

The Runtime never depends on the Module.

---

# Core Architectural Domains

The OpenClaw Module is divided into four primary domains.

## Architecture

Describes structure and boundaries.

Questions answered:

- How is OpenClaw organized?
- Which concepts exist?
- How do components relate?

---

## Knowledge

Contains validated operational knowledge.

Examples:

- configuration concepts
- provider behavior
- workspace organization
- agent lifecycle
- model capabilities

Knowledge must always be evidence-based.

---

## Playbooks

Contains executable operational procedures.

Examples:

- verify installation
- restart services
- recover configuration
- validate providers

Playbooks define operational actions.

---

## Diagnostics

Contains investigative procedures.

Examples:

- provider failures
- workspace corruption
- configuration issues
- API failures

Diagnostics reduce uncertainty.

---

# Architectural Layers

Layer 1

Framework

Responsible for governance.

Layer 2

Module

Responsible for interpretation.

Layer 3

Runtime

Responsible for execution.

Layer 4

External Systems

Examples:

- AI Providers
- Filesystem
- Operating System
- Network

Each layer has distinct responsibilities.

---

# Conceptual Components

The Framework recognizes several conceptual components within OpenClaw.

These components are logical concepts rather than implementation details.

Examples include:

- Workspace
- Agent
- Identity
- Provider
- Model
- Configuration
- Runtime
- CLI
- Logs
- Tasks

Detailed descriptions belong in Knowledge documents.

---

# Information Flow

Operational information generally flows as follows:

External Event

â†“

Runtime

â†“

Logs / State

â†“

Diagnostics

â†“

Knowledge

â†“

Playbooks

â†“

Operations

â†“

New Evidence

â†“

Knowledge

This closed feedback loop supports continuous improvement.

---

# Dependency Rules

The architecture follows the Dependency Rules defined by the Framework.

Allowed

Framework

â†“

Module

â†“

Runtime

â†“

External Systems

Not Allowed

Runtime

â†“

Framework

Module

â†“

Framework

Cross-module dependencies without approved interfaces.

---

# Architectural Stability

This document should remain stable over time.

Changes are expected primarily in:

- Knowledge
- Playbooks
- Diagnostics

Architectural changes should require an ADR.

---

# Future Expansion

Future architecture documents may include:

components.md

interfaces.md

runtime.md

provider-model.md

workspace-model.md

agent-model.md

configuration-model.md

data-flow.md

sequence-diagrams.md

These documents extend this architecture without replacing it.

---

# Success Criteria

The architecture succeeds when it:

- clearly defines boundaries
- avoids implementation coupling
- supports future evolution
- remains understandable
- enables modular growth

---

# Summary

This document defines how the SAM Framework conceptualizes OpenClaw.

Rather than documenting implementation details, it establishes stable architectural concepts that guide Knowledge, Diagnostics, Playbooks, and future module evolution.

Its purpose is to preserve architectural consistency while allowing operational documentation to evolve independently.