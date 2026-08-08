# IP-3.2-002 Engineering Verdict - Runtime Planning & Scheduling

- **Mission**: MISSION-3.2 - Autonomous Runtime
- **Implementation Package**: IP-3.2-002
- **Architecture Order**: AO-3.2-001
- **Lead Engineer Directive**: ED-3.2-002
- **Status**: **IMPLEMENTATION COMPLETE** (read-only planning, no authority)
- **Tanggal**: 2026-08-09
- **Oleh**: Lead Implementation Engineer (ZARA)

---

## Ringkasan

IP-3.2-002 memberikan Runtime kemampuan **menyusun rencana operasional** berdasarkan kondisi yang diamati (memperluas observasi IP-3.2-001). Prinsip inti: **"Plan, never decide"** - Runtime boleh merencanakan, tetapi tidak pernah mengambil keputusan konstitusional.

Seluruh implementasi berada dalam bounded context `src/sam/autonomy_runtime/` (sesuai ED-3.2-001) pada direktori yang diizinkan: `planning/`, `scheduling/`, `optimization/`, `api/`, `compliance/`. Tidak ada implementasi pada `recovery/`, `healing/`, `coordination/` (scope paket berikutnya).

## Deliverables (WP-11 s/d WP-20)

| WP | Capability | Output | Status |
|---|---|---|---|
| WP-11 | Runtime Planning Model | `RuntimePlan`, `PlanningContext`, `PlanningMetadata`, `PlanStep` (immutable DTO) | COMPLETE |
| WP-12 | Runtime Planning Engine | `PlanningEngine` - deterministic plan dari observation & diagnostics | COMPLETE |
| WP-13 | Dependency Planner | `DependencyPlanner` - planning via dependency graph tanpa mutasi | COMPLETE |
| WP-14 | Scheduling Engine | `SchedulingEngine`, `SchedulingProposal`, `ScheduledStep` (proposal only) | COMPLETE |
| WP-15 | Readiness-based Planner | `ReadinessBasedPlanner`, `ReadinessPriority`, `ReadinessPlanResult` | COMPLETE |
| WP-16 | Planning Optimization | `PlanningOptimizer`, `OptimizationResult` (deterministic heuristic, bukan AI/LLM) | COMPLETE |
| WP-17 | Planning API | `PlanningAPI` - read-only facade: plan(), schedule(), optimize(), summarize() | COMPLETE |
| WP-18 | Planning Explainability | `PlanningExplainer`, `PlanningExplanation` - why a plan was generated | COMPLETE |
| WP-19 | Planning Compliance | `compliance/planning_checker.py` - verifikasi "planning without authority" | COMPLETE |
| WP-20 | Integration & Certification | `tests/autonomy_runtime/test_wp20_certification.py` - 20 tests e2e | COMPLETE |

## Package Structure

```
src/sam/autonomy_runtime/
|-- planning/
|   |-- models.py            (WP-11) immutable DTO: RuntimePlan, PlanningContext, dst.
|   |-- engine.py            (WP-12) PlanningEngine
|   |-- dependency_planner.py(WP-13) DependencyPlanner
|   |-- readiness_planner.py (WP-15) ReadinessBasedPlanner
|   |-- explainability.py    (WP-18) PlanningExplainer
|   -- __init__.py
|-- scheduling/
|   -- engine.py            (WP-14) SchedulingEngine
|-- optimization/
|   -- engine.py            (WP-16) PlanningOptimizer
|-- api/
|   -- planning.py          (WP-17) PlanningAPI facade
-- compliance/
    -- planning_checker.py  (WP-19) compliance "planning without authority"
```

## Engineering Constraints Compliance

### Forbidden -> Tidak Terjadi
| Forbidden | Verifikasi |
|---|---|
| Runtime mutation | Tidak ada definisi/panggilan fungsi mutasi runtime (compliance PLN-03) |
| Runtime execution | Semua action ber-label `plan_*` (proposal, bukan eksekusi) |
| Workflow mutation | Tidak ada API/import ke Workflow mutation |
| Policy mutation | Tidak ada API/import ke Policy mutation |
| Mission mutation | Tidak ada API/import ke Mission mutation |
| Approval invocation | Tidak ada token approval (compliance PLN-01) |
| External side effect | Tidak ada aksi eksternal; semua murni komputasi + read-only |
| Hidden state | Semua DTO immutable (frozen dataclass, ADR-023) |
| Non-deterministic planning | Semua plan deterministic (plan_id + isi konsisten antar pemanggilan) |

### Required -> Terpenuhi
| Required | Verifikasi |
|---|---|
| Deterministic planning | `test_planning_deterministic`, `test_optimizer_deterministic` |
| Explainable scheduling | `PlanningExplainer.explain_plan` (basis + kondisi + alasan) |
| Evidence-backed planning | `PlanningContext` dari observation + diagnostics; basis terekam di metadata |
| Readiness-aware prioritization | `ReadinessBasedPlanner` (healthy > degraded > unavailable) |
| Dependency-aware sequencing | `DependencyPlanner` + `PlanningEngine._prereqs_of` (dependency asli) |
| Immutable planning output | `RuntimePlan`, `SchedulingProposal`, `OptimizationResult` frozen |

## Design Decision - Prerequisite Dependency (perbaikan desain)

**Temuan**: Pada `PlanningEngine._prereqs_of` (WP-12) awal, prerequisite dependency difilter hanya komponen yang sehat - ini menghilangkan info dependency untuk target yang sendiri tidak available. Akibatnya `SchedulingEngine` (WP-14) salah menilai jadwal (target unavailable dianggap tanpa prasyarat -> siap).

**Keputusan**: `prerequisite_ids` menyimpan **dependency asli** (semua komponen yang harus siap, terlepas dari status saat ini). Penilaian "apakah prerequisite tersedia saat ini" adalah domain `SchedulingEngine` (via parameter `available`), bukan perekam dependency. Ini menjaga dependency-aware sequencing konsisten di seluruh WP-12/13/14/16.

## Design Decision - Isolasi Bounded Context antar-IP

**Temuan**: `compliance/checker.py` (IP-3.2-001) sebelumnya me-rglob seluruh package. Setelah IP-3.2-002 menambah `planning/`, `scheduling/`, `optimization/`, `api/planning.py`, `compliance/planning_checker.py`, checker observasi ikut mengaudit file IP-3.2-002 dan memunculkan false-positive.

**Keputusan**: `default_source_files` (checker IP-3.2-001) kini membatasi scan ke implementasi observasi saja (observation/, diagnostics/, readiness/, api/observation.py, compliance/checker.py). Compliance IP-3.2-002 ditangani oleh `planning_checker.py` tersendiri. Ini menjaga isolasi akuisisi compliance antar-IP.

## Test Evidence

| Suite | Jumlah | Hasil |
|---|---|---|
| `tests/autonomy_runtime/test_wp20_certification.py` (IP-3.2-002) | 20 | **20 passed** |
| `tests/autonomy_runtime/test_wp10_certification.py` (IP-3.2-001) | 10 | **10 passed** (tanpa regresi) |
| `tests/governance_intelligence` (MISSION-3.1) | 122 | **122 passed** (tanpa regresi) |
| Compliance planning "without authority" | 6 | **6/6 passed** |

## Exit Criteria Verification

IP-3.2-002 dinyatakan selesai karena Runtime mampu secara deterministik:
- [x] **membangun rencana operasional** -> `PlanningEngine.build_plan`
- [x] **menyusun urutan kerja** -> `PlanningAPI.plan` + `PlanStep` berurutan
- [x] **menjelaskan alasan sequencing** -> `PlanningExplainer` (priorities + dependencies)
- [x] **mengoptimalkan urutan berdasarkan observation** -> `PlanningOptimizer.optimize`
- [x] **mempertimbangkan dependency dan readiness** -> `DependencyPlanner` + `ReadinessBasedPlanner`
- [x] **tanpa pernah melakukan aksi terhadap Runtime maupun Governance** -> compliance PLN-01..06 + semua action ber-label `plan_*`

## Engineering Success Criteria Verification

- [x] Seluruh WP-11 sampai WP-20 selesai
- [x] Seluruh evidence tersedia (test evidence di atas)
- [x] Baseline IP-3.2-001 tetap lulus tanpa regresi (10 passed)
- [x] Seluruh compliance "planning without authority" lulus (6/6)
- [x] Tidak terdapat Architecture Drift maupun Runtime Drift (semua implementasi dalam bounded context yang diizinkan)

## Catatan Baseline CI

Seperti IP-3.2-001, `tests/autonomy_runtime/` saat ini **belum menjadi bagian baseline CI** (`ci.yml`). Perluasan baseline = bagian Program A (bertahap + persetujuan). Test ter-commit namun belum dieksekusi CI. IP-3.2-002 belum dinyatakan Operational sampai baseline diperluas + review Chief Architect.

## Kewenangan Masa Depan (di luar scope)

Aksi nyata - recovery, restart, scheduling eksekusi, orchestration - adalah scope IP-3.2-003 (Recovery & Self Healing) dan seterusnya, yang membutuhkan Architecture Order tersendiri dan tetap dalam batas konstitusional SAM. IP-3.2-002 berhenti pada proposal.
