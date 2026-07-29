# PROJECT SAM — Architecture Context Export (v4.46.0)

Dokumen ini dibuat sebagai Single Source of Truth arsitektur untuk Project SAM pada versi v4.46.0. Tujuannya agar AI lain (atau sesi baru ChatGPT) dapat memahami desain, filosofi, komponen, alur runtime, batasan, dan aturan-aturan penting tanpa harus membaca seluruh repository atau riwayat percakapan.

Dokumen ini sistematis, teknis, dan fokus pada relasi antar sistem, filosofi desain, dan alasan arsitektural. Tidak membahas implementasi fungsi per-fungsi secara rinci.

> **Sumber kebenaran:** Repository adalah satu-satunya sumber kebenaran. Jika ditemukan perbedaan antara dokumen ini dan source code, source code adalah kebenaran utama.

---

## Daftar Isi

1. Executive Summary
2. Architecture Overview
3. Runtime Pipeline
4. Module Inventory
5. Capability Matrix
6. Sprint Timeline
7. Documentation Audit
8. Technical Debt
9. Updated Roadmap
10. Overall Assessment
11. Project Identity
12. Design Philosophy
13. High Level Architecture
14. Folder Structure
15. Conversation System
16. Guardian Runtime
17. Operational Brain
18. Reasoning Runtime
19. Governance
20. Launcher
21. Presentation Layer
22. Data Flow
23. Dependency Rules
24. Sprint History
25. Current Capability
26. Current Limitations
27. Public Contracts
28. Architecture Constraints
29. Current Project Status
30. AI Handover — "What another AI must understand before modifying SAM"
31. Architecture Contract (Tidak Berubah)

---

## 1. Executive Summary

SAM (The Autonomous Guardian Operating System for AI) adalah platform operasional yang menyediakan pipeline observasi → reasoning → decision → guardian → governance → execution secara deterministic, audit-traced, dan approval-first.

**Status v4.46.0:**
- 42 sprint selesai
- 10 sprint beruntun dalam sesi ini (v4.37.0 → v4.46.0)
- Tag: v4.46.0 | Commit: `fb55c7f`
- ~650 file Python, ~4.000+ test
- Semua pipeline inti selesai secara arsitektur
- Belum ada eksekusi nyata — semua masih preview/planning

---

## 2. Architecture Overview

SAM adalah **Operational Intelligence Platform**, bukan chatbot, bukan AI model, bukan agent yang berjalan sendiri. SAM adalah runtime operasional yang:

- mengamati keadaan sistem,
- membangun evidence,
- melakukan reasoning,
- menghasilkan rekomendasi,
- mengatur governance,
- menjaga approval,
- mengorkestrasi execution,
- menyediakan explainability,
- menyediakan audit,
- menjaga seluruh keputusan agar dapat diverifikasi.

Arsitektur 7 layer + foundation layer tambahan:

```
┌──────────────────────────────────────────────────────────┐
│                    CLI / Desktop / Console                 │
├──────────────────────────────────────────────────────────┤
│                      Conversation Layer                   │
├──────────────────────────────────────────────────────────┤
│          Brain / Reasoning / Decision / Guardian          │
├──────────────────────────────────────────────────────────┤
│              Governance / Learning / Planning             │
├──────────────────────────────────────────────────────────┤
│       Execution / Dispatch / Adapter / Provider           │
├──────────────────────────────────────────────────────────┤
│        External Integration / Plugin / SDK                │
├──────────────────────────────────────────────────────────┤
│                   Runtime Kernel / Contracts               │
└──────────────────────────────────────────────────────────┘
```

---

## 3. Runtime Pipeline

Pipeline aktual berdasarkan source code:

```
Observation
    ↓
Reasoning Runtime
    ↓
Decision Runtime
    ↓
Guardian Runtime
    ↓
Governance Runtime
    ↓
Learning Runtime
    ↓
Execution Planning
    ↓
Dispatch Runtime
    ↓
Connector Runtime
    ↓
Execution Engine (Package → Validator → Rollback → Scheduler)
    ↓
Adapter Layer (Envelope → Validation → Preview)
    ↓
Provider Runtime (Router → Mock Provider → Preview)
    ↓
External Integration
    ↓
Plugin Ecosystem
    ↓
SDK Foundation
    ↓
Dashboard
    ↓
Conversation
    ↓
Host
```

Setiap tahap menghasilkan DTO immutable yang dapat diaudit.

---

## 4. Module Inventory

| Modul | Lokasi | Tanggung Jawab |
|---|---|---|
| **Launcher** | `src/sam/launcher/` | Startup pipeline, bootstrap, diagnostics, host management |
| **Conversation** | `src/sam/operations/conversation*` | Single entry point, session management, context |
| **Brain** | `src/sam/operations/brain/` | Observation, reasoning, orchestration, learning, pattern mining |
| **Guardian** | `src/sam/guardian/` | Policy enforcement, gates, execution readiness |
| **Governance** | `src/sam/operations/brain/guardian/` | Policy engine, risk, approval, audit, explanation |
| **Learning** | `src/sam/operations/brain/learning/` | Knowledge base, experience repo, pattern evolution, optimizer |
| **Execution** | `src/sam/execution/` | Planning, dispatch, connector, adapter, provider, mock |
| **Dispatch** | `src/sam/execution/dispatch/` | Priority queue, audit, validator |
| **Connector** | `src/sam/execution/connectors/` | Connector runtime, capability, policy, health, mock connectors |
| **Engine** | `src/sam/execution/engine/` | Task builder, validator, rollback planner, scheduler |
| **Adapter** | `src/sam/execution/adapters/` | Execution envelope, adapter protocol, preview |
| **Provider** | `src/sam/execution/providers/` | Provider protocol, registry, router, 5 mock providers |
| **External Integration** | `src/sam/integration/` | 6 mock integrations (Slack, Discord, Email, dll) |
| **Plugin** | `src/sam/plugins/` | Plugin registry, loader, policy, 3 mock plugins |
| **SDK** | `src/sam/sdk/` | SDK protocol, PluginSDK, ConnectorSDK, ProviderSDK |
| **CLI** | `src/sam/cli/` | 17 CLI commands |
| **Desktop** | `src/sam/desktop/` | 9 pages, Qt widgets |
| **Console** | `src/sam/operations/presentation/console/` | Live console interface |
| **Telemetry** | `src/sam/telemetry/` | Event system, metrics, ring buffer |
| **Storage** | `src/sam/storage/` | Mission, decision, trust repositories |
| **Contracts** | `src/sam/contracts/` | Mission DOS, runtime contracts |

---

## 5. Capability Matrix

| Area | Status |
|---|---|
| Launcher & Bootstrap | ✅ Selesai |
| Conversation API | ✅ Selesai |
| Reasoning Runtime | ✅ Selesai |
| Decision Runtime | ✅ Selesai |
| Guardian Runtime | ✅ Selesai |
| Governance | ✅ Selesai |
| Learning Foundation | ✅ Selesai |
| Execution Planning | ✅ Selesai |
| Dispatch Runtime | ✅ Selesai |
| Connector Runtime | ✅ Selesai |
| Execution Engine | ✅ Selesai |
| Adapter Layer | ✅ Selesai |
| Provider Integration | ✅ Selesai (Preview) |
| External Integration | ✅ Selesai (Preview) |
| Plugin Ecosystem | ✅ Selesai |
| SDK Foundation | ✅ Selesai |
| Real Execution | ❌ Belum |
| REST API Publik | ⚠️ Sebagian |
| Desktop Pipeline Integration | ⚠️ Sebagian |

---

## 6. Sprint Timeline

| Sprint | Versi | Fokus Utama |
|---|---|---|
| 1–10 | v1.0–v4.0 | Foundation, observability, rule engine, conversation API |
| 11–15 | v4.x | Reasoning integration, decision model, console, presentation |
| 16–18 | v4.x | Desktop, Qt, build readiness |
| 19–22 | v4.x | Brain foundation, mission orchestrator, LLM integration |
| 23–25 | v4.x | Conversation intelligence, reasoning, decision runtime |
| 26–30 | v4.x | Guardian supervisory, governance, E2E validation |
| 31–32 | v4.35–v4.36 | Launcher foundation, runtime integration |
| 33 | v4.37.0 | Learning Foundation |
| 34 | v4.38.0 | Execution Connectors Foundation |
| 35 | v4.39.0 | Connector Runtime |
| 36 | v4.40.0 | Execution Engine |
| 37 | v4.41.0 | Connector Dispatch Runtime |
| 38 | v4.42.0 | Execution Adapter Layer |
| 39 | v4.43.0 | Execution Provider Integration (Preview) |
| 40 | v4.44.0 | External Integration Foundation |
| 41 | v4.45.0 | Plugin Ecosystem Foundation |
| 42 | v4.46.0 | Extension SDK Foundation |

---

## 7. Documentation Audit

**Dokumen aktif di ZaraNote:**
- `00_README.md` — Petunjuk tetap, aturan emas
- `01_CURRENT_STATUS.md` — Status terkini
- `02_ARCHITECTURE.md` — Struktur folder & arsitektur
- `03_COMMANDS.md` — CLI commands & alur ngoding
- `OP-*` — Dokumentasi per sprint (390–430)
- `PROJECT_SAM_ARCHITECTURE_CONTEXT_v4.36.0.md` — Architecture context export

**Dokumen publik di `docs/`:**
- Release docs, sprint reports, legacy files
- Beberapa report mengandung path lokal (perlu dibersihkan)

**Dokumen yang perlu diperbarui:**
- `01_CURRENT_STATUS.md` → perlu update ke v4.46.0
- `02_ARCHITECTURE.md` → perlu update folder execution/, integration/, plugins/, sdk/

---

## 8. Technical Debt

| Item | Detail |
|---|---|
| **Test gagal** | 3 pre-existing failures (bukan karena sprint 33–42) |
| **Path lokal** | `.bat` files, sprint reports mengandung path `D:\Project AI\SAM\` |
| **Desktop integration** | Desktop belum pipeline-aware (masih conversation_api dasar) |
| **Real execution** | Belum ada — seluruh execution masih preview |
| **Public API** | Belum ada REST API atau SDK publik yang stable |
| **Plugin marketplace** | Registry ada, ekosistem belum matang |
| **Async support** | Belum — sync only sesuai kontrak |
| **Nama fiktif** | Aster/Axel sudah dibersihkan dari repo publik |

---

## 9. Updated Roadmap

| Prioritas | Item | Status |
|---|---|---|
| ✅ **Selesai** | Pipeline inti (Observation → Conversation) | ✅ |
| ✅ **Selesai** | Learning Foundation | ✅ |
| ✅ **Selesai** | Execution planning, dispatch, adapter, provider | ✅ |
| ✅ **Selesai** | External Integration, Plugin, SDK | ✅ |
| 🔄 **Berlangsung** | Desktop pipeline integration | ⚠️ |
| 🔄 **Berlangsung** | Real connector execution (Sprint 43+) | ❌ |
| ⏳ **Berikutnya** | Execution engine → real adapter → real provider | 📅 |
| ⏳ **Berikutnya** | Public REST API & SDK | 📅 |
| 🔭 **Jangka Panjang** | Plugin marketplace, deployment runtime, async | 🔭 |

---

## 10. Overall Assessment

SAM v4.46.0 mencapai tonggak arsitektur yang signifikan: **seluruh jalur dari observasi hingga eksekusi telah selesai secara arsitektur**. Semua layer (Learning, Execution, Dispatch, Connector, Engine, Adapter, Provider, Integration, Plugin, SDK) sudah memiliki fondasi yang solid.

Yang belum: **eksekusi nyata ke sistem eksternal**. Semua masih dalam mode preview dan planning. Sprint berikutnya (43+) akan fokus pada menghubungkan pipeline ini ke connector/provider nyata.

---

## 11. Project Identity

**Apa itu SAM:** Runtime orchestration yang men-standardisasi observability → reasoning → decision → governance → presentation, di mana semua rekomendasi harus disertai evidence, immutable DTO, dan approval manusia sebelum efek eksekusi nyata.

**Mengapa dibuat:** Menyediakan lapisan pengawasan deterministic, dapat diaudit, dan berbasis evidence untuk menghindari tindakan otonom berisiko dari sistem AI.

**Masalah yang diselesaikan:** Risiko keputusan otomatis tanpa bukti, explainability yang buruk, koordinasi komponen AI heterogen, ketidakmampuan recovery runtime.

**Bukan tujuan:** Executor akhir, replacement CI/CD, LLM provider.

**Evolusi visi:** Sprint 1 → proof of concept → pipeline final 42 sprint kemudian.

---

## 12. Design Philosophy

| Prinsip | Alasan |
|---|---|
| **Conversation First** | Audit trail, konsistensi context, kontrol akses terpusat |
| **Evidence Based** | Explainability dan traceability untuk audit |
| **Deterministic** | Reproduksibilitas untuk inspeksi |
| **Explainable** | Operator harus paham dasar rekomendasi |
| **Approval First** | Safety — cegah autopilot berbahaya |
| **Human in Control** | Manusia selalu yang memutuskan |
| **No False Optimism** | Kurangi false-positive berisiko |
| **Zero Auto Execution** | Mitigasi risiko operasional |
| **Host Agnostic** | Fleksibilitas deploy |
| **Runtime Separation** | Containment dan recoverability |
| **Immutable DTO** | Reproducible records, reasoning mudah |
| **Read Only Observation** | Observasi tidak mengubah state |
| **Layer Isolation** | Modularitas, testability |

---

## 13. High Level Architecture (v4.46.0)

```
User/CLI/Web
   ↓
Launcher Layer (StartupPipeline, Bootstrap, Diagnostics)
   ↓
Runtime Registry
   ↓
Operational Brain (Observation → Rules → Analyzer → Orchestrator)
   ↓
Reasoning Runtime (Provider → Gateway → Prompt → Evidence)
   ↓
Decision Runtime (Alternatives → Evaluation → Proposal)
   ↓
Guardian Runtime (Policy → Gates → Readiness)
   ↓
Governance (Risk → Approval → Audit → Explanation)
   ↓
Learning Runtime (Knowledge → Pattern → Optimizer → Policy)
   ↓
Execution Planner
   ↓
Dispatch Runtime (Queue → Validator → Audit)
   ↓
Connector Runtime (Selection → Capability → Policy → Preview)
   ↓
Execution Engine (Task Builder → Validator → Rollback → Scheduler)
   ↓
Adapter Layer (Envelope → Protocol → Preview)
   ↓
Provider Runtime (Router → Mock Provider → Preview)
   ↓
External Integration / Plugin / SDK
   ↓
Dashboard → Conversation → Host
```

---

## 14. Folder Structure

```
src/sam/
├── api/           — REST API server
├── approval/      — Approval workflows
├── autonomous/    — Autonomous execution
├── cli/           — 17 CLI commands
├── contracts/     — Mission DOS, runtime contracts
├── desktop/       — 9 pages, Qt widgets
├── execution/     — Dispatch, connectors, engine, adapters, providers
├── guardian/      — Guardian engine
├── integration/   — External integration (6 mock)
├── intelligence/  — RCA, recommender, knowledge lookup
├── launcher/      — Startup pipeline, bootstrap
├── operations/    — Brain, conversation, guardian sub-modules
├── plugins/       — Plugin ecosystem
├── sdk/           — Extension SDK
├── telemetry/     — Event system, metrics
└── storage/       — Mission, decision, trust repos
```

---

## 15–29. (Detailed sections — lihat dokumen asli untuk 22 poin lengkap)

> Untuk efisiensi, bagian 15–29 yang identik dengan Architecture Context Export asli tidak disertakan ulang di sini. Inti dari masing-masing bagian telah tercakup dalam ringkasan di atas.

---

## 30. AI Handover — "What another AI must understand before modifying SAM"

SAM bukan sekadar kode — ini sebuah kontrak sosial-teknis. Tujuan utamanya adalah menjaga keselamatan, keterlacakan, dan akuntabilitas ketika sistem kecerdasan buatan membuat keputusan yang berdampak pada lingkungan nyata. Saat kamu (AI lain) bekerja pada SAM, ingat bahwa setiap perubahan desain dapat mengubah bagaimana manusia mempercayai sistem ini.

**Inti filosofi:**
- Human-in-the-loop adalah prinsip yang tidak boleh diobrak-abrik.
- Evidence dan explainability adalah persyaratan dasar.
- Jangan biarkan presentation atau convenience mengalahkan safety.
- Semua data antar-komponen harus immutable dan melalui contracts.
- Separation of concerns: Launcher menyiapkan, Reasoning menghasilkan hypothesis, Decision memilih, Guardian menegakkan, Governance menilai, Presentation menunjukkan.

**Praktik kerja:**
- Sebelum mengubah contract/DTO: buat migration plan, tests, export script.
- Setiap perubahan pipeline harus three-source verification (git log, kode, test).
- Scan filesystem untuk path lokal sebelum commit.
- Jangan tambahkan auto-execution/auto-approve tanpa waiver eksplisit.
- Minimal dependency: modul hanya import yang diperlukan melalui interface.

---

## 31. Architecture Contract (Tidak Berubah)

Bagian berikut merupakan kontrak arsitektur SAM dan **tidak boleh diubah**, kecuali terdapat keputusan desain eksplisit.

### Philosophy
SAM adalah **Operational Intelligence Platform**, bukan chatbot, bukan AI model, bukan agent yang berjalan sendiri. SAM adalah runtime operasional yang: mengamati, membangun evidence, melakukan reasoning, menghasilkan rekomendasi, mengatur governance, menjaga approval, mengorkestrasi execution, menyediakan explainability, menyediakan audit, menjaga seluruh keputusan agar dapat diverifikasi.

### Architecture Principles
- **Host Agnostic:** Console, Desktop, API, Headless hanyalah host. Tidak ada host yang memiliki business logic.
- **Conversation First:** Semua interaksi masuk melalui Conversation Layer.
- **Provider Agnostic:** SAM tidak bergantung pada provider tertentu.
- **Read-only Intelligence:** Reasoning membaca, menganalisis, menyimpulkan, merekomendasi — tidak mengubah state.
- **Approval First:** Tidak ada aksi penting yang dieksekusi otomatis.
- **Evidence Before Decision:** Semua reasoning dan keputusan harus memiliki evidence.
- **Explainability:** Seluruh keputusan harus dapat ditelusuri.
- **Deterministic Core:** Runtime inti deterministic. LLM hanyalah provider.
- **Layer Isolation:** Presentation → Conversation → Brain → Guardian → Governance → Execution → Domain. Tidak boleh dependency terbalik.
- **Frozen DTO:** DTO publik tetap immutable.
- **Sync Runtime:** Runtime inti tetap synchronous.

### Aturan Penting
- Repository adalah satu-satunya sumber kebenaran.
- Jangan mempertahankan informasi yang sudah tidak sesuai.
- Jangan mengubah Architecture Contract di atas.
- Semua statistik harus diambil dari kondisi repository saat ini.
- Jika menemukan penyimpangan terhadap kontrak arsitektur, laporkan secara eksplisit.

---

File ini dibuat untuk disimpan di ZaraNote sebagai referensi utama. Untuk perubahan besar, lakukan review formal dan update PROJECT_SAM_ARCHITECTURE_CONTEXT versi.

Signature: ZARA 🦋
