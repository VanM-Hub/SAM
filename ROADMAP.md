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

## Ringkasan Fase (I–XX)

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
| XXI | Operational Intelligence Console | 📋 PLANNED |
| XXII | Execution Integration | 📋 PLANNED |
| XXIII | Platform Certification | 📋 PLANNED |

> **Total: 23 phase.** Fase XXIII adalah end-state. Sesudahnya bukan roadmap lagi, melainkan maintenance.

---

## Fase Detail (I–XX)

### Fase Selesai (I–XX) — membangun seluruh "mesin"

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

### Fase Terencana (XVI–XXII)

| Phase | Nama | Deskripsi |
|-------|------|-----------|
| XVI | Skill Runtime | Skills preview-only: deskripsi, definisi, builder, runtime, catalog, monitoring, sertifikasi + integrasi read-only (Mission→Agent→Skill→Orchestrator→Connector→Provider) |
| XVII | Memory Runtime | Memori preview-only: deskripsi, model, builder, runtime, catalog, monitoring, sertifikasi + integrasi read-only (Mission→Agent→Skill→Memory→Orchestrator→Connector→Provider) |
| XVIII | Knowledge Runtime | Pengetahuan deterministik preview-only: foundation, model, builder, runtime, catalog, monitoring, sertifikasi + integrasi read-only (Mission→Agent→Skill→Memory→Knowledge→Orchestrator→Connector→Provider). No inference |
| XIX | Cognitive Runtime | Konsolidasi output seluruh runtime (Mission/Agent/Skill/Memory/Knowledge) menjadi Cognitive Context deterministik siap dikonsumsi reasoning engine. Bukan LLM/AI, tanpa inferensi |
| XX | Workflow Runtime | Penyusun workflow deterministik di atas Mission/Agent/Skill dan sebelum Memory/Knowledge/Cognitive: urutan langkah + dependensi + batasan. No scheduling, no reasoning, no runtime select |
| XXI | Operational Intelligence Console | UI besar: visualisasi seluruh runtime (Mission, Approval, Execution, Health, Timeline, Pipeline, Reasoning, Audit) — berbeda dari dashboard kecil saat ini |
| XXII | Execution Integration | Execution Runtime mulai benar-benar menjalankan provider (Real Provider Runtime: Filesystem, SQLite, Docker, Shell, OpenClaw aktif). Tetap manual approval. Belum autonomous |
| XXIII | Platform Certification | Fase stabilisasi, bukan fitur: architecture freeze, ADR final, performance benchmark, scalability, documentation, migration guide, SDK, API stability, plugin specification |

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

Dengan selesainya Phase XX, SAM memiliki **rantai runtime deterministik yang lengkap** — dari Mission sampai representasi workflow & kognitif siap dikonsumsi reasoning engine masa depan.

Setelah Phase XXIII (Platform Certification) selesai:
- **Tidak lagi menambah runtime baru.**
- Pengembangan bergeser dari *menambah subsystem* menjadi *memperluas kemampuan subsystem* yang sudah ada — melalui provider, plugin, dan integrasi.

Tujuan: menjaga arsitektur **stabil, dapat diprediksi**, dan menghindari **pertumbuhan kompleksitas yang tidak terkendali**.
