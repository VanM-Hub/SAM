# Permissions

Version: 1.0

Status: Draft

Knowledge Type: Reference

Evidence Level: Verified

Confidence: High

Owner: OpenClaw Module

Related Documents

Knowledge

- environment.md
- filesystem.md
- workspace.md
- configuration-files.md
- runtime.md
- startup.md
- shutdown.md

Architecture

- ../architecture/workspace-model.md
- ../architecture/runtime-flow.md
- ../architecture/data-flow.md

Framework

- docs/documentation/KNOWLEDGE_STANDARD.md
- docs/models/RISK_MODEL.md
- docs/models/TRUST_MODEL.md

---

# Purpose

This document defines the conceptual permission model required by OpenClaw.

It explains what permissions represent, why they matter, and how they relate to operational reliability.

This document intentionally avoids operating-system-specific implementations.

---

# Definition

Permissions determine whether OpenClaw is authorized to perform an operation on a resource.

Permissions originate from the execution environment rather than from OpenClaw itself.

A component may be capable of performing an operation while lacking the permission to perform it.

---

# Objectives

The permission model exists to:

- protect operational resources,
- prevent unauthorized modification,
- support predictable execution,
- reduce unintended side effects,
- improve diagnostic accuracy.

Permissions are part of the operational environment.

They are not Runtime behavior.

---

# Permission Domains

Permissions apply to multiple architectural domains.

## Filesystem Permissions

Control access to:

- files,
- directories,
- Workspace resources,
- temporary storage.

Typical operations include:

- read,
- write,
- create,
- modify,
- delete.

---

## Configuration Permissions

Determine whether Configuration may be:

- viewed,
- modified,
- replaced,
- validated.

Configuration permissions should remain explicit.

---

## Runtime Permissions

Some Runtime operations may require elevated authorization.

Examples include:

- creating Workspaces,
- modifying operational state,
- managing execution artifacts.

Authorization requirements should be clearly documented.

---

## Provider Permissions

Providers may require authorization before exposing AI capabilities.

Examples include:

- API credentials,
- authentication tokens,
- service accounts.

Provider authorization is distinct from local filesystem permissions.

---

## Network Permissions

Communication with external Providers depends upon network authorization.

Network availability alone does not imply permission to communicate.

---

# Permission Principles

## Least Privilege

OpenClaw should operate with only the permissions required for the intended task.

Excessive permissions increase operational risk.

---

## Explicit Authorization

Operations requiring elevated permissions should be explicitly identifiable.

Hidden privilege escalation should be avoided.

---

## Separation of Responsibility

Permission management belongs to the operating environment.

OpenClaw consumes permissions but does not define them.

---

## Predictability

Permission failures should produce deterministic operational behavior.

Unexpected permission denial should never result in undefined execution.

---

# Permission Failures

Typical permission-related failures include:

- insufficient read access,
- insufficient write access,
- inaccessible Workspace,
- restricted Configuration,
- denied Provider authentication,
- blocked network communication.

These failures should be classified separately from Runtime failures.

---

# Relationship with Environment

Permissions are provided by the Environment.

Changes to the Environment may alter available permissions without changing OpenClaw itself.

---

# Relationship with Filesystem

Filesystem resources require appropriate authorization before access.

Filesystem accessibility should not be assumed.

---

# Relationship with Workspace

A Workspace is usable only if required permissions are available.

Workspace existence alone does not imply operational accessibility.

---

# Relationship with Runtime

The Runtime should detect permission failures and report them clearly.

The Runtime should not attempt to circumvent permission restrictions.

---

# Relationship with Risk Model

Permission failures often increase operational risk.

Examples include:

- inability to persist state,
- incomplete diagnostics,
- failed backups,
- interrupted execution.

Risk assessment should consider both the missing permission and its operational consequences.

---

# Operational Considerations

Operators should distinguish between:

- missing resources,
- unavailable resources,
- inaccessible resources.

Although these conditions may produce similar symptoms, they require different operational responses.

---

# Future Evolution

Future documentation may expand this domain into:

knowledge/permissions/

README.md

filesystem.md

providers.md

network.md

credentials.md

authorization.md

This document remains the conceptual foundation of the permission model.

---

# Summary

Permissions define whether OpenClaw is authorized to perform operations on operational resources.

By separating permissions from capabilities, the architecture improves diagnostic accuracy, supports least-privilege operation, and maintains clear responsibility boundaries between OpenClaw and its execution environment.