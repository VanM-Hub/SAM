# Release Notes - Engineering Package R-001 (Product Release)

**Release:** Capability Release - Program G-K (dalam garis keturunan v30.0.0)
**Versi arsitektural:** 30.0.0 (tetap, tanpa bump)
**Baseline:** HEAD `e0c52f3`
**Tanggal:** 2026-08-06
**Category:** Capability presentation / activation release

> Catatan rilis ini menyusun hasil implementasi aktual Program G-K sebagai
> rangkaian activation & presentation capability dalam garis keturunan v30.0.0.
> Seluruh data berdasarkan kode & git history aktual, bukan asumsi.

---

## 1. Yang Baru dalam Rilis Ini

Rilis ini menambahkan **capability presentation host** (G-J) dan mengaktifkan
**jalur runtime LLM** (Connector->Provider->Agent, K) di atas baseline v30.0.0,
tanpa mengubah arsitektur maupun RuntimeService.

| Program | Capability | Komit | Test |
|---|---|---|---|
| G | Conversation (presentation host) | `bda9313` | 14 |
| H | Dashboard (presentation host) | `fe0956a` | 18 |
| I | CLI (presentation host) | `f5bd184` | 21 |
| J | REST API as Presentation Host | `210dcd0` | 19 + 11 |
| K | Aktivasi jalur LLM (Connector->Provider->Agent) | `9ddb5ad` | 35 |

## 2. Program K - Aktivasi Jalur LLM (fokus rilis ini)

K1-K8 mengoperasionalkan jalur runtime LLM yang sebelumnya preview-only, tanpa
menambah runtime baru atau mengubah RuntimeService:

- **K1 Connector Runtime Activation** - `LLMConnectorLayer` mendaftarkan
  connector `llm_chat` (contract `connector.llm.chat`) ke ConnectorRegistry.
- **K2 Provider Runtime Activation** - `ProviderExecutor` (stub -> HTTP nyata
  via **httpx**); peta `provider_id -> LLMAdapter` di-inject (DI).
- **K3 Agent Runtime Activation** - `LLMAgentLayer` + baseline agent
  `mission_agent` (implements connector contract); `AgentBridge` di wiring layer.
- **K4 Provider Activation** - 5 LLM provider **active** (OpenAI, Anthropic,
  Gemini, DeepSeek, Ollama); 5 non-LLM **documented/deferred**; `provider_readiness()`.
- **K5 Host** - semua host tetap lewat `runtime_service.api`; **0 bypass**.
- **K6 E2E** - jalur Presentation->RuntimeService->Connector->Provider->Agent
  tanpa bypass; RuntimeService tidak diubah.
- **K7 Testing** - 35 test Program K PASS; regression non-legacy **3541 passed,
  42 skipped**.
- **K8 Verifikasi** - dependency scan intra-layer only; architecture compliance
  0 bypass; compliance 8 passed; ASCII bersih.

### Aktivasi connector/provider/agent
- `connector_readiness()` -> `ready: True` (registry, capability, binding).
- `provider_readiness()` -> 10 provider dinilai: **5 active** (openai, anthropic,
  gemini, deepseek, ollama - semua punya `LLMAdapter`), **5 missing/documented**
  (deferred). Eksekusi nyata memerlukan env kredensial.

## 3. Known Issues

| ID | Tingkat | Deskripsi |
|---|---|---|
| KI-1 | Ditutup | `tests/legacy/` (test warisan v1.0, 44 file, 65 collection error) dihapus permanen (`e0c52f3`) - mengetes kode lama yang sudah dibongkar; tidak pernah masuk scope resmi. |
| KI-2 | Rendah (dokumentasi) | `INSTALLATION.md`/`USER`/`CLI` guide belum penuh sinkron dengan capability G-K (R3); REST & LLM guide belum tersedia. Dijadwalkan sesi dokumentasi lanjutan. |
| KI-3 | Rendah (dokumentasi) | `manifest.md` Baseline menunjuk `f4edb87`; `version-history` belum mencatat Program G-K. |
| KI-4 | Info | Provider LLM `available: false` tanpa env kredensial - bukan cacat; eksekusi nyata butuh API key. |

## 4. Compatibility Notes

- **Versi:** tetap `30.0.0`; backward-compatible dengan v30.0.0 baseline.
- **Python:** `>=3.8` (diuji 3.10, 3.11, 3.12).
- **Dependency:** `httpx` (baru dipakai Program K) tersedia di extra `server`
  (`sam-ops[server]` / `[all]`).
- **Ekstra install:** `sam-ops[console]` untuk CLI, `sam-ops[server]` untuk REST,
  `sam-ops[desktop]` untuk GUI, `sam-ops[all]` untuk lengkap.
- **Regresi:** regression suite identik baseline (3541 passed) - tidak ada
  breaking change.

## 5. Upgrade Notes

- Dari v30.0.0 (Program F) ke rilis capability ini: **tidak memerlukan migrasi
  data atau skema**; perubahan murni penambahan capability & aktivasi jalur.
- Untuk memakai jalur LLM: set env kredensial provider (mis. `OPENAI_API_KEY`,
  `ANTHROPIC_API_KEY`, dll.) sesuai adapter; tanpa kredensial jalur siap tapi
  eksekusi nyata belum aktif.
- `tests/legacy/` tidak lagi ada - scaffold uji warisan v1.0 dihapus; gunakan
  suite modern (`tests/unit`, `tests/api`, `tests/runtime_service`,
  `tests/presentation`).

---

**Dibuat dari hasil implementasi aktual (git log + test output).**
