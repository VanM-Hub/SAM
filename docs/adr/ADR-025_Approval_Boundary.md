# ADR-025 — Approval Boundary

**Status:** Accepted
**Date:** 2026-07-30
**Deciders:** Architecture Freeze v10

## Context

Approval Runtime adalah boundary antara keputusan teknis dan kebijakan organisasi.

## Decision

Approval Runtime berdiri sebagai subsystem independen:
- PolicyEngine menentukan aturan
- WorkflowEngine menentukan alur
- MultilevelEngine menentukan chain of approvals

## Consequences

- Approval terpisah dari Decision Runtime (single responsibility)
- Bisa diubah tanpa mempengaruhi pipeline lain
- Audit trail di HistoryEngine
