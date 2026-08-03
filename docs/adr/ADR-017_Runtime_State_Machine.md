# ADR-017 — Runtime State Machine

**Status:** Accepted
**Date:** 2026-07-27
**Deciders:** Runtime Architecture Decisions

## Context

Lifecycle harus deterministik. Seluruh komponen Runtime harus mengetahui state yang sama pada waktu yang sama.

## Decision

Runtime menggunakan satu State Machine global. 12 state telah didefinisikan. Semua transisi melalui Runtime Coordinator; tidak ada komponen yang boleh mengubah state sendiri. Setiap transisi menghasilkan Lifecycle Event.

## Consequences

- 12 state yang telah didefinisikan.
- Semua transisi melalui Runtime Coordinator.
- Tidak ada komponen yang boleh mengubah state sendiri.
- Setiap transisi menghasilkan Lifecycle Event.

## Rejected Alternatives

- State machine per modul.
- State yang implisit (tidak terdefinisi).
