# ATLAS v2.1 — Repository Navigation System

**Status:** Live GPS · **Prinsip:** menunjuk, bukan menjelaskan.
> Baca ATLAS = tahu ke mana. Belajar isi = buka dokumen yang ditunjuk.

---

## 0. MASTER MAP

```
                          PROJECT SAM
                             │
              ┌──────────────┴──────────────┐
              │                             │
          DOCUMENTS                    SOURCE CODE
              │                             │
        ┌─────┴─────┐              ┌─────────┴─────────┐
        │           │              │                   │
   IDENTITY     AUTHORITY      WORLD (aktif)      LEGACY (historis)
        │           │              │                   │
   MISSION     CONSTITUTION    runtime_service     operations
   VISION      CITIZEN         execution_runtime   execution
   CHARTER     ARCHITECTURE    presentation        runtime
   PRINCIPLES  ADR             web                 reasoning
   GOVERNANCE  SPECIFICATION
              RUNTIME
              COMPLIANCE
              ENGINEERING
              (strategy · roadmap)
              HISTORY
```

> Legend: peta 2 sisi — **DOCUMENTS** (otoritas) kiri, **SOURCE CODE** (implementasi) kanan.
> Detail setiap simpul ada di bagian berikutnya — ATLAS hanya menunjuk.

---

## 1. DOCUMENTS — RUMPUN

```
 MISSION ── VISION ── CHARTER ── PRINCIPLES ── GOVERNANCE
                                    │
   CITIZEN SPEC (jembatan) ◄────── CONSTITUTION
                                    │
   Citizen (unit arsitektur) ◄──── ARCHITECTURE (SAM_ARCHITECTURE.md)
                                    │
        ┌───────────────┬──────────┴───────────┐
        │               │                      │
       ADR           SPECIFICATION           RUNTIME
  (docs/adr)    (docs/specifications)   (docs/runtime)
        │               │                      │
        │               │               ┌─────┴─────┐
        │               │               │           │
        │               │           R4/R5      I-series
        │               │           (arsitek)  (impl blueprint)
        │               │               │           │
        │               │               └─────┬─────┘
        │               │                     │
        │               │              COMPLIANCE (docs/compliance P1-001..008)
        │               │                     │
        │               │               ENGINEERING
        │               │               (docs/design)
        │               │               │
        │               │        IMPLEMENTATION (src/)
        │               │               │
        │               │            HISTORY (docs/history — ARSIP, bukan autoriti)
```

- **Klik "perlu keputusan arsitektur?"** → `docs/adr/` (1 keputusan = 1 file, record-only)
- **Klik "kontrak fungsi?"** → `docs/specifications/` (freeze)
- **Klik "bagaimana membangun runtime?"** → `docs/runtime/` (R4→R5→I-series)
- **Klik "sudah sesuai?"** → `docs/compliance/`
- **Klik "masa lalu?"** → `docs/history/` — baca saja, jangan dipakai utk keputusan baru
- **Klik "keputusan/catatan engineering?"** → `docs/engineering/` (reports/journals/templates) - Architecture Order aktif (Close Order SAM 2.x/3.x) -> `docs/decisions/`; laporan program selesai -> docs/history/reports/
- **Klik "strategi pengembangan?"** → `docs/engineering/strategy/` (DEVELOPMENT_STRATEGY, Planning Standard, Readiness Model)
- **Klik "rencana kerja/roadmap?"** → `docs/engineering/roadmap/` (ROADMAP SAM 2.x.md, Program A–E, Milestone Architecture, Appendix)
- **Klik "sudah jadi arsip non-aktif?"** → `docs/history/`

---

## 2. SOURCE CODE — RUMPUN

```
 src/sam/
   │
   ├── world (AKTIF, jalur resmi — ubah di sini utk capability baru)
   │     runtime_service       ← GATEWAY (konsumen: 6 capability)
   │     observation           ← OBSERVATION LAYER (C-Phase 1-4, read-only + gap resolution + recommendation + C1-C10 intel)
   │     execution_runtime     ← Execution (preview, ADR-024)
   │     presentation          ← UI entry (memakai RuntimeService)
   │     web / desktop         ← host UI
   │     knowledge_runtime / workflow_runtime / artifact_runtime /
   │     memory / policy_runtime / audit_runtime   ← 6 capability AKTIF
   │
   ├── 4.0 (SAM 4.0 - Federated Governance Platform, baseline resmi)
   │     operational_intelligence   ← Investigasi/diagnosis/evidence/RCA/risk/trust (4.2)
   │     operational_learning       ← Persistence + operational knowledge (4.3)
   │     governed_reasoning         ← Governed AI reasoning (4.4)
   │     autonomous_operations      ← Investigate/diagnose/recommend/verify (4.5)
   │     operational_workspace      ← Integration layer + EndToEndFlow + ProductionPlatform (4.6)
   │       └── web_ui_server.py     ← Presentation layer FastAPI (UI produksi, Article XVI)
   │       └── web_ui/              ← Host web UI (index.html)
   │
   ├── 5.x (SAM 5.x - Universal Governance Platform, citizen governance)
   │     universal_ai             ← Multi-provider AI platform (5.1)
   │     universal_tool           ← Tool citizen + governed execution (5.2)
   │     universal_agent          ← Agent citizen + governed collaboration (5.3)
   │     universal_workflow       ← Workflow citizen + governed execution (5.4)
   │     enterprise_governance    ← Org/tenant/policy/audit boundary (5.5)
   │     adaptive_governance      ← Learning/simulation/impact/recommendation (5.6, authority di manusia)
   │
   ├── legacy (HISTORIS — jangan tambah dependency baru)
   │     operations / execution / runtime / reasoning
   │
   ├── backlog (belum aktif; butuh Architecture Decision)
   │     intelligence_runtime / agent / model_runtime / connectors /
   │     orchestrator / skills / ...
   │
   └── infra/core
         cli / api / launcher / core / storage / telemetry / contracts / ...
```

> Simpul folder detail yang berubah-ubah → urusannya **Architecture**.
> ATLAS hanya menunjuk: *"kalau mau capability → runtime_service; kalau mau host UI → presentation"*.

---

## 3. AUTHORITY (yang stabil)

```
 MISSION ─────────── tak boleh diubah siapa pun (kecuali amandemen)
    │
 VISION
    │
 CONSTITUTION ────── Engineering TIDAK boleh ubah
    │
 CITIZEN SPEC
    │
 ARCHITECTURE ────── ubah = Architecture Session (bukan Engineering)
    │
 ADR ─────────────── catat keputusan baru; jangan edit yang lama
    │
 SPECIFICATION ───── freeze
    │
 RUNTIME → COMPLIANCE → ENGINEERING → IMPLEMENTATION (zona engineer)
```

| Kalau mau sentuh | Boleh oleh | TIDAK boleh oleh |
|---|---|---|
| Mission / Constitution / Architecture | Amandemen / Architecture Session | Engineering, code |
| ADR | File ADR baru | Edit langsung |
| code / runtime / activation | Engineering | Mission/Architecture |

---

## 4. YOU ARE HERE (posisi project)

```
 CURRENT PHASE
   Mission            ✓
   Architecture       ✓
   Specification      ✓
   Reference Runtime  ✓
   Engineering        ✓   (S01-S10 selesai; Program A/B/C closed)
   Operationalization ◉  ← KAMU DI SINI (M3 Observable Platform; 6 capability active)
   Production         ✓   (SAM 2.0 COMPLETE - Program A-F finished, M1-M6 achieved, Milestone M6 ACHIEVED)
   Ecosystem          ✓   (SAM 3.x COMPLETE 6/6 - release v3.6.0, 2026-08-09)
   Federation         ✓   (SAM 4.0 - Federated Governance Platform - release v4.0.0, 2026-08-10 - ARCHITECTURE ACCEPTED, CA verdict: 4.1 CLOSED, 4.2..4.6 ACCEPTED)
```
> Fase: **Product Integration & Operationalization** (Tahap 2). Execution = preview (ADR-024).
> Observability: Observation Layer (C-Phase 1-4) sudah observasi 5 pipeline + Platform Intelligence (C6-C10) secara read-only (M3).
> Program C **CLOSED** (Verdict EA-C06); M3 Observable Platform tercapai.
> **Program D (MISSION-2D) EA-002 Production Readiness Implementation SELESAI** - Verdict EA-002/EA-003; Official Order P1-P5. **Kelima High gap DONE** (H1 portable + H5 IAM + H2 recovery + H3 deploy rollback + H4 operational alerting; modul sam/iam + sam/recovery + sam/deploy_rollback + sam/operational_alerting; 8+30+23+24+25 test). EA-002 Implementation COMPLETE, menunggu Verdict Lead Engineer. Menuju Production Platform (M4).
> **Program E (MISSION-2E) EA-002 Early Adopter Experience Implementation ACTIVE** - Verdict EA-002 (AP-2E-001); Official Order WP-E2.1..E2.5. **WP-E2.1 E1-G1 Automatic Bootstrap Installation DONE** (modul sam/devx; 28 test evidence; baseline 4290 passed, no regression). **WP-E2.2 E2-G1 CLI Onboarding DONE** (sam onboarding init/doctor/version; 12 test evidence; integration 198 passed, no regression). **WP-E2.3 E4-G1 End-to-End Quick Start DONE** (docs/user/quickstart.md + README section 7). **WP-E2.4 E5-G1 Starter Project DONE** (sam onboarding init --scaffold; 13 test evidence; integration 211 passed). **WP-E2.5 E3-G1 SDK Public API DONE** (sam root exports SAM+Conversation+MissionSession; 7 test evidence; baseline unit 2970 passed). **PROGRAM E - SELURUH 5 WP SELESAI.**
> **Program F (MISSION-2F) SAM 2.0 Certification CLOSED (Verdict EA-M6)** - MISSION-2F ACCEPTED; **Milestone M6 (SAM 2.0) ACHIEVED**; **SAM 2.0 COMPLETE**; Program A-F finished, M1-M6 achieved, no drift; Engineering Phase SAM 2.x CLOSED; SAM 3.x planning dapat dimulai arsitektural. **PROGRAM F - SEMUA DELIVERABLE SELESAI, SAM 2.0 COMPLETE.**
> **SAM 3.x COMPLETE (2026-08-09) - rilis v3.6.0** - MISSION-3.1 Governance Intelligence, MISSION-3.2 Autonomous Runtime, MISSION-3.3 Citizen Ecosystem, MISSION-3.4 Federation, MISSION-3.5 Platform Experience, MISSION-3.6 Production Governance **COMPLETE 6/6**. Production Readiness CERTIFIED, Federation Readiness CERTIFIED. **SAM 3.x baseline release (3.6.0)**; jenjang berikut: **SAM 4.x Federation Operations**. Platform Experience & Production Governance lives in `src/sam/platform/` (compliance group PEX/MEX/CX/EX/PG/PO/OE/PR/MC). **Close Order AO-2.0-001 (SAM 2.x) & AO-3.0-001 (SAM 3.0) di `docs/decisions/`** → memberi kewenangan perbaikan SAM 2/3 selama tidak mengubah Foundation.

---

## 5. KNOWLEDGE FLOW (dari ide → operasional → arsip)

```
 IDE → MISSION → ARCHITECTURE → ADR → SPECIFICATION → RUNTIME
   → ENGINEERING/CODE → COMPLIANCE → OPERATIONAL → HISTORY
```

---

## 6. ENGINEERING FLOW (Decision Matrix — tanpa paragraf)

```
 MAU TAMBAH RUNTIME CAPABILITY?
   → AD-ENG-001/002/003 (docs/engineering/decisions/) → sudah ada Registry+Bridge+DI?
   → → ENGINEERING; belum → ARCHITECTURE BACKLOG

 MAU BUAT PROVIDER?
   → ADR-006 → src/sam/providers/ → ConnectionRuntime → preview (ADR-024)
   → LARANG provider baru tanpa consumer

 MAU PERBAIKI PRESENTATION / DASHBOARD?
   → Article XVI (Presentation Principle) → src/sam/presentation/ + runtime_service
   → tanpa business logic; komunikasi via RuntimeService

 MAU PERBAIKI COMPLIANCE?
   → docs/compliance P1-001..008 → src/sam/compliance/ → scripts/validation/
```

---

## 7. RUNTIME NAVIGATION (mana baca dulu)

```
 Reference Runtime (ide)
      ↓
   R4 (Arsitektur) → R5 (Model Engineering)
      ↓
   I-series (I0 blueprint → I1 skeleton → I2 impl 7 unit)
      ↓
   P0 (Sertifikasi)
      ↓
   E1 (Composition Root) → runtime_root (executable)
      ↓
 runtime (kernel/coordinator) ── presentation (UI entry)

 Jalur activation (resmi sekarang):
   conversation → runtime_service → execution_runtime → consumer → registry → bridge → STOP
```

> Yang perlu kau baca **pertama kali** saat mau runtime: `R4 → R5 → I-series → runtime_root`.

---

## 8. READING PATHS (flowchart tujuan)

```
 paham SAM         → MISSION → VISION → CHARTER → CONSTITUTION → SAM_ARCHITECTURE
 coba cepat (quick start) → README §7 Quick Start → docs/user/quickstart.md → cli_reference.md
 jadi kontributor  → README → ATLAS → GOVERNANCE → CONTRIBUTING → REPOSITORY_CONVENTION
 perbaiki runtime  → docs/runtime (R4/R5/I-series) → runtime_root → compliance
 buat capability   → AD-ENG-001/002/003 → Activation Pattern → docs/engineering/decisions/ (arsip) | Architecture Order aktif -> docs/decisions/
 perbaiki UI       → Article XVI → presentation → runtime_service
 paham citizen     → docs/CITIZEN_SPECIFICATION → SAM_ARCHITECTURE (Citizen)
 paham compliance  → docs/compliance P1-001 → src/sam/compliance
 paham engineering → docs/engineering/ (strategy · roadmap · decisions/reports/journals) → docs/history
```

---

## 9. REPOSITORY MAP (perintah "klik")

```
 ROOT
   ├── Identity      (MISSION, VISION, CHARTER, PRINCIPLES, GOVERNANCE)
   ├── Documentation (docs/ — authority + engineering(docs/engineering) + history)
   ├── Source        (src/sam/ — implementasi: world/legacy/backlog/infra)
   ├── Tests         (tests/ — folder baseline CI: unit + 8 runtime suites + observation layer C1-C10, 273 observation tests)
   ├── Tools         (scripts/ — validasi; data/ — migrasi)
   └── History       (docs/history/ — arsip, bukan authority)
```

---

## 10. RULES (pagar navigasi)

```
 • code tidak ubah Mission/Constitution/Architecture
 • engineering tidak ubah Architecture; ubah = Architecture Session
 • history bukan authority (read-only)
 • dokumen ber-status Draft/Deprecated (mis. konsep arsitektur eksploratif) = IDE, bukan status SAM saat ini
 • ADR = keputusan; specification = kontrak — beda
 • presentation tanpa business logic / tanpa coordinator (Article XVI)
 • provider tanpa governance; approval wajib; preview-first (ADR-024)
 • capability gagal AD-ENG → Architecture Backlog (jangan diaktifkan paksa)
 • catatan internal engineer tidak pernah di-commit; laporan publik → docs/history
 • jangan tambah runtime baru sebelum existing punya consumer
```

---

## 11. MAINTENANCE

- **Ukuran:** jangan melebihi ~15 halaman / ~15KB. Kurangi teks, bukan perbesar.
- **Isi:** hanya arah/diagram/hubungan. Bukan isi dokumen.
- **Ubah oleh:** Chief Repository Architect (besar) / Maintenance Session (kecil).
- **Update saat:** struktur/authority/status aktivasi berubah — jangan biarkan ATLAS tertinggal.
- **Uji:** *"bisa navigasi ke dokumen/folder yang tepat hanya dari ATLAS?"* → kalau ya, sehat.

---

*ATLAS menunjuk jalan. Dokumen lain yang membawa isi.*
*Kebijakan arsip: docs/HISTORY_POLICY.md.*
