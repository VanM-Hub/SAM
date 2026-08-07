# EA-005-002 — Work Package Definition

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Work Package Definition · **Status:** AUTHORIZED
**Mode:** PLANNING (READ-ONLY) · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini mendefinisikan setiap **Work Package (WP)** dari WBS (EA-005-001 §1 Level 2) secara lengkap:
> tujuan, input, output, dependency, owner, rollback boundary, acceptance target, status readiness.
> Mengikuti **Engineering Execution Rules** (EA-004-005 §2) & model rollback (EA-004-006).
> **BUKAN task teknis / WBS rinci implementasi.**
>
> **READINESS ALIGNMENT (AP-2A-007/008, 2026-08-08):** setiap WP kini memiliki atribut **Target Readiness**
> (Readiness Dimension yg harus dicapai) dan **Exit Gate** (Gate A0–A6/Final yg harus dilulusi) — konsisten
> dgn kolom Readiness Dimension & Gate ID di EA-005-001.

---

## 1. Work Package Definition Table

### WS-01 — Source of Truth

| Attribut | WP-01.1 |
|---|---|
| Gap | G1-02, (G8-03 cross) |
| Tujuan | Tetapkan 1 SoT dokumen roadmap; klasifikasi docs/core |
| Input | EA-003-003 (opsi A/B/C) |
| Output | SoT per domain final; status docs/core |
| Dependency | none (blocker utama) |
| Owner | Software Architect |
| Rollback boundary | 1 keputusan (revisable) sblm publikasi |
| **Target Readiness** | **Architecture Approved** (AP-2A-007) |
| **Exit Gate** | **A0** |
| Acceptance | SP-1 exit |
| Status | **Blocked** (Architecture Blocker) |

### WS-02 — Repository Normalization

| Attribut | WP-02.1 | WP-02.2 | WP-02.3 | WP-02.4 | WP-02.5 | WP-02.6 |
|---|---|---|---|---|---|---|
| Gap | G1-01, G1-03 | G2-01..04 | G3-01..03 | G6-01..06 | G7-01..04 | G8-01, G8-02 |
| Tema | dedupe canonical | dedupe engineering | orphan | repo inconsistency | naming | doc inconsistency |
| Input | WP-01.1 | WP-01.1 | WP-01.1 | WP-01.1 | WP-01.1 | WP-01.1 |
| Output | canonical tunggal | engineering tunggal | orphan resolved | konsisten | naming tunggal | konsisten |
| Dependency | WP-01.1 | WP-01.1 | WP-01.1 | WP-01.1 | WP-01.1 | WP-01.1 |
| Owner | Engineering | Engineering | Engineering | Engineering | Engineering | Engineering |
| Rollback | 1 batch | 1 batch | 1 batch | 1 batch | 1 batch | 1 batch |
| **Target Readiness** | **Repository Baseline** | **Repository Baseline** | **Repository Baseline** | **Repository Baseline** | **Repository Baseline** | **Repository Baseline** |
| **Exit Gate** | **A1** | **A1** | **A1** | **A1** | **A1** | **A1** |
| Acceptance | SP-2 | SP-2 | SP-2 | SP-2 | SP-2 | SP-2 |
| Status | Ready* | Ready* | Ready* | Ready* | Ready* | Ready* |

*Ready setelah WP-01.1 (SoT) unblock.

### WS-03 — Legacy Isolation

| Attribut | WP-03.1 | WP-03.2 |
|---|---|---|
| Gap | G4-01..03 | G5-01..03 |
| Tema | isolasi legacy | isolasi historical |
| Input | WP-01.1 (classify core) | WP-01.1 (classify core) |
| Output | legacy terisolasi (dokumentasi-only) | historical terarsip |
| Dependency | WP-01.1 | WP-01.1 |
| Owner | Engineering | Engineering |
| Rollback | 1 kelompok dokumen | 1 kelompok dokumen |
| **Target Readiness** | **Engineering Baseline Understood** | **Engineering Baseline Understood** |
| **Exit Gate** | **A2** | **A2** |
| Acceptance | SP-3 | SP-3 |
| Status | **Blocked** | **Blocked** |

### WS-04 — Documentation Traceability

| Attribut | WP-04.1 | WP-04.2 |
|---|---|---|
| Gap | G9-01 | G9-02, G8-03(cross) |
| Tema | matriks end-to-end | checker traceability |
| Input | WP-01.1 (anchor), WP-03.x (objek bersih) | WP-04.1 |
| Output | matriks Mission→Cap→Prog→Release | checker anti-siklik |
| Dependency | WP-01.1, WP-03.x | WP-04.1 |
| Owner | Engineering + Arch review | Engineering |
| Rollback | 1 artifact matriks | 1 checker |
| **Target Readiness** | **Convergence Planned** | **Convergence Planned** |
| **Exit Gate** | **A3** | **A3** |
| Acceptance | SP-4 | SP-4 |
| Status | **Ready** (stlh Q-03) | **Ready** (stlh Q-03) |

### WS-05 — Compliance Normalization

| Attribut | WP-05.1 | WP-05.2 | WP-05.3 |
|---|---|---|---|
| Gap | G10-01, G10-03 | G10-04 | G9-03 |
| Tema | SoT kode check + audit | standardisasi report | readiness checker |
| Input | QA-01 diff, WP-04.x | WP-05.1 | WP-04.x (readiness) |
| Output | 1 SoT kode; 99 audit | report standard | readiness check |
| Dependency | WP-04.x, QA-01 | WP-05.1 | WP-04.x |
| Owner | Engineering | Engineering | Engineering |
| Rollback | 1 kategori check/arsip | 1 kelompok report | 1 checker |
| **Target Readiness** | **Compliance Unified** | **Compliance Unified** | **Compliance Unified** |
| **Exit Gate** | **A5** | **A5** | **A5** |
| Acceptance | SP-5 | SP-5 | SP-5 |
| Status | **Blocked** (QA-01) | **Blocked** (QA-01) | **Blocked** (QA-01) |

### WS-06 — Testing Normalization

| Attribut | WP-06.1 |
|---|---|
| Gap | G10-02 |
| Tema | scope compliance/testing |
| Input | WP-05.x (scope compliance) |
| Output | scope testing tegas (area include/exclude) |
| Dependency | WP-05.x |
| Owner | Software Architect |
| Rollback | 1 scope-area |
| **Target Readiness** | **Architecture Verified** |
| **Exit Gate** | **A6** |
| Acceptance | SP-6 |
| Status | **Blocked** (Architect scope) |

---

## 2. Summary Readiness

| Status | Work Package | Blocker |
|---|---|---|
| **Blocked** | WP-01.1, WP-03.1, WP-03.2, WP-05.1, WP-05.2, WP-05.3, WP-06.1 | Architecture / QA-01 / classify / Architect scope |
| **Ready*** | WP-02.1..06, WP-04.1, WP-04.2 | WP-01.1 (SoT) sbg gerbang |

*`Ready*` = siap dieksekusi begitu WP-01.1 (Architecture Blocker) unblock. Tidak ada WP yang dipaksakan Ready tanpa evidence (konsisten EA-004-007 §5).

---

## 3. Exit Criteria EA-005-002

| Kriteria | Status |
|---|---|
| Setiap WP terdefinisi lengkap | ✅ (15 WP) |
| Input/output/owner/rollback/acceptance ada | ✅ |
| **Target Readiness per WP ada** | ✅ (AP-2A-007) |
| **Exit Gate per WP ada** | ✅ (AP-2A-008) |
| Dependency konsisten dgn WBS | ✅ |
| Status readiness eksplisit | ✅ |
| Repository tetap read-only | ✅ |
| Working tree bersih | ✅ |
| Tanpa commit | ✅ |

---

*— Akhir EA-005-002 Work Package Definition —*
