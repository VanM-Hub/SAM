# ADR-028 — Runtime Kernel

**Status:** Accepted
**Date:** 2026-07-30
**Deciders:** Architecture Freeze v10

## Context

Runtime Kernel adalah lapisan koordinasi yang baru di Phase X.

## Decision

Runtime Kernel berfungsi sebagai:
1. **Orchestrator** — mengkoordinasikan semua subsystem
2. **Health monitor** — aggregated health checks
3. **Security enforcer** — centralized ACL
4. **Event bus** — cross-subsystem events
5. **Telemetry collector** — aggregated metrics

## Consequences

- 69 file, 13-stage pipeline
- Implementasi awal masih preview-only
- Bridge/adapter pattern untuk extensibility
- FinalInspector memberikan laporan komponen (11 checks)
