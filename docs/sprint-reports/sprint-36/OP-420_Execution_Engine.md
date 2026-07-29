# OP-420 — Execution Engine (Sprint 36)

Dokumentasi arsitektur Execution Engine untuk Sprint 36.

---

## 1. Execution Architecture

Execution Engine adalah lapisan yang mengubah ExecutionPlan menjadi rangkaian Task terstruktur, tervalidasi, dapat di-rollback, tetapi tetap TIDAK mengeksekusi apa pun.

```
Mission Proposal
    ↓
Execution Plan (from Sprint 34)
    ↓
Execution Builder (OP-412)
    ↓
Execution Package
    ↓
Validator (OP-413)
    ↓
Rollback Planner (OP-414)
    ↓
Scheduler (OP-415)
    ↓
Guardian → Conversation → Dashboard
    ↓
(Human Approval)
    ↓
Connector Dispatch (Sprint 37)
```

**Lokasi kode:** `src/sam/execution/engine/`

---

## 2. Task Lifecycle

```
pending → validated → scheduled → ready → dispatched → completed
                                                         ↓
                                                    failed → rolled_back
```

Setiap task memiliki `TaskStatus` yang immutable — perubahan menghasilkan task baru via `with_status()`.

---

## 3. Execution Package

`ExecutionPackage` dihasilkan oleh `ExecutionBuilder.build(plan)`:
- Split ExecutionPlan menjadi tasks
- Membangun dependency graph
- Mengelompokkan parallel tasks
- Menentukan aggregated risk
- Menandai rollback markers

---

## 4. Validation Flow

`ExecutionValidator` memeriksa 8 kategori:

| Kategori | Severity | Deskripsi |
|---|---|---|
| dependency | warning | Missing dependency target |
| duplicate | warning | Duplicate task (same connector+action+target) |
| cycle | error | Circular dependency graph |
| missing_connector | error | Task without connector type |
| missing_approval | error | High-risk task without approval |
| invalid_capability | warning | Unusual action name |
| risk_mismatch | warning | Risk level below expected |
| rollback_completeness | warning | Missing rollback task reference |

---

## 5. Rollback Model

`RollbackPlanner` menghasilkan `RollbackPlan`:

- Reverse execution order: last task rolled back first
- Partial rollback: individual task rollback
- Requires approval for rollback as well
- Can validate completeness vs original package

---

## 6. Scheduler Model

`ExecutionScheduler` menghasilkan `ExecutionQueue`:

- Sequential stages (parallel within each stage)
- Groups from ExecutionPlan preserved
- Re-orderable by dependency via `reorder_by_dependency()`
- Estimated duration computed per stage

---

## 7. Conversation & Dashboard

`ConversationExecutionV2Bridge` — 10 query types:
execution package, execution tasks, dependency graph, rollback, validation, schedule, estimated duration, risk summary, approval state, readiness

`ExecutionDashboardV2Builder` — 6 DTO cards:
ExecutionPackageCard, TaskCard, ScheduleCard, RollbackCard, ValidationCard, RiskCard

---

## 8. Future Connector Execution (Sprint 37)

ExecutionPackage siap dikirim ke connector — semua validasi sudah lulus, approval sudah didapat, schedule sudah siap. Sprint berikutnya akan menghubungkan package ini dengan connector runtime untuk dispatch sungguhan.

---

## 9. Files (ringkasan)

| File | Baris | Isi |
|---|---|---|
| `execution_task.py` | ~120 | Core DTOs: ExecutionTask, TaskGroup, TaskDependency, TaskCondition, TaskResult, TaskStatus, TaskRisk, TaskMetadata |
| `execution_builder.py` | ~170 | ExecutionBuilder, ExecutionPackage |
| `execution_validator.py` | ~250 | ExecutionValidator, 8 validation categories |
| `rollback_planner.py` | ~140 | RollbackPlanner, RollbackPlan, RollbackStep |
| `execution_scheduler.py` | ~160 | ExecutionScheduler, ExecutionQueue, ExecutionStage |
| `conversation_execution_v2.py` | ~250 | ConversationExecutionV2Bridge, 10 query types |
| `dashboard_execution_v2.py` | ~140 | ExecutionDashboardV2Builder, 6 DTO cards |
| `integration_execution_v2.py` | ~130 | ExecutionEnginePipeline |

Signature: ZARA 🦋
