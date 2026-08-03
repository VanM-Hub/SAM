# ADR-026 — Subsystem Independence

**Status:** Accepted
**Date:** 2026-07-30
**Deciders:** Architecture Freeze v10

## Context

Setiap subsystem memiliki lifecycle, DTO, dan pipeline sendiri.

## Decision

Setiap subsystem memiliki:
1. `__init__.py` dengan public API
2. Conversation/Dashboard bridges
3. Pipeline sendiri (input → stages → output)
4. Test suite independen

## Consequences

- 7 subsystem teridentifikasi, masing-masing dengan `__all__`
- Branching/tagging bisa per-subsystem
- Knowledge bus untuk sharing state tanpa coupling
