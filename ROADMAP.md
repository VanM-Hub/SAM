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

> **Total: 24 phase (XXIV opsional).** Fondasi arsitektur LENGKAP di v23.0.0. Fokus kini beralih ke **Product Integration & Operationalization** (Tahap 2: Program A–H; Tahap 3: Product Release) — lihat bagian *Roadmap Produk (pasca v23.0.0)* di bawah.

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

### Tahap 2 — Product Integration (Program A–H)

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
> (approval→preview→execute) tetap menunggu instruksi lanjutan dan approval eksplisit + API key.

#### Program C — Desktop Application

Mengaktifkan UI yang sudah lama ada. Prioritas: **Mission Designer · Workflow Designer · Policy Viewer · Audit Explorer · Artifact Explorer · Runtime Explorer · Connector Explorer · Provider Explorer · Execution Preview**. Semua memakai subsystem yang sudah tersedia.

#### Program D — Conversation

Conversation Runtime menjadi benar-benar berguna: buat mission, tampilkan workflow, cari policy, lihat audit, preview artifact, jalankan approval, preview execution, ringkas knowledge, cari memory. **Bukan lagi sekadar bridge.**

#### Program E — Dashboard

Dashboard menjadi konsol operasional: **Mission · Workflow · Execution · Approval · Audit · Connector · Provider · Runtime · Health · Telemetry**.

#### Program F — CLI

Perintah seperti: `sam mission` · `sam workflow` · `sam policy` · `sam audit` · `sam artifact` · `sam connector` · `sam provider` · `sam execution` · `sam preview` · `sam dashboard`.

#### Program G — REST API

REST API untuk semua runtime, mis. `POST /missions` · `POST /workflow` · `POST /approval` · `POST /execution-preview` · `GET /audit` · `GET /artifact` · `GET /policy`.

#### Program H — LLM Integration

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
Program B — Execution Integration
        ↓
Program C — Desktop Application
        ↓
Program D — Conversation Experience
        ↓
Program E — Operational Dashboard
        ↓
Program F — CLI
        ↓
Program G — REST API
        ↓
Program H — LLM Integration
        ↓
SAM v24+ — Operational Product
```

**Catatan status:** Semua Program (A–H) & Tahap 3 adalah **perencanaan** — belum dieksekusi. Eksekusi menunggu instruksi. Lihat *3 Tahap Pembangunan* di atas untuk detail per Program.
