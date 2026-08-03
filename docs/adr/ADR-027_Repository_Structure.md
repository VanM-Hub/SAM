# ADR-027 — Repository Structure

**Status:** Accepted
**Date:** 2026-07-30
**Deciders:** Architecture Freeze v10

## Context

Repository memiliki 52 package di `src/sam/`, banyak yang legacy.

## Decision

Struktur saat ini di-freeze sebagai baseline. Legacy package (`sam/runtime/`, `sam/reasoning/`, `sam/workflow/`) dipertahankan untuk backward compatibility.

## Consequences

- Legacy code tidak dihapus — hanya didokumentasikan sebagai deprecated
- Arsitektur baru di `sam/runtime_kernel/`, `sam/guardian/live/`, `sam/operations/brain/decision/`
- Butuh pembersihan di masa depan
