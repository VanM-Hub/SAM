# ADR-021 — Overall Architecture

**Status:** Accepted
**Date:** 2026-07-30
**Deciders:** Architecture Freeze v10

## Context

SAM terdiri dari 7 runtime subsystem yang beroperasi sebagai pipeline: Guardian Live → Decision Runtime → Approval Runtime → Operational Brain → Activation Runtime → Execution Runtime → Runtime Kernel. Masing-masing independen dan berkomunikasi via DTO (frozen dataclass).

## Decision

Gunakan arsitektur **pipeline-oriented dengan subsystem independence**. Setiap subsystem:
- Punya `__init__.py` dengan `__all__` eksplisit
- Punya ConversationBridge + DashboardBridge
- Berkomunikasi via DTO sebagai contract
- Tidak boleh tahu implementasi internal subsystem lain

## Consequences

- Mudah ditest secara unit (isolasi)
- Extension point via bridges jelas
- DTO adalah public API
- Subsystem bisa dikembangkan independen
