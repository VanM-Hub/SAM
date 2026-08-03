# ADR-020 — Lifecycle Events

**Status:** Accepted
**Date:** 2026-07-27
**Deciders:** Runtime Architecture Decisions

## Context

Kebutuhan Auditability, Observability, dan Telemetry atas seluruh perubahan Runtime.

## Decision

Seluruh perubahan Runtime menghasilkan Lifecycle Event. Event Bus menjadi komponen inti Runtime. Semua event memiliki schema yang sama. Event digunakan oleh Operations Console, CLI, Dashboard, dan Telemetry. Tidak ada perubahan state tanpa event.

## Consequences

- Event Bus menjadi komponen inti Runtime.
- Semua event memiliki schema yang sama.
- Event digunakan oleh Operations Console, CLI, Dashboard, dan Telemetry.
- Tidak ada perubahan state tanpa event.

## Rejected Alternatives

- Logging tanpa event terstruktur.
- Event hanya untuk error (tidak untuk lifecycle normal).
