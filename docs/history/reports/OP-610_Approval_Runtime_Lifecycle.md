# OP-610: Approval Runtime Lifecycle
**Project:** SAM | **Version:** v5.17.0 | **Sprint:** 60

## Lifecycle Architecture

```
Approval Gateway → Approval Session → Approval Lifecycle
                                            │
                                     ┌──────▼──────┐
                                     │  State      │
                                     │  Machine    │
                                     │             │
                                     │  CREATED ──────────────────┐
                                     │     │                     │
                                     │     ▼                     │
                                     │  VALIDATED               │
                                     │     │                     │
                                     │     ▼                     │
                                     │  READY                    │
                                     │     │                     │
                                     │  ┌──▼──┐                 │
                                     │  │WAITING                │
                                     │  └──┬──┘                 │
                                     │     ├── CANCELLED ───────┤
                                     │     ▼                     │
                                     │  CLOSED ◄────────────────┘
                                     └──────────────────────────┘
                                            │
                                            ▼
                                   Existing Decision Runtime
```

## Lifecycle Rules

| From State | To States |
|---|---|
| CREATED | VALIDATED, CANCELLED |
| VALIDATED | READY, CANCELLED |
| READY | WAITING, CANCELLED |
| WAITING | READY, CANCELLED, CLOSED |
| CANCELLED | CLOSED |
| CLOSED | — (final) |

## Pipeline Length: 15 tahap

Decision Runtime pipeline sekarang dari Receive → Lifecycle: **15 tahap berurutan, semuanya synchronous, deterministik, preview-only.**

## Approval Boundary

**TIDAK:** submit, approve, reject, execute, async, thread, network.

**HANYA:** state machine immutable untuk ApprovalSession.
