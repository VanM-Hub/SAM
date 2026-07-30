# OP-600: Approval Runtime Session
**Project:** SAM | **Version:** v5.16.0 | **Sprint:** 59

## Architecture

```
Decision Runtime V3 Pipeline (Sprint 52→59)
==============================================

  Receive Package
       ↓
  Validate/Normalize
       ↓
  Context Builder
       ↓
  Evaluate (Readiness → Policy → Confidence)
       ↓
  Plan (Alternatives → Strategy → Constraints)
       ↓
  Approval Preparation
       ↓
  Approval Adapter (Envelope → Mapper → Bridge → Status)
       ↓
  Submission Orchestrator (Plan → Queue → Summary)
       ↓
  →→→ Approval Gateway (Router → Validator → Registry) ←←←
       ↓
  →→→ Approval Session (Builder → Validator → Registry) ←←←
       │
       │   ┌──────────────────────────────┐
       │   │  Session Lifecycle            │
       │   │  ┌─────┐                      │
       │   │  │CREATED─────────────────┐   │
       │   │  └──┬──┘                  │   │
       │   │     │ VALIDATED           │   │
       │   │  ┌──▼──┐  ┌──────────────▼┐  │
       │   │  │PENDING│  │  CANCELLED   │  │
       │   │  └──┬──┘  └───────────────┘  │
       │   │     │ ACTIVE                  │
       │   │  ┌──▼──┐                      │
       │   │  │COMPLETED                   │
       │   │  └──┬──┘                      │
       │   │     │ CLOSED                  │
       │   │  ┌──▼──┐                      │
       │   │  │CLOSED◄─────────────────────┘
       │   │  └─────┘
       │   └──────────────────────────────┘
       │
       ↓
  Existing Decision Runtime → Reasoning → Learning → Execution Preview
```

## Session Layer (7 files)

| File | Role |
|---|---|
| `approval_session.py` | 5 DTO: ApprovalSession, State, Reference, Metadata, Statistics, Snapshot |
| `session_builder.py` | Build session from ApprovalGatewayRequest |
| `session_validator.py` | Validate session integrity, references, readiness |
| `session_registry.py` | In-memory registry: register, lookup, search, statistics, snapshot |
| `session_history.py` | Ring buffer (max 1000) tracking created/validated/updated/closed/cancelled |
| `conversation_session.py` | 10 DTO-only queries |
| `dashboard_session.py` | 6 immutable cards |

## Approval Boundary

**TIDAK:**
- submit approval ke Approval Runtime
- approve/reject apa pun
- execute mission
- mengubah src/sam/approval/**
- menggunakan async, thread, network

**HANYA:**
- Lifecycle container
- Preview-only
- Deterministic
- Immutable DTOs

## Future: Approval Runtime Connection

Session ini akan menjadi input bagi Approval Runtime ketika nanti diintegrasikan — tugasnya hanya *mengelola representasi* proses approval.
