# OP-430 — Dispatch Runtime (Sprint 37)

Dokumentasi arsitektur Connector Dispatch Runtime untuk Sprint 37.

---

## 1. Dispatch Architecture

Dispatch Runtime adalah lapisan yang mengirim Execution Package ke Connector secara aman. Seluruh connector masih menggunakan Mock Connector.

```
Execution Engine
    ↓
Dispatch Builder (OP-422)
    ↓
Dispatch Validator (OP-423)
    ↓
Dispatch Queue (OP-424)
    ↓
Dispatch Audit (OP-425)
    ↓
Guardian → Conversation → Dashboard
    ↓
(Human Approval)
    ↓
Mock Connector Preview
```

**Lokasi kode:** `src/sam/execution/dispatch/`

---

## 2. Queue Model

`DispatchQueue` — in-memory priority queue:
- Enqueue/dequeue/cancel/reorder
- Priority-based ordering (higher = first)
- No worker thread — purely synchronous
- QueueStatistics for monitoring

---

## 3. Audit Model

`DispatchAudit` — immutable audit trail:
- 6 action types: created, validated, approved, queued, cancelled, previewed
- Filterable by request_id and action
- Auto-summary with counts by action type
- No execution logs — only dispatch lifecycle events

---

## 4. Validation Flow

`DispatchValidator` — 8 validation categories:
- connector_exists: connector must be registered
- connector_healthy: connector must be healthy
- approval_exists: approval must be provided when required
- task_complete: dispatch must have tasks
- dependency_complete: task IDs are coherent
- rollback_ready: retry counts within limits
- policy_satisfied: target must be healthy
- capability_satisfied: tasks must have actions

---

## 5. Files (ringkasan)

| File | Baris | Isi |
|---|---|---|
| `dispatch_request.py` | ~120 | Core DTOs: DispatchRequest, DispatchTask, DispatchBatch, DispatchStatus, DispatchPriority |
| `dispatcher.py` | ~170 | ConnectorDispatcher, DispatchSession, DispatchContext, DispatchReport |
| `dispatch_validator.py` | ~200 | DispatchValidator, 8 validation categories |
| `dispatch_queue.py` | ~180 | DispatchQueue, priority queue with enqueue/dequeue/cancel/reorder |
| `dispatch_audit.py` | ~100 | DispatchAudit, immutable audit trail |
| `conversation_dispatch.py` | ~260 | ConversationDispatchBridge, 10 query types |
| `dashboard_dispatch.py` | ~130 | DispatchDashboardBuilder, 6 DTO cards |
| `integration_dispatch.py` | ~170 | DispatchIntegrationPipeline |

Signature: ZARA 🦋
