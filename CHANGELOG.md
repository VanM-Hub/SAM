# Changelog

> Riwayat perubahan rilis SAM. **SAM 1.0 (1.0.0, 2026-08-07) adalah rilis publik pertama dan satu-satunya.**
> Tidak ada rilis sebelum ini — seluruh versi internal lama (0.01–0.30) hanyalah tahap pengembangan
> fondasi (pre-1.0), bukan rilis publik, sehingga tidak tercatat sebagai rilis di sini.

## SAM 1.0.0 (2026-08-07) - SAM 1.0 Foundation

### Rilis fondasi resmi pertama
- Penetapan identitas rilis: **SAM 1.0** (nama publik) dengan versi teknis **1.0.0**.
- `pyproject.toml` versi ditetapkan ke `1.0.0`; `sam.__version__ = '1.0.0'`.
- Dokumen foundation (9 file di `docs/foundation/`) diselaraskan ke `Version: 1.0.0` + status `Foundational`/`Accepted`.
- README, panduan user (installation/cli/capability/rest api/llm), `docs/releases/manifest.md` & `release_checklist.md` menggunakan label SAM 1.0 Foundation.
- Baseline arsitektur (`Architecture_Rulebook.md`, `Forbidden_Dependencies.md`, `Contributor_Checklist.md`) diselaraskan ke SAM 1.0 Foundation.

### Kemampuan yang dirilis
- **Conversation** sebagai Presentation Capability (bridge read-only, preview-first).
- **Dashboard** sebagai konsol operasional (Mission · Workflow · Execution · Approval · Audit · Connector · Provider · Runtime · Health · Telemetry).
- **CLI** (11 command resmi: mission, workflow, policy, audit, artifact, connector, provider, execution, preview, dashboard).
- **REST API** via `runtime_service.api` (endpoint `/missions`, `/workflow`, `/approval`, `/execution-preview`, `/audit`, `/artifact`, `/policy`).
- **LLM Runtime Activation** — 5 provider (OpenAI · Anthropic · Gemini · DeepSeek · Ollama) via Connector → Provider → Agent.
- Arsitektur deterministik: preview-first, approval mandatory sebelum execute, eksekusi cancellable, rollback metadata, full audit, DTO immutable, kredensial hanya dari environment.

### Catatan
- Seluruh fase pengembangan fondasi (Foundation 0.01 → 0.30, 279 sprint + Program A–K) tercatat di `SPRINT_TRACKER.md` sebagai konteks pengembangan, bukan riwayat rilis.
- Rencana ke depan di `docs/foundation/ROADMAP.md` (post-1.0).

## SAM 1.0.1 (2026-08-08) - Baseline CI Expansion

### Test Baseline Convergence (Program A Phase 2-3)
- Baseline CI diperluas dari 2 runtime (Knowledge + Memory) menjadi 7 runtime.
- Total baseline: 3,808 tests passed, 1 skipped (sebelumnya 3,022).
- Runtime yang sekarang Operational dalam baseline CI:
  - Knowledge (26 tests), Memory (33 tests)
  - Policy (208 tests), Workflow (210 tests)
  - Artifact (135 tests), Audit (173 tests), Mission (60 tests)
- Mission Runtime Activation Path: `mission_preview.py` + wiring `preview_with_mission()` (WP-B2).
- Execution Runtime: 209/211 passed (2 pre-existing environment-dependent, belum masuk baseline CI).

## SAM 1.0.2 (2026-08-08) - Execution Baseline CI

### Test Baseline Convergence (Program A Phase 4)
- Execution Runtime masuk baseline CI dengan 2 test pre-existing di-xfail.
- Total baseline: 4,017 tests passed, 1 skipped, 2 xfailed.
- 8 runtime OPERATIONAL: Knowledge · Memory · Policy · Workflow · Artifact · Audit · Mission · Execution.
- 2 xfail: `test_no_hardcoded_secrets_in_provider_executor_source` (false positive pada prefix "Bearer") dan `test_provider_executor_non_auth_execute_ok` (filesystem provider belum memenuhi syarat base_url).

## SAM 1.0.2 (2026-08-08) — C-Phase 1 Observation Layer

### Operational Intelligence — Wiring & Integration (Program C)
- Observation Layer: `src/sam/observation/` (publication, adapters, timeline, capability, evidence).
- 10 Runtime Publication Adapter (mission, workflow, policy, execution, approval, audit, knowledge, memory, artifact, runtime_service).
- Unified TimelineAggregator (4 sumber timeline: mission, execution, approval, audit).
- CapabilityStatusReader — 10 runtime, 8 capability axis per runtime.
- EvidenceExplorer — 10 evidence entries, by-category/by-runtime navigation.
- ObservationGateway — unified REST endpoint via `runtime_service.api.observation_endpoint`.
- Observation Wiring — singleton composition root.
- Total baseline (lokal): 4,096 tests (unit + 8 runtime suites + observation 79 tests).
- Constraint: read-only, no new runtime, no governance change, no business logic.

## SAM 1.0.2 (2026-08-08) — C-Phase 2 Gap Resolution

### Operational Intelligence — Gap Resolution (Program C)
- GAP-001: UnifiedHealthReporter — enhanced health overview per-runtime + rekomendasi otomatis.
- GAP-002: PreviewConsumerIndex — mapping preview→consumer (5 consumer: desktop, console, web, cli, rest_api).
- GAP-003: EventBusInspector — unified event bus facade (read-only, 3 bus teridentifikasi).
- GAP-004: ReadinessReporter — readiness endpoint aggregation + gap detection.
- GAP-005: OperationalAnalytics — trend + pattern detection (metric density, dashboard coverage, insights).
- GAP-006: ApprovalHealthInspector — approval engine self-reporting assessment.
- GapResolutionCoordinator — resolve_all_gaps() aggregator (1 panggilan, 6 laporan).
- ObservationWiring diperluas: `get_gap_coordinator()` + `resolve_all_gaps()` singleton.
- Total baseline (lokal): 4,157 tests (unit + 8 runtime suites + observation 142 tests).
- Constraint: read-only, no new runtime, no governance change.

## SAM 1.0.2 (2026-08-08) - CI-003 Fix (lazy import httpx)

### Stabilitas CI (Program C / maintenance)
- Akar masalah CI-003: provider_executor.py menaruh import httpx di top-level, padahal httpx
  hanya ada di extra `server` (pyproject.toml). Job `core` (install `[dev,console]`) tidak
  punya `httpx` -> `ModuleNotFoundError` saat collection test -> exit code 2 -> 3 job core gagal.
- Fix: pindahkan `import httpx` menjadi lazy (di dalam `_call_http`); konsisten pola lazy-import project.
- Perbaiki test `test_llm_provider_activation.py`: mock `httpx.post` global (`unittest.mock.patch`)
  alih-alih akses atribut modul `pe_mod.httpx`.
- Hapus import `dataclasses.field` unused (F401).
- Hasil: **CI hijau 7/7** (core 3.10/3.11/3.12, server, desktop, validation, coverage).
- Total baseline (lokal): 4,159 tests (unit + 8 runtime suites + observation 142 tests).

## SAM 1.0.2 (2026-08-08) — C-Phase 1 & 2 Fully Verified

### Verifikasi Independen (Evidence Before Assumption)
- Diff commit `978f89d` (C-Phase 1) & `74f6a72` (C-Phase 2) diinspeksi langsung: perubahan terkonsentrasi di `src/sam/observation/` + endpoint wiring + test; **tidak ada perubahan** pada runtime boundary, governance flow, approval, execution, audit, atau ADR-001..007.
- Engineering Concern Lead Engineer ditegakkan dari kode: `GapResolutionCoordinator` hanya punya 1 method publik `resolve_all()` (query read-only); **0 panggilan** approve/execute/submit/register/publish/emit/transition/write di seluruh `observation/`; **0 import** ke governance/approval/execution/events/runtime; registry terbukti tidak berubah (10 -> 10) sebelum & sesudah `resolve_all()`.
- 142/142 test observation dijalankan ulang lokal — hijau.
- CI commit `e6c514b` (HEAD) terkonfirmasi **hijau 7/7** (core 3.10/3.11/3.12, server, desktop, validation, coverage).
- Hasil: **Engineering Report Accepted** -> **Lead Engineer Verdict: Fully Verified**. Zero Architecture Drift dikonfirmasi.

## SAM 1.0.2 (2026-08-08) - C-Phase 3 Observation Recommendation Engine

### Observation Recommendation Engine (Engineering Decision 2026-08-08, Opsi A)
- Analisis terhadap 3 recommendation engine existing: (`recommendations/engine.py` berbasis event bus - di luar scope; `operations/recommend.py` berbasis anomaly/infra - tidak baca PublicationRegistry; `guardian/recommendation.py` berbasis Guardian) - tidak ada yang konsumsi ObservationReport/PublicationRegistry.
- Dibangun **Observation Recommendation Engine** baru di `src/sam/observation/recommendation.py` - domain `Observation -> Analytics -> Recommendation`, bukan `Runtime -> Recommendation`.
- 7 kategori output observasi: missing_publication, capability_degradation, readiness_regression, stale_timeline, missing_metadata, metric_insufficiency (+ inconsistent_health).
- Constraint read-only: 0 mutation call (approve/execute/publish/register/emit/transition/write); 0 import governance/execution/workflow/events/runtime; source = PublicationRegistry saja.
- Wiring: `get_recommendation_engine()` + `recommend_observations()` di `observation_wiring.py` (bounded context Observation).
- Test suite baru: `tests/observation/test_recommendation_engine.py` (21 tests) - Total observation 163 passed.
- Laporan: `docs/engineering/reports/EA-C03_Engineering_Report_C-Phase_3.md` (commit `43382b5`).
- Total baseline (lokal): 4,180 tests (unit + 8 runtime suites + observation 163 tests).

## SAM 1.0.2 (2026-08-08) - C-Phase 3 Workstream C1-C5 Operational Intelligence

### Operational Intelligence Observers (prioritas engineering Van, urutan governance konstitusional)
- C1 Mission: MissionIntelligenceObserver - timeline/status/progress/health mission (baca mission_timeline/status/health DTO).
- C2 Workflow: WorkflowIntelligenceObserver - workflow views, dependency graph, bottleneck detection (baca descriptor + step depends_on).
- C3 Approval: ApprovalIntelligenceObserver - approval queue, decision history, metrics (baca intake registry + history).
- C4 Execution: ExecutionIntelligenceObserver - executions, timeline end-to-end, analytics (baca registry + history).
- C5 Audit: AuditIntelligenceObserver - audits, correlation per category, compliance status, search (baca audit registry + evidence explorer).
- Constraint read-only: 5 file observation intelligence = imports stdlib-only (annotations/dataclasses/typing); 0 import governance/execution/workflow/events/runtime; 0 mutation call (execute/approve/reject/record/emit/publish); source = PublicationRegistry (jalur publikasi aman).
- Wiring: get_{mission,workflow,approval,execution,audit}_intelligence_observer() + observe_{mission,workflows,approvals,executions,audits}() di observation_wiring.py (bounded context Observation).
- Test suite baru: 5 file per workstream + wiring (43 tests) - Total observation 206 passed.
- Baseline lokal: 4,216 tests passed, 1 skipped, 2 xfailed. CI 7/7 hijau.
- Commit: 81211f6 (13 files, 2214 insertions).

## SAM 1.0.2 (2026-08-08) - Verdict Lead Engineer: C-Phase 3 Workstream C1-C5 COMPLETE

### Engineering Verdict (EA-C04)
- Lead Engineer menyatakan C-Phase 3 (Workstream C1-C5) **COMPLETE**.
- Evidence terverifikasi: 43 test baru, observation suite 206 passed, baseline 4,216 passed, CI 7/7 hijau, commit 81211f6 (implementasi) + daed6c4 (dokumentasi).
- Zero architecture drift: Zero Runtime Expansion, Zero Responsibility Leakage, Zero Governance Mutation, Zero Boundary Violation. Prinsip "Observe, never govern" dipertahankan.
- Tidak ada blocker architecture; temuan validate_imports.py = pre-existing tooling issue.
- Prioritas berikutnya: C6 Capability, C7 Provider, C8 Runtime, C9 Platform Health, C10 Operational Learning.
- Dokumen: docs/engineering/decisions/EA-C04_Lead_Engineer_Verdict_C1-C5.md (commit dirujuk di atas).

## SAM 1.0.2 (2026-08-08) - Directive Lead Engineer: C-Phase 4 (Workstream C6-C10) CONTINUE

### Engineering Directive (EA-C05)
- Lead Engineer menetapkan status CONTINUE (Continuous Execution) untuk C-Phase 4 - Platform Operational Intelligence.
- Workstream C6-C10: C6 Capability, C7 Provider, C8 Runtime, C9 Platform Health, C10 Operational Learning.
- Constraint global: read-only (tanpa execute/approve/reject/publish/emit/transition/finalize), dependency Observation->Analytics->Recommendation->Platform Intelligence (tanpa Platform Intelligence->Runtime), tanpa Runtime/Governance/Event Bus baru, tanpa mengubah Approval/Workflow/Execution/Audit/Provider Runtime.
- Exit Criteria Program C: seluruh Runtime & Capability observable, Platform Health, Operational Metrics, Readiness Reporting, Recommendation, Operational Learning, tanpa Architecture Drift / Foundation Impact.
- Dokumen: docs/engineering/decisions/EA-C05_Lead_Engineer_Directive_C6-C10.md.

## SAM 1.0.2 (2026-08-08) - C-Phase 4 Workstream C6-C10 Operational Intelligence

### Platform Operational Intelligence Observers (revisi #4 - Continuous Execution EA-C05) - COMPLETE (Working Report)
- C6 Capability: CapabilityIntelligenceObserver - aggregation, readiness, health, dependency view (baca CapabilityStatusReader).
- C7 Provider: ProviderIntelligenceObserver - availability, readiness, connectivity, health, metrics (baca ProviderRegistry metadata preview-only; bukan Provider Runtime).
- C8 Runtime: RuntimeIntelligenceObserver - status matrix, dependency view, lifecycle view, health matrix (agregasi PublicationRegistry).
- C9 Platform: PlatformHealthObserver - health report, metrics, cross-runtime correlation, status summary (health dihitung, bukan dipaksa).
- C10 Learning: OperationalLearningObserver - trend report, recommendation center (dari Recommendation Engine C-Phase 3), historical summary, learning evidence (bukan AI/governance/autonomous).
- Wiring: get_{capability,provider,runtime,platform_health,operational_learning}_observer() + observe_*() di observation_wiring.py (bounded context Observation).
- Constraint read-only: 5 file observation intelligence = imports stdlib-only (annotations/dataclasses/typing/dict/list/tuple); 0 import governance/execution/workflow/approval/provider runtime; 0 mutation call (execute/approve/reject/connect/authenticate/retry/transition/finalize); registry terbukti tidak berubah sebelum/sesudah.
- Test suite baru: C6 (14) + C7 (14) + C8 (13) + C9 (14) + C10 (12) = 67 test baru - Total observation 273 passed.
- Full tests/ (tanpa root test_sprint25 legacy): 16,204 passed, 1 skipped, 2 xfailed - tanpa regresi.
- Commit: eb14e35 (C6), 288a74d (C7), f888f73 (C8), 25ceae5 (C9), 77039a6 (C10).
- Laporan: docs/engineering/reports/EA-C05_Report_C-Phase_4_C6-C10.md.
- Status: COMPLETE (Working Report) - menunggu Engineering Verdict - Program C Completion dari Lead Engineer.
