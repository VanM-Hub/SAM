# Release Manifest — SAM

## Era Overview

```
v1.x ─── Initial Prototype
  v2.x ─── Mission Runtime
    v3.x ─── Conversation Architecture
      v4.x ─── Guardian Runtime (current)
```

---

## v1.x — Initial Prototype

Prototype awal SAM. Eksperimen arsitektur, capability mapping, dan proof-of-concept.

| Tag | Highlights |
|---|---|
| v1.0.0-rc1 | 559 tests, RC1 validation |
| v1.0.0 | GA release, soak test validated |

---

## v2.x — Mission Runtime

Fokus pada mission execution, knowledge graph, dan plugin ecosystem.

| Tag | Highlights |
|---|---|
| v2.0.0 | Service, telemetry, openclaw connection, autonomous, web |

---

## v3.x — Conversation Architecture

Fokus pada conversation-first interaction, narrative engine, dan desktop UX.

| Tag | Highlights |
|---|---|
| v3.0.0 | Operations Platform: Home, Timeline, Work, Knowledge, History, Settings, Explainability |
| v3.1.0 | UX Polish: Activity Timeline, Work Center, Knowledge & History UX, Assistant, Notification |
| v3.2.0 | Narrative Engine integration |
| v3.2.1 | OpenClaw Connection, Protection Cycle, Runtime Launcher, CI pipeline |

---

## v4.x — Guardian Runtime (Current)

Fokus pada pipeline brain: Observation → Reasoning → Decision → Guardian → Governance → Execution.

### Foundation Phase (Sprint 10–19)

| Tag | Sprint | Highlights |
|---|---|---|
| v4.4.0 | Sprint 10 | Production Certification (OP-141–150) |
| v4.6.0 | Sprint 12 | Presentation Layer Foundation |
| v4.7.0 | Sprint 13 | SAM Console |
| v4.8.0 | Sprint 14 | Operational Console Runtime |
| v4.9.0 | Sprint 15 | Operational Console Features |
| v4.10.0 | Sprint 16 | Desktop Host Foundation |
| v4.11.0 | Sprint 17 | Qt Desktop Implementation |
| v4.12.0 | Sprint 18 | Qt Desktop Workspace |
| v4.12.1 | Sprint 18.1 | Build & CI Readiness |
| v4.20.0 | Sprint 19 | Operational Workbench (10 OP) |
| v4.21.0 | Sprint 19 | Operational Brain Foundation (10 OP) |

### Guardian Phase (Sprint 20–30)

| Tag | Sprint | Highlights | Tests |
|---|---|---|---|
| v4.23.0 | Sprint 21 | Learning & Optimization — **reset point** | — |
| v4.24.0 | Sprint 20 | Proactive Observation & Orchestration | — |
| v4.25.0 | Sprint 22 | Operational Mission Orchestrator (OP-271–280) | 1068 pass |
| v4.26.0 | Sprint 23 | Conversation Intelligence & LLM Layer (OP-281–290) | 1068 pass |
| v4.27.0 | Sprint 24 | Operational Reasoning Runtime (OP-291–300) | — |
| v4.28.0 | Sprint 25 | Operational Decision Runtime (OP-301–310) | — |
| v4.29.0 | Sprint 25B+26 | Event & Alert Layer + Guardian Runtime Integration | 997 pass |
| v4.31.0 | Sprint 27 | Guardian Supervisory Runtime (OP-321–330) | — |
| v4.32.0 | Sprint 28 | Guardian Runtime V2 Integration (OP-331–340) | — |
| v4.33.0 | Sprint 29 | Guardian Governance & Execution Coordination (OP-341–350) | 1282 pass |
| **v4.34.0** | **Sprint 30** | **Guardian E2E Operational Validation (OP-351–360)** | **1392 pass** |

---

## Current Status

- **Latest version:** v4.34.0
- **Latest sprint:** Sprint 30 — Guardian End-to-End Operational Validation
- **Test count:** 1392 passed, 1 skipped, 0 failed
- **Pipeline layers:** Observation → Reasoning → Decision → Guardian → Governance → Readiness → Risk → Explanation → Dashboard → Conversation
- **Next:** Desktop integration, execution engine, provider integration

---

## Version Numbering Convention

- **v4.x.y**: `v{major}.{sprint-cluster}.{patch}`
- Major version bumps (v5.0.0) reserved for architectural breaking changes
- Gap in version numbers is intentional — not every number represents a release
- See [version-history.md](./version-history.md) for full sprint-to-version mapping
