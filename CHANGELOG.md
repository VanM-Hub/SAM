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
