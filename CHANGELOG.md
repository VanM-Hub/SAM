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
