# EA-001 — Repository Mapping Report

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Package:** EA-001 · **Status:** AUTHORIZED · **Bersifat:** 100% READ-ONLY
**Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)
**Repo:** repositori SAM (origin: `VanM-Hub/SAM`)

> Dokumen ini murni observasi & pemetaan. Tidak ada perubahan/commit/branch pada repository.

---

## A. Repository Structure

### A.0 Ringkasan Area (Root, level 1–2)

| Area | Jumlah File | Klasifikasi | Keterangan |
|---|---|---|---|
| `docs/` | 220 (git-tracked) | Dokumentasi (canonical+engineering+history) | 22 folder non-kosong |
| `src/` | 2656 | Source code | `src/sam/` utama + `.venv` + egg-info |
| `tests/` | 550 | Pengujian | 62+ folder sprint + capability |
| `scripts/` | 13 | Tooling/validasi | validasi + helper |
| `modules/openclaw/` | 80 | **Vendor/eksternal ter-track** | copy OpenClaw |
| `examples/` | 6 | Contoh | plugins + workflows |
| `data/` | 4 | Migrasi data | migrations/SQL |
| `workspace/` | 4450 | **Runtime (git-ignore)** | manifest/sessions/telemetry |
| `memory/` | 1 | **Runtime (git-ignore)** | — |
| Root files | 32 | Kebijakan/konfigurasi | README, ATLAS, .bat, dll. |

### A.1 Canonical Folders (`docs/`)

| Folder | File | Peran |
|---|---|---|
| `docs/foundation/` | 9 | MISSION, VISION, CHARTER, PRINCIPLES, GOVERNANCE, CONSTITUTION, GLOSSARY, PHILOSOPHY, CITIZEN_SPECIFICATION |
| `docs/specifications/` | 7 | Kontrak fungsional (APPROVAL, AUDIT, CAPABILITY, CONTRACT, EXECUTION, REGISTRY, FRAMEWORK) |
| `docs/adr/` | 25 | Architecture Decision Records (ADR-000…028, gap 008/009/010/014) |
| `docs/compliance/` | 8 | Baseline P1-001…008 |
| `docs/runtime/` | 15 | Blueprint runtime (R4/R5/I-series/E1) |
| `docs/architecture/` | 24 | SAM_ARCHITECTURE + diagram + rulebook + DTO/permission maps |

### A.2 Engineering Folders (`docs/`)

| Folder | File | Peran |
|---|---|---|
| `docs/engineering/` | 29 | decisions(7) + journals(3) + roadmap(11) + strategy(3) + templates(2) + README |
| `docs/design/` | 30 | Design recovery / blueprint R/D/C/E/G/O |
| `docs/development/` | 6 | Panduan developer eksternal (SDK/plugin/DSL/API/stability/RFC) |
| `docs/implementation/` | 4 | Implementasi SDK/runtime/data/repo |
| `docs/documentation/` | 8 | Aturan pengelolaan dokumen |

### A.3 Historical/Legacy Folders

| Folder | File | Peran |
|---|---|---|
| `docs/history/` | 6 | `legacy/` (6 dokumen era Framework+Module yang di-archive) + subfolder kosong `audit/`, `reports/`, `sprint-reports/` |
| `docs/releases/history/` | 0 | **Kosong** (arsip release lama dihapus/berpindah) |
| `docs/engineering/references/` | 0 | **Kosong** (25 file EC-* dihapus) |
| `docs/engineering/reports/` | 0 | **Kosong** |

### A.4 Generated/Temporary Folders

| Folder | Peran | Status git |
|---|---|---|
| `workspace/` | Runtime data (manifest/sessions/telemetry) | git-ignore |
| `memory/` | Runtime data | git-ignore |
| `src/.venv/`, `.venv/` | Virtual env | git-ignore |
| `__pycache__/` (banyak) | Cache Python | git-ignore |
| `.pytest_cache/`, `.ruff_cache/` | Cache tooling | git-ignore |
| `src/sam.egg-info/`, `src/sam_ops.egg-info/` | Build artifact | — |
| `*.pyc` | Bytecode | git-ignore |

### A.5 Repository Inventory (kuantitatif)

| Kategori | Jumlah |
|---|---|
| Canonical documents (foundation 9 + specification 7 + ADR 25 + compliance 8 + architecture inti) | **~53** (definisi ketat) |
| ADR | 25 |
| Spec | 7 |
| Engineering documents (engineering 29 + design 30) | 59 |
| History (legacy) | 6 |
| Release artifact aktif | 4 (compatibility, manifest, checklist, upgrade) |
| Compliance artifact (docs) | 8 |
| Compliance checker (kode) | framework + **99 placeholder** |
| Folder docs aktif | 22 |
| Folder docs kosong | 8 |
| Folder docs nyaris kosong (.gitkeep saja) | 3 |

---

## B. Canonical Documents

Daftar dokumen dengan status otoritas (immutable/canonical) di repo:

| Dokumen | Lokasi | Status |
|---|---|---|
| MISSION, VISION, CHARTER, PRINCIPLES, GOVERNANCE, CONSTITUTION, GLOSSARY, PHILOSOPHY, CITIZEN_SPECIFICATION | `docs/foundation/` | **Canonical (immutable)** |
| `docs/foundation/CITIZEN_SPECIFICATION.md` | `docs/foundation/` | Canonical |
| `docs/architecture/SAM_ARCHITECTURE.md` | `docs/architecture/` | Canonical (arsitektur) |
| ADR-000…028 (`docs/adr/`) | `docs/adr/` | Canonical (keputusan, record-only) |
| 7 specification (`docs/specifications/`) | `docs/specifications/` | Canonical (freeze) |
| P1-001…008 (`docs/compliance/`) | `docs/compliance/` | Canonical baseline |
| `docs/HISTORY_POLICY.md` | `docs/` | Kebijakan arsip |
| `docs/SPECIFICATION_FREEZE.md` | `docs/` | Kebijakan freeze |
| `docs/engineering/strategy/*` | `docs/engineering/strategy/` | **Strategi SAM 2.x (autoritas Chief Architect)** |
| `docs/engineering/roadmap/ROADMAP SAM 2.x.md` + Program/Milestone/Appendix | `docs/engineering/roadmap/` | Rencana kerja (bukan Source of Truth) |

> Catatan: Terdapat **duplikasi konsep canonical** di root: `MISSION/VISION/CONSTITUTION/dll` TIDAK ada di root (hanya di `docs/foundation/`), sehingga **tidak ada duplikasi canonical antar lokasi**. Namun beberapa file root berperan mirip canonical: `ROADMAP.md`, `ATLAS.md`, `REPOSITORY_CONVENTION.md`, `DEPENDENCY_MATRIX.md`, `SPRINT_TRACKER.md` — posisinya vs kitab SAM 2.x perlu penegasan (lihat Gap G1/G6).

---

## C. Repository Ownership

| Area | Pemilik (Authority) | Lokasi |
|---|---|---|
| Architecture | Software Architect | `docs/architecture/`, `docs/adr/`, `docs/specifications/` |
| Foundation | Mission/Constitution (amandemen) | `docs/foundation/` |
| Engineering | ZARA (Lead Implementation Engineer) | `docs/engineering/`, `docs/design/`, `src/sam/`, `tests/` |
| History / Legacy | Maintenance/Archive | `docs/history/` |
| Release | Release Manager | `docs/releases/`, tag `v1.0.0` |
| Compliance | Compliance Owner | `docs/compliance/`, `src/sam/compliance/` |
| Runtime | Engineering (preview-first, ADR-024) | `src/sam/runtime*/`, `docs/runtime/` |
| Presentation | Engineering (Article XVI) | `src/sam/presentation/` |
| Tests | Engineering | `tests/` |
| Docs (kebijakan umum) | Maintenance | `docs/documentation/` |
| Scripts/Tools | Engineering | `scripts/` |

---

## D. Repository Dependency Map

```
                    ┌────────────────────────────┐
                    │   FOUNDATION (immutable)    │
                    │  docs/foundation/ 9 docs    │
                    └──────────┬─────────────────┘
                               │  (otoritas)
                    ┌──────────▼─────────────────┐
                    │   ARCHITECTURE (canonical)  │
                    │  adr/ · specifications/ ·    │
                    │  architecture/ · compliance/ │
                    └──────────┬─────────────────┘
                               │  (kontrak)
                    ┌──────────▼─────────────────┐
                    │   RUNTIME (blueprint)       │
                    │  docs/runtime/ · core/      │
                    └──────────┬─────────────────┘
                               │  (implementasi)
                    ┌──────────▼─────────────────┐
                    │   ENGINEERING (aktif)       │
                    │  engineering/ · design/     │
                    │  development/ · implementation/│
                    └──────────┬─────────────────┘
                               │  (kode)
                    ┌──────────▼─────────────────┐
                    │   SOURCE (src/sam/)         │
                    │  world · legacy · inti      │
                    └──────────┬─────────────────┘
                               │  (uji)
                    ┌──────────▼─────────────────┐
                    │   TESTS (tests/)            │
                    └──────────┬─────────────────┘
                               │  (bukti/rilis)
                    ┌──────────▼─────────────────┐
                    │   RELEASE · HISTORY         │
                    │  releases/ · history/       │
                    └────────────────────────────┘
```

**Aliran dependency** (utama):
- Foundation → Architecture → Runtime → Engineering → Source → Tests → Release/History
- Strategy SAM 2.x (`engineering/strategy/`) → Roadmap → Program → Milestone → Appendix (rantai internal)
- Compliance (`docs/compliance/` P1-x) ↔ Kode compliance (`src/sam/compliance/`) ↔ Evidence/Report

**Area terhubung compliance (dipetakan kode `loader.py`):**
`docs/foundation`, `docs/specifications`, `docs/adr`, `docs/runtime`, `docs/engineering`, `docs/blueprint`(+`blueprints`), `docs/compliance`, `docs/architecture`, `docs/design`, `docs/core` → semua dipetakan ke `_DOC_DIR_TYPES`.
> Catatan: `docs/development`, `docs/implementation`, `docs/documentation`, `docs/user`, `docs/releases`, `docs/history` **TIDAK dipetakan** oleh `loader.py` (bukan bagian baseline compliance).

---

*— Akhir Repository Mapping Report —*
