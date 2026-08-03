# OP-620: Approval Runtime Activation Preview
**Project:** SAM | **Version:** v5.18.0 | **Sprint:** 61

## Activation Architecture

```
Approval Lifecycle → Approval Activation (preview)
                          │
                    ┌─────▼──────┐
                    │ Activation │
                    │  Engine    │
                    │            │
                    │ Readiness  │ → score 0.0-1.0
                    │ Blockers   │ → missing IDs, cancelled, closed
                    │ Decision   │ → APPROVE / HOLD / ESCALATE / REJECT / NONE
                    │ State      │ → PENDING / EVALUATED / READY / BLOCKED / INVALID / WAITING
                    └─────┬──────┘
                          │
                          ▼
              Existing Decision Runtime
```

## Activation Rules

| Condition | Readiness Score | State | Decision |
|---|---|---|---|
| Session ready, Lifecycle READY, ≥1 transition | ≥ 0.8 | READY | APPROVE |
| Session ready, Lifecycle VALIDATED | 0.5-0.7 | WAITING | ESCALATE |
| Blockers found (missing IDs, cancelled) | varies | BLOCKED | HOLD |
| No readiness | < 0.5 | PENDING | NONE |

## Pipeline: 16 tahap

```
Receive → Validate → Normalize → Context
→ Evaluate → Plan → Approval Prep
→ Approval Adapter → Submission Orchestrator
→ Approval Gateway → Approval Session
→ Approval Lifecycle → Approval Activation (preview)
→ Existing Decision Runtime → Reasoning → Learning → Execution Preview
```

## Approval Boundary

**TIDAK:** submit, approve, reject, execute, async, thread, network.

**HANYA:** activation preview — evaluasi layak/tidak masuk Approval Runtime.
