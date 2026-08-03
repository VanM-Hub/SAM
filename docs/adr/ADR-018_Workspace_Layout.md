# ADR-018 — Workspace Layout

**Status:** Accepted
**Date:** 2026-07-27
**Deciders:** Runtime Architecture Decisions

## Context

Kebutuhan portabilitas, backup sederhana, dan self-contained persistence.

## Decision

Workspace menjadi root seluruh persistence. Seluruh data berada di satu direktori. Workspace dapat dipindahkan, dibackup, dan direstore; tidak ada data di luar Workspace.

## Consequences

- Seluruh data berada di satu direktori.
- Workspace dapat dipindahkan, dibackup, dan direstore.
- Tidak ada data di luar Workspace.

## Rejected Alternatives

- Data tersebar di berbagai lokasi (Registry, /etc, /var, dll.).
