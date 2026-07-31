# SAM Roadmap

> **Sumber kebenaran tunggal (single source of truth) untuk seluruh fase SAM.**
> Visi: **Deterministic Operational Intelligence Platform** — observasi, pemahaman, perencanaan, koordinasi, penyiapan, dan pengawasan operasi lintas sistem secara aman, dapat diaudit, provider-agnostic, dan dapat dipertanggungjawabkan.

---

## Visi Akhir (End-state)

SAM adalah **Deterministic Operational Intelligence Platform** yang mampu:

- **Mengobservasi** — melihat kondisi sistem
- **Memahami** — memetakan konteks operasional
- **Merencanakan** — menyusun urutan operasi
- **Mengoordinasikan** — mengatur antar-runtime
- **Menyiapkan** — membangun request/aksi
- **Mengawasi** — memantau hingga selesai

Karakteristik kunci:

| Bukan | Melainkan |
|-------|-----------|
| Chatbot | Operational Intelligence Platform |
| LLM | Deterministic engine |
| Autonomous AI | Dapat diaudit & dapat dipertanggungjawabkan |
| AGI | Provider-agnostic (AI hanyalah salah satu provider via Connector Runtime) |

> **Identitas SAM tetap utuh** walaupun provider AI diganti atau dilepas.

---

## Ringkasan Fase (I–XXIV)

> **✅ ARSITEKTUR SAM KOMPLIT — v23.0.0 = Architecture Complete.**
> Fase I–XXIII (fondasi runtime deterministik, 23 phase, ~200+ sprint) SELESAI. XXIV opsional. **Mulai titik ini, roadmap bergeser dari Architecture Development ke Product Integration & Operationalization (Tahap 2 & 3), tanpa menambah runtime baru.**
> Keputusan ini dari Aster (2026-08-01): nilai terbesar berikutnya bukan dari runtime baru, melainkan membuat semua runtime yang ada bekerja bersama untuk pekerjaan nyata.

| Phase | Nama | Status |
|-------|------|--------|
| I | Foundation | ✅ DONE |
| II | Core Runtime | ✅ DONE |
| III | Runtime Expansion | ✅ DONE |
| IV | Guardian Runtime | ✅ DONE |
| V | Decision Runtime | ✅ DONE |
| VI | Approval Runtime | ✅ DONE |
| VII | Operational Brain | ✅ DONE |
| VIII | Activation Runtime | ✅ DONE |
| IX | Execution Runtime | ✅ DONE |
| X | Runtime Kernel | ✅ DONE |
| XI | Universal Connector Runtime | ✅ DONE |
| XII | Orchestration Runtime | ✅ DONE |
| XIII | Mission Runtime | ✅ DONE |
| XIV | Provider Runtime | ✅ DONE |
| XV | Agent Runtime | ✅ DONE |
| XVI | Skill Runtime | ✅ DONE |
| XVII | Memory Runtime | ✅ DONE |
| XVIII | Knowledge Runtime | ✅ DONE |
| XIX | Cognitive Runtime | ✅ DONE |
| XX | Workflow Runtime | ✅ DONE |
| XXI | Policy Runtime | ✅ DONE |
| XXII | Audit Runtime | ✅ DONE |
| XXIII | Artifact Runtime | ✅ DONE |
| XXIV | Simulation Runtime (opsional) | 📋 PLANNED — TIDAK DIPRIORITASKAN |

> **Total: 24 phase (XXIV opsional).** Fondasi arsitektur LENGKAP di v23.0.0. Fokus kini beralih ke **Product Integration & Operationalization** (Tahap 2: Program A–K; Tahap 3: Product Release) — lihat bagian *Roadmap Produk (pasca v23.0.0)* di bawah.

---

## Fase Detail (I–XXIV)

### Fase Selesai (I-XXIII) — membangun seluruh "mesin"

| Phase | Sprint | Versi | Komponen Inti |
|-------|--------|-------|---------------|
| I | 1-7 | v0.0.1 | Foundation: agent state, telemetry, contracts |
| II | 8-17 | v2.0.0 | Core Runtime: operational brain, plan, archive, monitor |
| III | 18-29 | v3.0.0 | Runtime Expansion: guardian intelligence, policies, event engine |
| IV | 30-42 | v4.0.0 | Guardian Runtime: dispatcher, reasoning, learning, dashboard |
| V | 43-58 | v5.0.0-v6.0.0 | Decision Runtime: guardian live, situation intelligence |
| VI | 59-75 | v6.0.0-v7.0.0 | Approval Runtime: certification, finalization, lifecycle |
| VII | 76-81 | v7.0.0-v8.0.0 | Operational Brain Full Integration |
| VIII | 82-87 | v8.0.0-v8.5.0 | Activation Runtime (pipeline lengkap) |
| IX | 88-99 | v9.0.0-v9.11.0 | Execution Runtime (12 sprints, ~1,600 tests) |
| X | 100-111 | v10.0.0 | Runtime Kernel (12 sprints, 1,719 tests, 69 files) |
| XI | 112-122 | v11.0.0 | Universal Connector Runtime (11 sprints, 220 tests, 77 files) |
| XII | 123-133 | v12.0.0 | Orchestration Runtime (11 sprints, 172 tests, 78 files) |
| XIII | 134-143 | v13.0.0 | Mission Runtime (10 sprints, 145 tests, 70 files) |
| XIV | 144-155 | v14.0.0 | Provider Runtime (12 sprints, 164 tests, 10 folders) |
| XV | 156-163 | v15.0.0 | Agent Runtime (8 sprints, 211 tests, 11 folders) |
| XVI | 164-171 | v16.0.0 | Skill Runtime (8 sprints, 192 tests, 67 files) |
| XVII | 172-179 | v17.0.0 | Memory Runtime (8 sprints, 209 tests, 67 files) |
| XVIII | 180-187 | v18.0.0 | Knowledge Runtime (8 sprints, 207 tests, 67 files) |
| XIX | 188-195 | v19.0.0 | Cognitive Runtime (8 sprints, 201 tests, 8 folders) |
| XX | 196-203 | v20.0.0 | Workflow Runtime (8 sprints, 210 tests, 66 files) |
| XXI | 204-211 | v21.0.0 | Policy Runtime (8 sprints, 208 tests, 66 files) |
| XXII | 212-219 | v22.0.0 | Audit Runtime (8 sprints, 173 tests, 66 files) |
| XXIII | 220-227 | v23.0.0 | Artifact Runtime (8 sprints, 135 tests, 66 files) |

### Fase Terencana (XVI–XXIV)

| Phase | Nama | Deskripsi |
|-------|------|-----------|
| XVI | Skill Runtime | Skills preview-only: deskripsi, definisi, builder, runtime, catalog, monitoring, sertifikasi + integrasi read-only (Mission→Agent→Skill→Orchestrator→Connector→Provider) |
| XVII | Memory Runtime | Memori preview-only: deskripsi, model, builder, runtime, catalog, monitoring, sertifikasi + integrasi read-only (Mission→Agent→Skill→Memory→Orchestrator→Connector→Provider) |
| XVIII | Knowledge Runtime | Pengetahuan deterministik preview-only: foundation, model, builder, runtime, catalog, monitoring, sertifikasi + integrasi read-only (Mission→Agent→Skill→Memory→Knowledge→Orchestrator→Connector→Provider). No inference |
| XIX | Cognitive Runtime | Konsolidasi output seluruh runtime (Mission/Agent/Skill/Memory/Knowledge) menjadi Cognitive Context deterministik siap dikonsumsi reasoning engine. Bukan LLM/AI, tanpa inferensi |
| XX | Workflow Runtime | Penyusun workflow deterministik di atas Mission/Agent/Skill dan sebelum Memory/Knowledge/Cognitive: urutan langkah + dependensi + batasan. No scheduling, no reasoning, no runtime select |
| XXI | Policy Runtime | Menyatukan seluruh policy lintas subsystem (saat ini masih tersebar): deskripsi, model policy, builder, katalog, monitoring, sertifikasi + integrasi read-only. Tidak evaluasi/keputusan |
| XXII | Audit Runtime | Immutable audit trail: provenance, traceability end-to-end, integritas log. Semua operasi terekam deterministik, tanpa bisa diubah |
| XXIII | Artifact Runtime | Semua output SAM menjadi artifact resmi: manifest, versioning, signing. Representasi immutable artifact + siklus hidupnya |
| XXIV | Simulation Runtime (opsional) | Menjalankan simulasi pipeline tanpa menyentuh runtime lain - dry-run end-to-end dalam mode preview |

---

## 3 Tahap Pembangunan (rencana Aster)

Arsitektur SAM tidak akan terus menambah runtime tanpa batas. Setelah fondasi lengkap (v23.0.0 = **Architecture Complete**), prioritas bergeser dari membangun lapisan baru ke **Product Integration & Operationalization**.

### Tahap 1 — Lengkapi Fondasi (XXI–XXIII) ✅ SELESAI

| Phase | Runtime | Status |
|-------|---------|--------|
| XXI | **Policy Runtime** | ✅ v21.0.0 |
| XXII | **Audit Runtime** | ✅ v22.0.0 |
| XXIII | **Artifact Runtime** | ✅ v23.0.0 |
| XXIV (opsional) | **Simulation Runtime** | 📋 tidak diprioritaskan |

> **Tahap 1 SELESAI di v23.0.0 (Architecture Complete).** Phase XXIV (Simulation) sengaja tidak diprioritaskan — seluruh runtime inti sudah siap dikonsumsi.

### Tahap 2 — Product Integration (Program A–K)

Fokus: membuat runtime yang sudah ada **benar-benar bekerja bersama** untuk pekerjaan nyata. Menghubungkan Execution → Provider → Connector → provider nyata. Prinsip tetap: **approval dulu → preview dulu → baru execute**.

#### Program A — External Connectors

SAM benar-benar dapat berbicara dengan dunia luar. Implementasi bertahap: **OpenAI · Anthropic · Google Gemini · Ollama · OpenClaw · GitHub · Filesystem · SQLite · Docker · Terminal · REST API · MCP**. Semua memanfaatkan **Connector Runtime + Provider Runtime** yang sudah dibangun.

#### Program B — Model Runtime Integration ❌ DONE (v25.0.0)

Runtime model generik: **Model Foundation (239) · Generic Interface (240) · Chat (241) · Embedding (242) ·
Reasoning (243) · Vision (244) · Tool Calling (245) · Model Runtime+pipeline (246) · Provider Mapping (247) ·
Certification 7-dimensi (248) · Integration + pipeline akhir (249)**.

Pipeline: Descriptor → Request → Validation → Preview → Report. All immutable, preview-only, no-network.
Pipeline akhir: Mission→Agent→Workflow→Memory→Knowledge→Cognitive→Policy→Audit→Artifact→Connector→Provider→Model→Execution Preview.

> Catatan: ROADMAP terdahulu menamai Program B sebagai **Execution Integration**. Nama resmi release ini,
> sesuai keputusan pelaksanaan, adalah **Model Runtime Integration** (v25.0.0). Eksekusi provider-nyata
> (approval→preview→execute) telah dilaksanakan sebagai **Real Execution Runtime** (v26.0.0) di bawah ini,
> dengan approval eksplisit + API key dari environment (bukan hardcode).

#### Program C — Real Execution Runtime

> Dilaksanakan: **SELESAI (v26.0.0)**. Mengubah SAM dari preview-only menjadi eksekusi nyata lewat provider yang ada. **11 sprint (250–260)**:
> Execution Foundation (250) · Execution Request (251) · Approval Gate (252) · Provider Dispatcher (253) ·
> Execution Engine (254) · Rollback Runtime (255) · Monitoring (256) · Safety Runtime (257) ·
> Certification 7-dimensi (258) · Integration + pipeline akhir (259) · Real Provider Activation (260).
> Pipeline akhir: Mission→Workflow→Policy→Memory→Knowledge→Cognitive→Orchestrator→Connector→Provider→
> Model Runtime→Approval→Execution Runtime→Artifact. Preview-first; approval MANDATORY sebelum execute;
> execution cancellable; rollback metadata; full audit; network HANYA di provider layer; kredensial env.

#### Program D — Runtime Services & Deployment

> Dilaksanakan: **SELESAI (v27.0.0)**. Menjadikan SAM sebagai layanan runtime
> nyata dengan lifecycle & kesiapan produksi. **11 sprint (261–271)**:
> Runtime Service Foundation (261) · Configuration Runtime (262) · Secrets Runtime (263) ·
> Runtime Lifecycle (264) · Dependency Injection (265) · Plugin Runtime (266) ·
> Runtime API (267) · Server Runtime (268) · Monitoring (269) · Certification 7-dimensi (270) ·
> Integration + pipeline akhir (271).
> Pipeline akhir: Mission→Workflow→Policy→Agent→Skill→Memory→Knowledge→Cognitive→
> Orchestrator→Connector→Provider→Execution Runtime→**Runtime Service**→External Provider.
> Entry point resmi: `sam.runtime_service`. Kredensial HANYA dari environment,
> tidak pernah hardcode. Semua DTO immutable, sync/deterministic, tanpa network di layer aplikasi.

#### Program E — Unified Intelligence Runtime

> Dilaksanakan: **SELESAI (v28.0.0)**. Menyatukan representasi seluruh runtime SAM
> menjadi graph + context + sertifikasi yang deterministik. **8 sprint (261–268)**:
> Foundation (261) · Runtime Registry (262) · Pipeline Graph (263) ·
> Context Assembly (264) · Intelligence Runtime (265) · Monitoring (266) ·
> Certification 7-dimensi (267) · Integration + pipeline akhir (268).
> Pipeline internal: Registry→Graph→Context→Validation→Assembly→Report.
> Pipeline akhir: Mission→Agent→Workflow→Skill→Memory→Knowledge→Cognitive→Policy→
> Audit→Artifact→**Intelligence Runtime**→Orchestrator→Connector→Provider→
> Model Runtime→Execution Runtime→Runtime Service. Entry point: `sam.intelligence_runtime`.
> 0 async/thread/socket/network, DTO frozen, preview-only, external_calls==0,
> tanpa inference/LLM, bridge read-only, tidak mengubah subsystem lama.

#### Program F — Desktop Application

> Catatan: Semula direncanakan sebagai Program E (Desktop Application). Sesuai
> keputusan pelaksanaan, Program E diisi Unified Intelligence Runtime (v28.0.0);
> Desktop Application digeser menjadi **Program F**.

Mengaktifkan UI yang sudah lama ada. Prioritas: **Mission Designer · Workflow Designer · Policy Viewer · Audit Explorer · Artifact Explorer · Runtime Explorer · Connector Explorer · Provider Explorer · Execution Preview**. Semua memakai subsystem yang sudah tersedia.

#### Program G — Conversation

Conversation Runtime menjadi benar-benar berguna: buat mission, tampilkan workflow, cari policy, lihat audit, preview artifact, jalankan approval, preview execution, ringkas knowledge, cari memory. **Bukan lagi sekadar bridge.**

#### Program H — Dashboard

Dashboard menjadi konsol operasional: **Mission · Workflow · Execution · Approval · Audit · Connector · Provider · Runtime · Health · Telemetry**.

#### Program I — CLI

Perintah seperti: `sam mission` · `sam workflow` · `sam policy` · `sam audit` · `sam artifact` · `sam connector` · `sam provider` · `sam execution` · `sam preview` · `sam dashboard`.

#### Program J — REST API

REST API untuk semua runtime, mis. `POST /missions` · `POST /workflow` · `POST /approval` · `POST /execution-preview` · `GET /audit` · `GET /artifact` · `GET /policy`.

#### Program K — LLM Integration

SAM memperoleh kemampuan AI nyata. Connector: **OpenAI · Anthropic · Gemini · Ollama · OpenClaw**. Tetap melalui **Connector Runtime → Provider Runtime → Agent Runtime** — bukan langsung memanggil provider.

### Tahap 3 — Product Release

Sesudah integrasi selesai: **SAM Desktop · SAM CLI · SAM Server · SAM SDK · SAM Python Package · SAM Documentation · SAM Examples · SAM Templates · SAM Tutorial · SAM Marketplace (opsional)**.

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

> Fase I–XV tidak melakukan realignment — urutan yang berjalan memang membangun stack penuh. Yang diperbarui hanya dokumentasi agar mengikuti implementasi aktual.

---

## Kebijakan Sinkronisasi Dokumen (permanen)

| Dokumen | Tanggung jawab |
|---------|----------------|
| **ROADMAP.md** | **Satu-satunya** sumber kebenaran fase proyek |
| **README.md** | Hanya versi aktif, fase aktif, status proyek, + tautan ke ROADMAP.md |
| **CHANGELOG.md** | Hanya histori perubahan rilis (tidak lagi memuat tabel fase) |
| **docs/releases/manifest.md** | Hanya metadata rilis |
| **docs/releases/version-history.md** | Hanya riwayat versi |

**Aturan per fase baru:**
Setiap fase baru hanya mengubah satu bagian pada ROADMAP.md:
- Status fase berjalan → **DONE**
- Status fase berikutnya → **IN PROGRESS**

Dokumen lain cukup memperbarui versi dan merujuk ke roadmap induk.

---

## Catatan Arsitektur

Dengan selesainya 1–XXIII, SAM mencapai **Architecture Complete (v23.0.0)** — **rantai runtime deterministik yang lengkap** dari Mission sampai representasi policy, audit, artifact, workflow & kognitif siap dikonsumsi reasoning engine masa depan.

**Arsitektur DIANGGAP SELESAI.** Keputusan dari Aster (2026-08-01):
- **Tidak lagi menambah runtime / lapisan arsitektur baru.**
- Roadmap bergeser dari *Architecture Development* ke *Product Integration & Operationalization*.
- Nilai terbesar berikutnya bukan dari runtime baru, melainkan membuat semua runtime yang ada bekerja bersama untuk menyelesaikan pekerjaan nyata.

Tujuan: menjaga arsitektur **stabil, dapat diprediksi**, menghindari **pertumbuhan kompleksitas yang tidak terkendali**, dan mengalihkan energi ke **integrasi & produk**.

---

## Roadmap Produk (pasca v23.0.0)

> Keputusan Aster (2026-08-01): **SAM Architecture v23.0.0 = Architecture Complete**.
> Roadmap bergeser dari Architecture Development → **Product Integration & Operationalization**.

```
✓ Phase I–XXIII (v23.0.0)
   Architecture Complete
        ↓
Program A — External Connectors
        ↓
Program B — Model Runtime Integration (v25.0.0 ✅)
        ↓
Program C — Real Execution Runtime (v26.0.0 ✅)
        ↓
Program D — Runtime Services & Deployment (v27.0.0 ✅)
        ↓
Program E — Unified Intelligence Runtime (v28.0.0 ✅)
        ↓
Program F — Desktop Application
        ↓
Program G — Conversation
        ↓
Program H — Dashboard
        ↓
Program I — CLI
        ↓
Program J — REST API
        ↓
Program K — LLM Integration
        ↓
SAM Operational Product
```

**Catatan status:** Program A (v24.0.0 ✅), B (v25.0.0 ✅), C (v26.0.0 ✅), D (v27.0.0 ✅), E (v28.0.0 ✅) **sudah dieksekusi & dirilis**. Program F–K & Tahap 3 masih **perencanaan**. Lihat *3 Tahap Pembangunan* di atas untuk detail per Program.
