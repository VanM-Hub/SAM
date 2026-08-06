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
- Rencana ke depan di `ROADMAP.md` (post-1.0).
