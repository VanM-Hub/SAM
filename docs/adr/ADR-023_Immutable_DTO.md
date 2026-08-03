# ADR-023 — Immutable DTO

**Status:** Accepted
**Date:** 2026-07-30
**Deciders:** Architecture Freeze v10

## Context

DTO adalah kontrak antar subsystem. Mutasi state setelah instantiation menyebabkan side-effect yang sulit dilacak.

## Decision

Semua DTO menggunakan `@dataclass(frozen=True)`.

## Consequences

- 1,010 frozen DTOs telah diidentifikasi
- Immutable = thread-safe (meski synchronous)
- Copy-on-write untuk perubahan
- Validasi di konstruktor, bukan di setter
