# ADR-019 — Recovery Contract

**Status:** Accepted
**Date:** 2026-07-27
**Deciders:** Runtime Architecture Decisions

## Context

Recovery harus meminimalkan kehilangan pekerjaan, dan tidak hanya mengembalikan proses tetapi juga konteks operasional.

## Decision

Recovery menggunakan rantai Session → Snapshot → Checkpoint → Replay. Checkpoint wajib immutable. Setiap operasi penting memiliki recovery point. Jika Replay gagal, Runtime masuk SAFE_MODE.

## Consequences

- Checkpoint wajib immutable.
- Setiap operasi penting memiliki recovery point.
- Jika Replay gagal, Runtime masuk SAFE_MODE.

## Rejected Alternatives

- Recovery hanya dari Session (tanpa checkpoint).
- Recovery hanya restart proses (tanpa restore konteks).
