# SAM Roadmap

> **Sumber kebenaran tunggal (single source of truth) untuk seluruh fase SAM.**
> Visi: **Deterministic Operational Intelligence Platform** - observasi, pemahaman, perencanaan, koordinasi, penyiapan, dan pengawasan operasi lintas sistem secara aman, dapat diaudit, provider-agnostic, dan dapat dipertanggungjawabkan.

---

## Visi Akhir (End-state)

SAM adalah **Deterministic Operational Intelligence Platform** yang mampu:

- **Mengobservasi** - melihat kondisi sistem
- **Memahami** - memetakan konteks operasional
- **Merencanakan** - menyusun urutan operasi
- **Mengoordinasikan** - mengatur antar-runtime
- **Menyiapkan** - membangun request/aksi
- **Mengawasi** - memantau hingga selesai

Karakteristik kunci:

| Bukan | Melainkan |
|-------|-----------|
| Chatbot | Operational Intelligence Platform |
| LLM | Deterministic engine |
| Autonomous AI | Dapat diaudit & dapat dipertanggungjawabkan |
| AGI | Provider-agnostic (AI hanyalah salah satu provider via Connector Runtime) |

> **Identitas SAM tetap utuh** walaupun provider AI diganti atau dilepas.

---

## Status Saat Ini

> **SAM 4.0 Complete (4.0.0, 2026-08-10) - ARCHITECTURE ACCEPTED - BASELINE RELEASE TERBARU.**
> Roadmap SAM 4.0 (MISSION-4.1 .. MISSION-4.6) **COMPLETE + ARCHITECTURE ACCEPTED** (CA verdict: 4.1 CLOSED, 4.2..4.6 ACCEPTED).
> Federated Governance Platform - seluruh capability 4.0 = baseline resmi arsitektur. Foundation tetap IMMUTABLE (tanpa perubahan identitas sejak SAM 1.x).

Seluruh perjalanan pengembangan (Foundation 0.01 → 0.30, 279 sprint + Program A–K + SAM 1.0/2.0 + SAM 3.x)
menghasilkan platform **Deterministic Operational Intelligence** yang:

- **SAM 1.0** — membangun identitas "Apa itu SAM?"
- **SAM 2.0** — membangun platform operasional "Apakah SAM dapat digunakan?"
- **SAM 3.x** — membangun ekosistem "Bagaimana banyak capability bekerja sebagai satu ekosistem?"
  (Governance Intelligence, Autonomous Runtime, Citizen Ecosystem, Federation, Platform Experience,
  Production Governance) — tanpa mengubah Foundation.
- **SAM 4.0** - membangun platform operasional nyata "Bagaimana capability dijalankan & dioperasikan?"
  (Real Execution, Operational Intelligence, Operational Learning, Governed AI Reasoning,
  Autonomous Operations, Human Operational Experience) - tanpa mengubah Foundation.

Lalu ditutup dengan MISSION-4.6 (Human Operational Experience) dan **Architecture Accepted** oleh Chief
Architect (2026-08-10). Platform kini memasuki **SAM 5 - Universal Governance Platform** sesuai Roadmap.
>
> **Status SAM 5.x (2026-08-13):** MISSION-5.1..5.6 terimplementasi di atas baseline SAM 4.0 (Universal Governance). **rilis v5.0.0 (2026-08-10) + M12 Self-Preservation v5.1.0 (2026-08-13)**. M12 membuat SAM "tahan banting" untuk operasi produksi: durable state + idempotency + restart safety (PostgreSQL persistent + fail-closed), secret manager terenkripsi + identity/auth, multi-mission isolation, NSSM Windows Service + external watchdog, backup/restore terenkripsi (Fernet), dan failure-injection matrix (crash/PG-down/secret-down/corrupt/disk/duplicate - termasuk injeksi PG-down nyata terhadap produksi: /health/ready 503 + BLOCKED, pulih ke ready 200 setelah PG up, truth survive). **M12-016 (12h mission test) ✅ PASS (14 Agu 2026, elapsed 14.5h).** **HTTPS lokal SELESAI (2026-08-13)**: Caddy reverse-proxy self-signed `https://localhost:8443 -> 127.0.0.1:8080`; secure cookie M12-011 TERBUKTI (`Set-Cookie ... Secure`); autostart Caddy PENDING (butuh UAC). **Catatan:** kontrak M12-016 dikurangi 24h -> 12h atas keputusan Van (2026-08-13); task 24h lama dibiarkan sbg bayangan (tak bisa di-disable non-admin).


### Ringkasan Fase I–XXIII (0.01 → 0.23)

| Phase | Nama | Tahap |
|-------|------|-------|
| I | Foundation | 0.01 |
| II | Core Runtime | 0.02 |
| III | Runtime Expansion | 0.03 |
| IV | Guardian Runtime | 0.04 |
| V | Decision Runtime | 0.05 |
| VI | Approval Runtime | 0.06 |
| VII | Operational Brain | 0.07 |
| VIII | Activation Runtime | 0.08 |
| IX | Execution Runtime | 0.09 |
| X | Runtime Kernel | 0.10 |
| XI | Universal Connector Runtime | 0.11 |
| XII | Orchestration Runtime | 0.12 |
| XIII | Mission Runtime | 0.13 |
| XIV | Provider Runtime | 0.14 |
| XV | Agent Runtime | 0.15 |
| XVI | Skill Runtime | 0.16 |
| XVII | Memory Runtime | 0.17 |
| XVIII | Knowledge Runtime | 0.18 |
| XIX | Cognitive Runtime | 0.19 |
| XX | Workflow Runtime | 0.20 |
| XXI | Policy Runtime | 0.21 |
| XXII | Audit Runtime | 0.22 |
| XXIII | Artifact Runtime | 0.23 |

> **0.23 = Architecture Complete.** Seluruh runtime inti deterministik selesai dibangun.

### Program A–K (0.24 → 0.30)

Setelah fondasi arsitektur lengkap, fokus bergeser dari membangun lapisan baru ke
**Product Integration & Operationalization** — membuat seluruh runtime bekerja bersama
untuk pekerjaan nyata. Prinsip tetap: **approval dulu → preview dulu → baru execute**.

| Program | Isi | Tahap |
|---------|-----|-------|
| A | External Connectors (OpenAI · Anthropic · Gemini · DeepSeek · Ollama · OpenClaw · GitHub · Filesystem · SQLite · Docker · Terminal · REST API · MCP) | 0.24 |
| B | Model Runtime Integration (interface chat/embedding/reasoning/vision/tool, provider mapping, certification) | 0.25 |
| C | Real Execution Runtime (execution engine, approval gate, rollback, monitoring, safety, provider activation, Simulation & Preview) | 0.26 |
| D | Runtime Services & Deployment (configuration, secrets, lifecycle, DI, API, server runtime, monitoring) | 0.27 |
| E | Unified Intelligence Runtime (runtime registry, pipeline graph, context assembly) — cabang paralel | 0.28 |
| F | Presentation Layer (desktop, dashboard, conversation bridge) — Sprint 272–279 | 0.29 |
| G | Conversation as Presentation Capability (14 test) | 0.30 |
| H | Dashboard as Presentation Capability (18 test) | 0.30 |
| I | CLI as Presentation Capability (21 test) | 0.30 |
| J | REST API as Presentation Host (19 REST + 11 api test) | 0.30 |
| K | LLM Runtime Activation (5 provider LLM active; 35 test) | 0.30 |

### Tahap-tahap fondasi yang telah selesai (detail)

**Pipeline akhir kemampuan nyata:** Mission → Workflow → Policy → Agent → Skill → Memory →
Knowledge → Cognitive → Orchestrator → Connector → Provider → Model Runtime →
Approval → Execution Runtime → Artifact → Runtime Service → External Provider.

**Kemampuan rilis yang dihasilkan fondasi:**
- **Provider nyata**: OpenAI · Anthropic · Gemini · DeepSeek · Ollama (via Connector → Provider → Agent)
- **Entry point resmi**: `sam.runtime_service` (Runtime API + server)
- **Presentasi**: CLI (`sam mission/workflow/policy/audit/artifact/connector/provider/execution/preview/dashboard`), Dashboard (konsol operasional), REST API (`/missions`, `/workflow`, `/approval`, `/execution-preview`, `/audit`, `/artifact`, `/policy`)
- **Desain**: preview-first, approval mandatory sebelum execute, execution cancellable, rollback metadata, full audit, network hanya di provider layer, kredensial hanya dari environment (tidak pernah hardcode), DTO immutable & deterministic.

---

## SAM 1.0 — Rilis Publik Pertama (2026-08-07)

✅ **SAM 1.0 (1.0.0) — Foundation stabil pertama SAM, resmi dirilis.**

- Nama publik: **SAM 1.0**
- Versi teknis: **1.0.0**
- 9 dokumen foundation di `docs/foundation/` — diselaraskan ke `1.0.0` Foundational/Accepted
- `pyproject.toml` = `1.0.0`; `sam.__version__ = "1.0.0"`
- Kemampuan: Conversation, Dashboard, CLI, REST API, LLM (5 provider) — semua aktif & teruji
- Rilis pertama dan satu-satunya; tidak ada riwayat rilis sebelumnya

---

## Roadmap Produk (post-1.0)

> Rencana pengembangan setelah **SAM 1.0** dirilis. Prioritas beralih dari integrasi
> ke **pematangan produk, skalabilitas, dan ekosistem**.

```
SAM 1.0 (rilis, 2026-08-07) ✅
       ↓
Sam 1.1 — Penyempurnaan stabilitas & observabilitas produksi
       ↓
SAM 2.0 — Skalabilitas multi-node / cluster production
       ↓
Ekosistem — Marketplace, Templates, Examples (opsional)
```

| Rencana | Isi |
|---------|-----|
| **SAM 1.1** | Stabilisasi produksi, observability lanjutan, perbaikan operational issues, tuning performa |
| **SAM 2.0** | Skalabilitas cluster, distributed runtime, federation |
| **Ekosistem** | Marketplace, examples, templates, dokumentasi pelengkap |

### Simulation & Preview — bagian dari Program C (Execution Evolution)

Simulation merupakan **penyempurnaan Program C (Real Execution Runtime)**:
menambahkan lapisan **Simulation** di antara Policy dan Approval sehingga **approval
gate** milik Program C menjadi **Decision + Evidence** (bukan "buta").
Pipeline konseptual: Mission → Workflow → Policy → **Simulation** → Approval
→ Execution → Verification → Audit. Simulation menyediakan evidence (cost, time,
risk, expected provider, rollback feasibility, side effects, external calls).

Daftar kerja Simulation (bagian dari lingkup Program C):

- **C.1 Simulation Capability** — SimulationEvidence deterministik dari metadata governance; SimulationEngine tanpa mock; mode simulation di ExecutionRequest.
- **C.2 Preview & Dry Run** — external_calls = 0; wiring ke Approval (evidence opsional, kontrak ApprovalGate tidak berubah).
- **C.3 Validation** — perbandingan hasil simulasi vs hasil nyata; program terpisah berikutnya.

> **Kebijakan:** jangan menambah runtime/lapisan arsitektur baru tanpa kebutuhan nyata.
> Pertumbuhan kompleksitas harus terkendali; energi diarahkan ke integrasi, stabilitas, dan nilai produk.

---

## Urutan Stack (konseptual)

Membangun satu lapisan demi satu lapisan (dari bawah ke atas):

```
Guardian
  ↓
Decision
  ↓
Approval
  ↓
Operational Brain
  ↓
Activation
  ↓
Execution
  ↓
Runtime Kernel
  ↓
Connector
  ↓
Orchestrator
  ↓
Mission
  ↓
Provider
  ↓
Agent
```

---

## Kebijakan Sinkronisasi Dokumen (permanen)

| Dokumen | Tanggung jawab |
|---------|----------------|
| **ROADMAP.md** | **Satu-satunya** sumber kebenaran fase proyek & rencana |
| **README.md** | Hanya versi aktif, fase aktif, status proyek, + tautan ke ROADMAP.md |
| **CHANGELOG.md** | Hanya histori perubahan rilis (SAM 1.0 = rilis pertama) |
| **docs/releases/manifest.md** | Hanya metadata rilis |

**Aturan:** setiap perubahan fase hanya memperbarui bagian terkait di dokumen dan
merujuk ke ROADMAP induk. Dokumen lain cukup memperbarui versi aktif & status.

---

## Post SAM 1.0 — Baseline CI Expansion (2026-08-08)

✅ **SAM 1.0.1 — Baseline CI diperluas.**

- Baseline CI: 8 folder (unit + 7 runtime suites), 3,808 tests passed, 1 skipped.
- Runtime Operational dalam baseline: Knowledge · Memory · Policy · Workflow · Artifact · Audit · Mission.
- Execution Runtime: 209/211 passed (2 pre-existing), menunggu perbaikan sebelum masuk baseline.
- Lihat `CHANGELOG.md` untuk detail per Sprint/Program.

SAM 1.x
Foundation

        ↓

SAM 2.x
Governance Platform

        ↓

SAM 3.x
Production Governance Platform

        ↓

SAM 4.x
Federated Governance Network

        ↓

SAM 5.x
Universal Governance Layer
