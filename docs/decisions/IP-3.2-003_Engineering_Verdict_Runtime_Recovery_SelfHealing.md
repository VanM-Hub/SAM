# IP-3.2-003 Engineering Verdict - Runtime Recovery & Self-Healing Strategy

- **Mission**: MISSION-3.2 - Autonomous Runtime
- **Implementation Package**: IP-3.2-003
- **Architecture Order**: AO-3.2-001
- **Lead Engineer Directive**: ED-3.2-003
- **Status**: **IMPLEMENTATION COMPLETE** (strategic recovery, proposal only)
- **Tanggal**: 2026-08-09
- **Oleh**: Lead Implementation Engineer (ZARA)

---

## Ringkasan

IP-3.2-003 memberikan Runtime kemampuan **menyusun strategi pemulihan** - bukan langsung melakukan pemulihan otomatis. Prinsip inti: **"Recover by strategy, never by authority."** Runtime boleh memahami kegagalan dan menyusun strategi recovery, tetapi tidak pernah melakukan recovery konstitusional secara sepihak.

Seluruh implementasi dalam bounded context `src/sam/autonomy_runtime/` pada direktori yang sah untuk IP ini: `recovery/` (analisis & strategi) dan `healing/` (planner & model proposal). Tidak ada executor, tidak ada mutasi Runtime.

## Paket Layer (sesuai ED-3.2-003)

| Layer | Isi | Peran |
|---|---|---|
| `recovery/` | analisis & strategi | RecoveryContext, FailureAnalysis, RecoveryStrategy, Impact, Recommendation, Explainability |
| `healing/` | planner & model proposal | SelfHealingPlanner, SelfHealingPlan, HealingStep |
| `api/` (bersama) | RecoveryAPI fasad read-only | analyze(), recover_plan(), recommend() |
| `compliance/` (bersama) | recovery_checker | verifikasi "recovery without execution" |

## Deliverables (WP-21 s/d WP-30)

| WP | Capability | Output | Status |
|---|---|---|---|
| WP-21 | Recovery State Model | `RecoveryContext`, `RecoveryMetadata` (immutable) | COMPLETE |
| WP-22 | Failure Analysis Engine | `FailureAnalyzer`, `FailureAnalysis` (deterministik dr diagnostics) | COMPLETE |
| WP-23 | Recovery Strategy Engine | `RecoveryStrategyEngine`, `RecoveryStrategy` (evidence & readiness) | COMPLETE |
| WP-24 | Self-Healing Planner | `SelfHealingPlanner`, `SelfHealingPlan` (proposal only) | COMPLETE |
| WP-25 | Recovery Impact Analyzer | `RecoveryImpactAnalyzer`, `RecoveryImpactReport` | COMPLETE |
| WP-26 | Recovery Recommendation | `RecoveryRecommender`, `RecoveryRecommendation` (evidence & trust) | COMPLETE |
| WP-27 | Recovery API | `RecoveryAPI` - read-only: analyze(), recover_plan(), recommend() | COMPLETE |
| WP-28 | Recovery Explainability | `RecoveryExplainer`, `RecoveryExplanation` (mengapa strategi dipilih) | COMPLETE |
| WP-29 | Recovery Compliance | `compliance/recovery_checker.py` (verifikasi 8 check) | COMPLETE |
| WP-30 | Integration & Certification | `tests/autonomy_runtime/test_wp30_certification.py` (18 tests e2e) | COMPLETE |

## Package Structure

```
src/sam/autonomy_runtime/
|-- recovery/
|   |-- models.py            (WP-21) RecoveryContext, RecoveryMetadata (immutable)
|   |-- failure_analysis.py  (WP-22) FailureAnalyzer, FailureAnalysis
|   |-- strategy.py          (WP-23) RecoveryStrategyEngine, RecoveryStrategy
|   |-- impact.py            (WP-25) RecoveryImpactAnalyzer, RecoveryImpactReport
|   |-- recommendation.py    (WP-26) RecoveryRecommender, RecoveryRecommendation
|   |-- explainability.py    (WP-28) RecoveryExplainer, RecoveryExplanation
|   `-- __init__.py
|-- healing/
|   |-- models.py            (WP-24) SelfHealingPlan, HealingStep
|   |-- planner.py           (WP-24) SelfHealingPlanner
|   `-- __init__.py
|-- api/
|   `-- recovery.py          (WP-27) RecoveryAPI, RecoverySummary
`-- compliance/
    `-- recovery_checker.py  (WP-29) compliance "recovery without execution"
```

## Engineering Constraints Compliance

### Forbidden -> Tidak Terjadi
| Forbidden | Verifikasi |
|---|---|
| Runtime restart | Tidak ada token restart/panggilan (REC-01) |
| Runtime mutation | Tidak ada definisi fungsi mutasi (REC-03) |
| Automatic healing | Tidak ada auto_heal / apply_recovery / execute_heal (REC-01, REC-04) |
| Automatic rollback | Tidak ada rollback execution (REC-01) |
| Approval invocation | Tidak ada token approval (REC-05) |
| Workflow / Mission / Policy mutation | Tidak ada import/aksi ke modul tersebut (REC-02) |
| External side effect | Tidak ada impor jaringan/fs eksternal (REC-06) |
| Hidden persistent state | Tidak ada sqlite/open(write)/pickle/json.dump (REC-07) |

### Required -> Terpenuhi
| Required | Verifikasi |
|---|---|
| Deterministic recovery analysis | `test_strategy_deterministic_and_proposal`, compliance REC-08 |
| Explainable recovery strategy | `RecoveryExplainer.explain_plan` (evidence + rationale) |
| Evidence-backed recommendation | `RecoveryRecommender` (failure class + confidence + risk) |
| Trust-aware recovery proposal | `RecoveryOption.trust_score` (0..100) |
| Dependency-aware recovery planning | `SelfHealingPlanner._dependency_order` (prereq dulu) |
| Immutable recovery output | Semua DTO frozen (ADR-023), verifikasi via `pytest.raises(Exception)` |

## Design Decisions

1. **failure_analysis root_candidates** - mempertimbangkan komponen gagal DAN degraded sebagai afeksi, karena komponen degraded bisa menjadi penyebab hilir kegagalan (mis. provider degraded membuat gateway gagal). Ini membuat deteksi akar lebih akurat.
2. **healing dependency-first ordering** - `_dependency_order` menggunakan topological ordering (dependency-first) dengan tie-break deterministik (priority turun, step_id naik); fallback ke urutan priority bila cycle (tidak gagal).
3. **trust_score heuristic** - `RecoveryRecommender._trust_score = 0.7*confidence + 0.3*evidence_coverage`, murni deterministik, tanpa AI/LLM.
4. **compliance recovery_checker 8-check** - menegakkan "recovery without execution" via AST scan; checker self-detect di-exclude (pola mapan IP-3.2-001/002).

## Test Evidence

| Suite | Jumlah | Hasil |
|---|---|---|
| `tests/autonomy_runtime/test_wp30_certification.py` (IP-3.2-003) | 18 | **18 passed** |
| `tests/autonomy_runtime/test_wp20_certification.py` (IP-3.2-002) | 20 | **20 passed** (tanpa regresi) |
| `tests/autonomy_runtime/test_wp10_certification.py` (IP-3.2-001) | 10 | **10 passed** (tanpa regresi) |
| `tests/governance_intelligence` (MISSION-3.1) | 122 | **122 passed** (tanpa regresi) |
| Compliance observasi (IP-3.2-001) | 5 | **5/5 passed** |
| Compliance planning (IP-3.2-002) | 6 | **6/6 passed** |
| Compliance recovery (IP-3.2-003) | 8 | **8/8 passed** |

## Exit Criteria Verification

IP-3.2-003 dinyatakan selesai karena Runtime mampu secara deterministik:
- [x] **menganalisis penyebab kegagalan** -> `FailureAnalyzer.analyze`
- [x] **memilih strategi recovery yang sesuai** -> `RecoveryStrategyEngine.build_strategy`
- [x] **menyusun proposal self-healing** -> `SelfHealingPlanner.build_plan`
- [x] **menjelaskan alasan strategi tersebut** -> `RecoveryExplainer.explain`
- [x] **memperkirakan dampak recovery** -> `RecoveryImpactAnalyzer.analyze`
- [x] **menghasilkan rekomendasi berbasis evidence & trust** -> `RecoveryRecommender.recommend`
- [x] **tanpa melakukan aksi recovery terhadap sistem** -> compliance REC-01..08 + seluruh label `recover_*`/`heal_*` (proposal)

## Engineering Success Criteria Verification

- [x] Seluruh WP-21 sampai WP-30 selesai
- [x] Seluruh evidence tersedia (test evidence di atas)
- [x] Baseline IP-3.2-001 & IP-3.2-002 tetap lulus tanpa regresi (10 + 20 passed)
- [x] Compliance "Recovery without Execution" lulus 100% (8/8)
- [x] Tidak terdapat Architecture Drift maupun Runtime Drift

## Catatan Baseline CI

Seperti IP sebelumnya, `tests/autonomy_runtime/` saat ini **belum menjadi bagian baseline CI** (Opsi A, `ci.yml` tidak diubah). Perluasan baseline = bagian Program A (bertahap + persetujuan). Test ter-commit namun belum dieksekusi CI. IP-3.2-003 belum dinyatakan Operational sampai baseline diperluas + review Chief Architect.

## Kewenangan Masa Depan (di luar scope)

**Self-Healing Execution** - melakukan restart, rollback, memulihkan Runtime secara nyata - adalah tahap yang sengaja TIDAK termasuk IP-3.2-003. Misi IP-3.2-003 berhenti pada level analisis, strategi, dan proposal. Eksekusi self-healing membutuhkan Architecture Order tersendiri dan tetap dalam batas konstitusional Foundation SAM.
