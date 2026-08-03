# Migration Index — Repository Documentation Cleanup (Phase C1)

> **Status:** REFERENCE (indeks navigasi)
> Mencatat perpindahan dokumen selama Phase C1 (Repository Cleanup).
> Berguna saat membaca commit lama atau melakukan `git blame` — path lama kini diatribusikan ke lokasi baru.
> Dibuat: 2026-08-03

Format: **Old Path → New Path → Reason**

## C1-A — History Migration (commit `d9a4949`)

| Old Path | New Path | Reason |
|---|---|---|
| `docs/sprint-reports/` | `docs/history/sprint-reports/` | Historical artifact (195 laporan sprint) |
| `docs/reports/` | `docs/history/reports/` | Historical artifact (56 laporan op/program) |
| `docs/legacy/` | `docs/history/legacy/` | Historical artifact (14 dokumen legacy) |
| `docs/program-e-reports/` | `docs/history/program-e-reports/` | Historical artifact (8 laporan Program E) |
| `docs/program-f-reports/` | `docs/history/program-f-reports/` | Historical artifact (8 laporan Program F) |
| `docs/audit/` | `docs/history/audit/` | Historical artifact (3 audit report) |

## C1-B — Duplicate / Status Consolidation

### Arsitektur (commit `58342bf` + fase C1-B)
| Old Path | New Path | Reason |
|---|---|---|
| `docs/architecture/SAM_ARCHITECTURE_MASTER.md` | `docs/history/architecture/SAM_ARCHITECTURE_MASTER.md` | Superseded (AD-028); canonical = `docs/architecture/SAM_ARCHITECTURE.md` |
| `docs/architecture/ARCHITECTURE.md` | `docs/history/architecture/ARCHITECTURE.md` | Superseded (AD-028); canonical = `docs/architecture/SAM_ARCHITECTURE.md` |
| `docs/architecture/SAM_CONSTITUTION.md` | `docs/history/architecture/SAM_CONSTITUTION.md` | Self-declared Historical; canonical = `docs/CONSTITUTION.md` |

### Release — Hybrid Consolidation (docs/releases/ canonical)
| Old Path | New Path | Reason |
|---|---|---|
| `docs/releases/Release_Checklist.md` | `docs/releases/release_checklist.md` | Canonical rename (satu checklist release) |
| `docs/releases/v29.0.0_release.md` | `docs/releases/release_notes/v29.md` | Release notes — dikelompokkan ke `release_notes/` |
| `docs/releases/v30.0.0_release.md` | `docs/releases/release_notes/v30.md` | Release notes — dikelompokkan ke `release_notes/` |
| `docs/release/v1.0_release_notes.md` | `docs/releases/release_notes/v1.0.md` | Release notes — canonical di `docs/releases/` |
| `docs/release/compatibility.md` | `docs/releases/compatibility.md` | Canonical (cara melakukan release) |
| `docs/release/upgrade.md` | `docs/releases/upgrade.md` | Canonical (cara melakukan release) |
| `docs/release/RC1_Validation_Report.md` | `docs/releases/history/RC1_Validation.md` | Historical (hasil proses release → history) |
| `docs/release/RC2_Validation_Report.md` | `docs/releases/history/RC2_Validation.md` | Historical (hasil proses release → history) |
| `docs/release/RC3_Validation_Report.md` | `docs/releases/history/RC3_Validation.md` | Historical (hasil proses release → history) |
| `docs/release/ARCHITECTURE_FREEZE.md` | `docs/releases/history/ARCHITECTURE_FREEZE.md` | Historical (era release awal) |
| `docs/release/CHECKLIST_RC1.md` | `docs/releases/history/CHECKLIST_RC1.md` | Historical (RC checkpoint) |
| `docs/release/RC2_linux_guide.md` | `docs/releases/history/RC2_linux_guide.md` | Historical (RC checklist artifact) |
| `docs/release/release_checklist.md` (v1.0.0) | `docs/releases/history/release_checklist_v1.0.md` | Historical (checklist satu-kali rilis v1.0) |

## C1-C — Obsolete Cleanup (commit `b79ac24`)

| Old Path | New Path | Reason |
|---|---|---|
| `docs/core/CONSTITUTION.md` | *(deleted)* | OBSOLETE — superseded oleh `docs/CONSTITUTION.md` (canonical v1.0); self-flag Draft/Superseded. 27 referensi dialihkan ke canonical |
| `docs/install.md` | `docs/history/install.md` | OBSOLETE di root — 0 referensi; panduan EN Desktop Qt unik dipertahankan di arsip |

## Status Dokumen — Capability SDK (bukan move, merupakan re-classification)

| Path | Status Baru | Reason |
|---|---|---|
| `docs/development/capability_sdk.md` | **CANONICAL** | Konsep, cara pakai, API publik, workflow — mudah dibaca |
| `docs/implementation/capability-sdk.md` | **REFERENCE** | Detail implementasi, contoh engineering, keputusan teknis |

## Referensi yang Diperbarui (broken-link fix)

Setiap move di atas diikuti pembaruan link yang terdampak pada dokumen aktif:
- `README.md`, `CHANGELOG.md` — path `docs/reports/`, `docs/sprint-reports/` → `docs/history/...`
- `docs/CONSTITUTION.md` — `SAM_CONSTITUTION` → `docs/history/architecture/`
- `docs/architecture/SAM_ARCHITECTURE.md` — pointer ke arsip architecture
- `docs/releases/release_checklist.md`, `docs/releases/release_notes/*.md`, `docs/releases/history/ARCHITECTURE_FREEZE.md` — path folder yang dipindah
