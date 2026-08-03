# ADR-022 — Runtime Isolation

**Status:** Accepted
**Date:** 2026-07-30
**Deciders:** Architecture Freeze v10

## Context

Runtime subsystem tidak boleh saling bergantung secara implementasi. Guardian tidak boleh import Decision Engine secara langsung.

## Decision

Isolasi ditegakkan dengan:
1. **No direct imports** antar runtime — hanya via bridges
2. **Bridge Router** di Runtime Kernel sebagai routing layer
3. **Transform Engine** untuk konversi DTO cross-subsystem

## Consequences

- 0 cyclic dependency antar runtime
- Pipeline bisa dihentikan/dilewati tanpa crash
- Testing mocking mudah
- Overhead routing minimal
