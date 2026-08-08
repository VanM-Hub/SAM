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
- **Klik "keputusan/catatan engineering?"** → `docs/engineering/` (decisions/reports/journals/templates)
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
   Production         ◉   (PROGRAM D - EA-002 Implementation Active; P1/H1 done)
```
> Fase: **Product Integration & Operationalization** (Tahap 2). Execution = preview (ADR-024).
> Observability: Observation Layer (C-Phase 1-4) sudah observasi 5 pipeline + Platform Intelligence (C6-C10) secara read-only (M3).
> Program C **CLOSED** (Verdict EA-C06); M3 Observable Platform tercapai.
> **Program D (MISSION-2D) EA-002 Implementation Active** - Verdict EA-002/EA-003; Official Order P1-P5. **P1/H1 + P2/H5 + P3/H2 + P4/H3 DONE** (5 .bat portable + modul sam/iam + modul sam/recovery + modul sam/deploy_rollback; 8+30+23+24 test). Next: P5/H4 Operational Alerting. Menuju Production Platform (M4).

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
 jadi kontributor  → README → ATLAS → GOVERNANCE → CONTRIBUTING → REPOSITORY_CONVENTION
 perbaiki runtime  → docs/runtime (R4/R5/I-series) → runtime_root → compliance
 buat capability   → AD-ENG-001/002/003 → Activation Pattern → docs/engineering/decisions/
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
