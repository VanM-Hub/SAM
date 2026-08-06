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

> ✅ **SAM 1.0 (versi teknis 1.0.0, 2026-08-07) — RILIS PUBLIK PERTAMA.**

Seluruh perjalanan pengembangan (Foundation 0.01 → 0.30, 279 sprint + Program A–K) telah
mencapai titik rilis stabil: **SAM 1.0 Foundation**. Ini adalah **rilis pertama dan satu-satunya**
SAM. Tidak ada rilis sebelumnya — semua versi internal lama hanyalah tahap pengembangan
fondasi (pre-1.0), bukan rilis publik.

Roadmap di bawah menjabarkan fase-fase fondasi yang telah dilalui (sebagai konteks pengembangan),
diikuti rencana ke depan (post-1.0).

---

## Fase Fondasi (sudah dilalui — konteks pengembangan)

> Seluruh fase ini adalah **tahap pengembangan fondasi (pre-1.0)**, bukan rilis publik.
> Penomoran **0.X** menunjukkan tahap fondasi; puncaknya adalah **0.30**, yang kemudian
> dirilis resmi sebagai **SAM 1.0**. Lihat `SPRINT_TRACKER.md` untuk kronologi rinci.

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
| C | Real Execution Runtime (execution engine, approval gate, rollback, monitoring, safety, provider activation) | 0.26 |
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
