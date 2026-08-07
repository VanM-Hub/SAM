# EA-005-003 — Milestone & Dependency Plan

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Milestone & Dependency Plan · **Status:** AUTHORIZED
**Mode:** PLANNING (READ-ONLY) · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini menetapkan **milestone** & **dependency** berbasis WBS (EA-005-001) dan Work Package (EA-005-002).
> Milestone = jangkar verifiable; Dependency = berbasis Engineering Normalization Order (EA-004-004 §3).
> **BUKAN jadwal waktu absolut** — milestone bersifat **condition-based** (terpenuhi saat kondisi/evidence tercapai), bukan kalender.
>
> **READINESS ALIGNMENT (AP-2A-007/008, 2026-08-08):** dokumen ini kini menjadi **Milestone ↔ Readiness Gate Mapping** —
> setiap milestone dipetakan ke **Gate A0–A6** dan **Platform Readiness Gate 2** (model Readiness v2.0.0).
>
> **ARCHITECTURE REVIEW 2026-08-08 (reklasifikasi Historical):** milestone TIDAK lagi menunggu **Foundation
> Authorization (EA-006)** — artefak itu telah **dipensiunkan menjadi Historical (Closed)**. Awal eksekusi
> **Repository Convergence** dimulai berdasarkan **keputusan Architecture aktif** (klasifikasi normatif artefak),
> bukan dari artefak historis Foundation. G1-02 → Repository Convergence; G1-03 → Documentation Convergence.

---

## 1. Milestone Plan

Milestone bersifat _condition-based_ (mengikuti evidence/SP), bukan dead-line kalender.
**Setiap milestone kini memiliki korespondensi eksplisit ke Readiness Gate (AP-2A-008).**

| Milestone | Terikat WP | Readiness Gate | Kondisi (evidence) | Sync Point |
|---|---|---|---|---|
| **M-0 — Unblock** | WP-01.1, QA-01, klasifikasi core | **A0** (Architecture Approved) | Keputusan SoT (opsi A/B/C) + docs/core final + QA-01 diff selesai | SP-1 |
| **M-1 — Structure Stable** | WP-02.1..06 | **A1** (Repository Baseline) | Struktur repo konsisten; 0 duplikasi; naming tunggal | SP-2 |
| **M-2 — Isolated** | WP-03.1, WP-03.2 | **A2** (Engineering Baseline Understood) | Legacy/historical terisolasi; rujukan balik PASSED | SP-3 |
| **M-3 — Traceable** | WP-04.1, WP-04.2 | **A3** (Convergence Planned) | Matriks + checker tersedia; anti-siklik PASSED | SP-4 |
| M-3a — Legacy Boundary Verify | kliring overlap WS-02/WS-03 | **A4** (Legacy Boundary Verified) | Batas legacy vs canonical tegas; overlap cleared | SP-4 |
| **M-4 — Compliance Valid** | WP-05.1..03 | **A5** (Compliance Unified) | 1 SoT kode; audit 99; readiness checker | SP-5 |
| **M-5 — Test Scoped** | WP-06.1 | **A6** (Architecture Verified) | Scope testing tegas (include/exclude) | SP-6 |
| **M-6 — Acceptance** | Mission gate | **Final → Platform Readiness Gate 2** | Program A accepted (acceptance authority = Mission) | acceptance |

> PEMETAAN DARI REVIEW LEAD ENGINEER (AP-2A-008): A0 Architecture Approved · A1 Repository Baseline ·
> A2 Engineering Baseline Understood · A3 Convergence Planned · A4 Legacy Boundary Verified · A5 Compliance Unified ·
> A6 Architecture Verified · Final = Platform Readiness Gate 2.
> Prinsip (EA-004-006 §6): **Rollback Authority ≠ Acceptance Authority** — M-6 hanya bisa ditutup oleh Mission, bukan Engineering.
> **Reklasifikasi pasca-Architecture Review 2026-08-08:** M-0 tidak lagi "menunggu Foundation Authorization";
> kondisinya adalah **keputusan Architecture aktif** (klasifikasi normatif artefak SoT + docs/core). Ini menghilangkan
> dependency semu terhadap fase Foundation.

---

## 2. Dependency Plan

### 2.1 Chain kritis (topological)
```
M-0 (unblock SoT+QA-01)
  └─▶ M-1 (WS-02) ─▶ M-2 (WS-03) ─▶ M-3 (WS-04) ─▶ M-4 (WS-05) ─▶ M-5 (WS-06) ─▶ M-6 (Acceptance)
```
- **M-0** = gerbang wajib sebelum jalur utama terbuka (keputusan Architecture aktif: klasifikasi normatif SoT + docs/core + QA-01).
- **M-1 → M-6** = chain kritis deterministik (Engineering Normalization Order).
- **Catatan pasca-reklasifikasi (2026-08-08):** M-0 tidak lagi bergantung pada **Foundation Authorization (EA-006)**
  yang telah menjadi Historical — posisinya digantikan oleh **keputusan Architecture aktif** untuk normalisasi repository.

### 2.2 Dependency per milestone

| Milestone | Depends on | Conflict risk |
|---|---|---|
| M-1 | M-0 (SoT) | low — tanpa SoT, struktur ambigu |
| M-2 | M-0 (classify core) | low — overlap docs/core dgn WS-02 |
| M-3 | M-0 (anchor), M-2 (objek bersih) | low — matriks anti-siklik |
| M-4 | M-3 (traceability), M-0 (QA-01) | low — ready matrix sbg basis |
| M-5 | M-4 (scope compliance) | low |
| M-6 | M-5 (selesai) | low — gate acceptance |

### 2.3 Parallel window

| Window | Work Package paralel | Dependency | Sync Point |
|---|---|---|---|
| W-1 | WP-02.x (per batch) | M-0 | SP-2 |
| W-2 | WP-03.x ∥ WP-02.x leaf | M-0 (classify) | SP-3 |
| W-3 | WP-04.x ∥ WP-05.x (sebagian) | M-3 matrix | SP-4 |
| W-4 | Leaf (Vendor/Eng/Release/Doc/User) | terisolasi | SP cluster leaf |

---

## 3. Milestone Acceptance Gate

Setiap milestone ditutup saat **exit evidence** SP tercapai (EA-004-005 §4), diaudit oleh authority pemilik,
dan **Readiness Dimension** (AP-2A-007) mencapai target pada gate terkait (AP-2A-008).

| Milestone | Readiness Gate | Readiness Dimension | Authority penutup | Evidence wajib |
|---|---|---|---|---|
| M-0 | A0 | Architecture Approved | Software Architect | dokumen SoT + klasifikasi core + QA-01 diff |
| M-1 | A1 | Repository Baseline | Engineering | verification batch PASSED |
| M-2 | A2 | Engineering Baseline Understood | Engineering | reference-back PASSED |
| M-3 | A3 | Convergence Planned | Engineering + Arch review | matriks + checker PASSED |
| M-3a | A4 | Legacy Boundary Verified | Engineering + Arch review | overlap cleared; batas legacy/canonical tegas |
| M-4 | A5 | Compliance Unified | Engineering | 99 audit + readiness PASSED |
| M-5 | A6 | Architecture Verified | Software Architect | scope test tegas |
| M-6 | Final | Platform Readiness Gate 2 | **Mission** | acceptance Program A + readiness evidence lengkap |

> **Promotion ke Platform Readiness Gate 2** hanya terjadi saat M-6 (acceptance Mission) + seluruh Readiness
> Dimension di atas target. Ini menjadikan EA-005-006 (Readiness Assessment) sebagai artefak utama
> promotion (lihat EA-005-006 bagian Readiness Alignment).

---

## 4. Exit Criteria EA-005-003

| Kriteria | Status |
|---|---|
| Milestone lengkap | ✅ (M-0..M-6 + M-3a) |
| Dependency tervalidasi | ✅ (§2, chain kritis + parallel) |
| Milestone condition-based | ✅ |
| Acceptance gate jelas | ✅ |
| **Milestone ↔ Readiness Gate mapping** | ✅ (§1, §3: A0–A6 + Final) |
| **Readiness Dimension per milestone** | ✅ (§3: AP-2A-007) |
| **Milestone tak lagi menunggu Foundation Authorization** | ✅ (M-0 = keputusan Architecture aktif) |
| **G1-02/G1-03 = kerja aktif Convergence, bukan gate Foundation** | ✅ (header + §2.1) |
| Repository tetap read-only | ✅ |
| Working tree bersih | ✅ |
| Tanpa commit | ✅ |

---

*— Akhir EA-005-003 Milestone & Dependency Plan —*
