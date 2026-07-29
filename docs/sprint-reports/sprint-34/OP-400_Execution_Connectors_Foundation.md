# OP-400 — Execution Connectors Foundation (Sprint 34)

Dokumentasi arsitektur Execution Connectors untuk Sprint 34.

---

## 1. Arsitektur

Execution Connectors Foundation adalah lapisan yang menghubungkan Guardian Runtime dengan dunia luar TANPA memberi hak eksekusi langsung kepada SAM.

```
Guardian Runtime
    ↓
Decision Runtime
    ↓
Execution Planner
    ↓
Approval Bridge
    ↓
Execution Request (DTO)
    ↓
Conversation → Dashboard
    ↓
(Human Approval)
    ↓
External Connector (Sprint berikutnya)
```

**Lokasi kode:** `src/sam/execution/`

---

## 2. Pipeline

| Langkah | Modul | Output |
|---|---|---|
| Execution Request Creation | `execution_request.py` | ExecutionRequest (frozen, no execute) |
| Connector Protocol | `connector_protocol.py` | ConnectorInfo, ConnectorCapability, ConnectorProtocol (abc) |
| Connector Registry | `connector_registry.py` | RegistryEntry, CapabilityLookup |
| Execution Planning | `execution_planner.py` | ExecutionPlan (dependency order, parallel groups, rollback, risk) |
| Approval Bridge | `approval_execution.py` | ApprovalRequest, ApprovalResult |
| Conversation Bridge | `conversation_execution.py` | ExecutionQueryResult (10 query types) |
| Dashboard | `dashboard_execution.py` | ExecutionDashboard (6 cards) |
| Integration Pipeline | `integration_execution.py` | ExecutionPipelineResult |

---

## 3. DTO (Frozen Dataclass)

| DTO | Modul | Fungsi |
|---|---|---|
| ExecutionStatus | execution_request | Status enum (pending → planned → awaiting_approval → approved/rejected/executing/completed/failed/rolled_back) |
| ExecutionRisk | execution_request | Risk level + score + factors |
| ExecutionParameter | execution_request | Key/value parameter |
| ExecutionTarget | execution_request | Target system/resource |
| ExecutionRequest | execution_request | **Core DTO** — immutable, no execute(), requires approval |
| ExecutionPlan | execution_request | Ordered execution plan |
| ExecutionResult | execution_request | Read-only result |
| ConnectorInfo | connector_protocol | Connector metadata |
| ConnectorCapability | connector_protocol | Action capability |
| RegistryEntry | connector_registry | Registry entry |
| CapabilityLookup | connector_registry | Capability search result |
| DependencyEdge | execution_planner | Dependency edge |
| ApprovalRequest | approval_execution | Approval request |
| ApprovalResult | approval_execution | Approval decision |
| ApprovalItem | approval_execution | Single item needing approval |
| ExecutionQueryResult | conversation_execution | Query result DTO |
| ExecutionPipelineResult | integration_execution | Pipeline result |
| ConnectorCard | dashboard_execution | Dashboard connector overview |
| ExecutionCard | dashboard_execution | Dashboard execution status |
| ApprovalCard | dashboard_execution | Dashboard approval queue |
| CapabilityCard | dashboard_execution | Dashboard capabilities |
| HealthCard | dashboard_execution | Dashboard health |
| QueueCard | dashboard_execution | Dashboard queue |
| ExecutionDashboard | dashboard_execution | Complete dashboard |

---

## 4. Constraints

- **Python 3.8 compatible**
- **frozen dataclass** — semua DTO immutable
- **synchronous only** — tidak ada async/await, threading, asyncio
- **Connector tidak pernah mengeksekusi sendiri** — hanya membuat ExecutionRequest
- **Semua request wajib Approval** — ExecutionApprovalBridge
- **Tidak ada execute() method** — AST scan memverifikasi
- **No domain imports** — execution modules tidak import operations/\*, domain/\*, storage/\*
- **No network calls** — tidak ada requests, http, socket, subprocess
- **No vendor SDK**
- **No auto execution**
- **Backward compatible** — tidak mengubah domain/guardian/reasoning/conversation API

---

## 5. Approval Flow

```
ExecutionPlan
    ↓
ExecutionApprovalBridge.create_approval_request()
    ↓
ApprovalRequest (DTO)
    ↓
Human operator reviews
    ↓
ExecutionApprovalBridge.approve() or reject()
    ↓
ApprovalResult (DTO)
    ↓
Execution Pipeline continues
```

Tidak ada auto-submit. Semua approval request melalui human review.

---

## 6. Rollback Model

Rollback requirement dideteksi oleh ExecutionPlanner:

- **High/critical risk**: rollback required
- **Low/medium risk**: rollback optional
- Rollback information tersedia di ExecutionPlan.rollback_required

---

## 7. Capability Model

Connector mendaftarkan capabilities via `add_capability(ConnectorCapability)`:

- action: nama aksi (read, write, delete, execute, query, dll)
- description: deskripsi
- requires_approval: apakah butuh approval
- risk_level: risk level aksi
- estimated_duration_seconds: estimasi durasi
- parameters: parameter yang dibutuhkan

ConnectorRegistry mendukung lookup by type, by action, dan capability search.

---

## 8. Future Connector Examples (Sprint berikutnya)

Setelah Sprint 34, connector nyata bisa diimplementasikan dengan:

- FileConnector: membaca/menulis file, hanya proposal
- APIConnector: membuat request API sebagai proposal
- DBConnector: query DB sebagai proposal
- CommandConnector: menjalankan command sebagai proposal

Semua connector TIDAK akan execute — hanya membuat ExecutionRequest yang harus melalui approval pipeline.

---

## 9. Files (ringkasan)

| File | Baris | Isi |
|---|---|---|
| `__init__.py` | 3 | Package init |
| `execution_request.py` | ~200 | Core DTOs (ExecutionRequest, ExecutionPlan, ExecutionResult, ExecutionStatus, ExecutionRisk) |
| `connector_protocol.py` | ~180 | Protocol, BaseConnector, ConnectorInfo, ConnectorCapability |
| `connector_registry.py` | ~200 | ConnectorRegistry with duplicate detection & capability lookup |
| `execution_planner.py` | ~220 | ExecutionPlanner with dependency ordering & risk aggregation |
| `approval_execution.py` | ~150 | ExecutionApprovalBridge |
| `conversation_execution.py` | ~300 | ConversationExecutionBridge (10 query types) |
| `dashboard_execution.py` | ~150 | ExecutionDashboardBuilder (6 cards) |
| `integration_execution.py` | ~200 | ExecutionPipeline |

Signature: ZARA 🦋
