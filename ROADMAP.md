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

> **Arsitektur SAM kini berada di ~85–90% perjalanan.** Fase I–XX (fondasi runtime, 17 runtime inti + Workflow) SELESAI. Sisa pembangunan dibagi menjadi **3 Tahap**: lengkapi fondasi (XXI–XXIV), integrasi nyata, lalu produk.

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
| XXIV | Simulation Runtime (opsional) | 📋 PLANNED |

> **Total: 24 phase (XXIV opsional).** Setelah fondasi arsitektur lengkap, fokus bergeser ke Tahap 2 (integrasi nyata) dan Tahap 3 (produk).

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

Arsitektur SAM tidak akan terus menambah runtime tanpa batas. Setelah fondasi ini lengkap, prioritas bergeser dari membangun lapisan baru ke **menghubungkan semua lapisan menjadi sistem yang benar-benar dapat digunakan**.

### Tahap 1 — Lengkapi Fondasi (XXI–XXIV, 3–4 phase)

Hanya runtime mandiri yang masih layak dibangun:

| Phase | Runtime | Tujuan |
|-------|---------|--------|
| XXI | **Policy Runtime** | Menyatukan seluruh policy lintas subsystem (saat ini tersebar) |
| XXII | **Audit Runtime** | Immutable audit trail, provenance, traceability end-to-end |
| XXIII | **Artifact Runtime** | Output SAM menjadi artifact resmi: manifest, versioning, signing |
| XXIV (opsional) | **Simulation Runtime** | Simulasi pipeline tanpa menyentuh runtime lain |

> **Maksimal 3–4 phase.** Setelah Phase XX, perkiraan arsitektur berada di ~85–90% perjalanan.

### Tahap 2 — Integrasi Nyata (tanpa runtime baru)

Fokus beralih ke menghubungkan runtime yang ada dengan kemampuan nyata:

- **OpenClaw** · **Docker** · **Filesystem** · **SQLite** · **GitHub**
- **LLM Connector** · **Tool Registry** · **CLI** · **Desktop UI**

> Inilah yang membuat SAM benar-benar berguna — Runtime yang telah dibangun kini benar-benar berjalan.

### Tahap 3 — SAM Menjadi Produk

Hampir tanpa penambahan arsitektur besar:

- **Dashboard operasional** · **Mission Designer** · **Workflow Designer**
- **Approval Console** · **Monitoring Console**
- **CLI** · **Desktop Application** · **API Server**

> Setelah fondasi + integrasi, SAM mencapai **Architecture Complete** — menjadi produk yang memberikan nilai nyata bagi pengguna.

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

Dengan selesainya Phase XXIII, SAM memiliki **rantai runtime deterministik yang lengkap** — dari Mission sampai representasi policy, audit, artifact, workflow & kognitif siap dikonsumsi reasoning engine masa depan.

Setelah fondasi arsitektur lengkap (Phase XXIV, lihat bagian *3 Tahap Pembangunan*):
- **Tidak lagi menambah runtime / lapisan arsitektur baru.**
- Pengembangan bergeser dari *menambah subsystem* menjadi *menghubungkan dan memperluas* apa yang sudah ada — melalui Tahap 2 (integrasi nyata: OpenClaw, Docker, Filesystem, SQLite, GitHub, LLM Connector, Tool Registry, CLI, Desktop UI) dan Tahap 3 (menjadi produk: dashboard, designer, console, API).
- SAM mencapai **Architecture Complete** dan mulai memberikan **nilai nyata bagi pengguna**.

Tujuan: menjaga arsitektur **stabil, dapat diprediksi**, dan menghindari **pertumbuhan kompleksitas yang tidak terkendali**.
