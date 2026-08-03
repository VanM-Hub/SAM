# OP-650: Approval Intake Runtime
**Project:** SAM | **Version:** v6.0.0 | **Sprint:** 64 | **Phase:** VI

## Architecture

```
Decision Runtime (v5.20.0)
       │
       ▼
Immutable FinalDecisionRecord
       │
       ▼  (operator explicitly submits)
       │
┌──────┴─────────────────────────────────────┐
│  APPROVAL RUNTIME (v6.0.0)                 │
│  ┌──────────────────────────────────────┐  │
│  │ Intake Pipeline                      │  │
│  │                                      │  │
│  │ Receive  → Validate → Normalize      │  │
│  │   → Register → Summary              │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  ┌─ Conversation Bridge (10 queries)      │
│  └─ Dashboard Bridge (6 immutable cards)  │
└────────────────────────────────────────────┘
```

## Files Created (Sprint 64)

| File | Role |
|---|---|
| `intake_record.py` | DTO: ApprovalIntakeRecord, IntakeMetadata, IntakeSource |
| `intake_validator.py` | Validasi required fields, integrity, version, duplicates |
| `intake_normalizer.py` | Normalisasi ids, metadata, categories, labels |
| `intake_registry.py` | In-memory registry: register, exists, get, list |
| `intake_summary.py` | ApprovalIntakeSummary: readiness, findings, warnings |
| `conversation_intake.py` | 10 DTO-only queries |
| `dashboard_intake.py` | 6 immutable cards |
| `runtime_v1.py` | Intake Pipeline + ApprovalRuntimeV1 entry point |

## Design Decisions

- **Independen**: Tidak nyambung otomatis ke Decision Runtime. Operator harus explicit submit.
- **Frozen DTOs**: Semua immutable.
- **Synchronous**: Deterministik, tidak ada async/thread/network.
- **In-memory**: Tidak ada persistence.
