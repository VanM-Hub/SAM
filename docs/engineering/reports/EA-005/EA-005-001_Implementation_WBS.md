# EA-005-001 — Implementation Work Breakdown Structure (WBS)

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Implementation WBS · **Status:** AUTHORIZED
**Mode:** PLANNING (READ-ONLY) · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini menyusun **Work Breakdown Structure** berbasis seluruh artefak EA-001–EA-004.
> WBS = kontrak kerja resmi Engineering sebelum perubahan pertama pada repository.
> **BUKAN implementasi** — belum mengubah repo, memindah file, menghapus, normalisasi, atau commit.
> Queue (Q-01..06) dari EA-004-007 adalah tulang punggung WBS ini, diperluas ke Work Package (EA-005-002).
>
> **READINESS ALIGNMENT (AP-2A-007/008, 2026-08-08):** WBS kini menyertakan atribut **Readiness Dimension**
> dan **Gate ID (A0–A6)** per Work Package, sesuai model Readiness (SAM Platform Readiness Model v2.0.0 + AP-2A-007/008).
> Pemetaan gate disusun dari review Lead Engineer; konsultasi AP-2A-008 final bila tersedia.
>
> **ARCHITECTURE REVIEW 2026-08-08 (reklasifikasi Historical):** Sesuai keputusan Software Architect, fase Foundation
> (termasuk **EA-006**) resmi **dipensiunkan menjadi Historical**. Seluruh referensi operasional ke "EA-006 Authorization"
> di WBS ini berlaku sebagai **Historical Reference** — bukan gate operasional. Pekerjaan kini berorientasi penuh pada
> **Repository/Compliance/Test Convergence · Legacy/Documentation Convergence · Architecture Baseline Verification**.
> G1-02 → Workstream Repository Convergence · G1-03 → Workstream Documentation Convergence. WBS teknis tidak berubah;
> hanya klasifikasi dua pekerjaan yang berubah (lihat §3).

---

## 1. WBS Structure

WBS mengikuti **2 level eksekusi**: 
- **Level 1 = Workstream (6)** sesuai EA-004-007 §1.
- **Level 2 = Work Package (WP)** — didefinisikan detail di EA-005-002; di sini hanya id + gap + output ringkas.

### Level 1 — Workstream

```
Program A (Foundation Convergence)
├── WS-01 Source of Truth (Q-01) — Architecture Blocker
├── WS-02 Repository Normalization (Q-02)
├── WS-03 Legacy Isolation (Q-03)
├── WS-04 Documentation Traceability (Q-04)
├── WS-05 Compliance Normalization (Q-05)
├── WS-06 Testing Normalization (Q-06)
└── [Gate] Mission Acceptance (SP-6)
```

### Level 2 — Work Package per Workstream

| Work Package | Workstream | Gap Scope | Output Ringkas | Readiness Dimension | Gate ID | Status di WBS |
|---|---|---|---|---|---|---|
| **WP-01.1** | WS-01 | G1-02 | Keputusan SoT roadmap (opsi A/B/C) + klasifikasi docs/core | Engineering Baseline | **A0** | **Blocked** (Architecture) |
| **WP-02.1** | WS-02 | G1-01, G1-03 | Resolusi duplikasi canonical | Repository Baseline | **A1** | Ready |
| **WP-02.2** | WS-02 | G2-01..04 | Resolusi duplikasi engineering | Repository Baseline | **A1** | Ready |
| **WP-02.3** | WS-02 | G3-01..03 | Resolusi orphan | Repository Baseline | **A1** | Ready |
| **WP-02.4** | WS-02 | G6-01..06 | Resolusi repo inconstistency | Repository Baseline | **A1** | Ready |
| **WP-02.5** | WS-02 | G7-01..04 | Resolusi naming | Repository Baseline | **A1** | Ready |
| **WP-02.6** | WS-02 | G8-01, G8-02 | Resolusi dokumentasi inconstistency | Repository Baseline | **A1** | Ready |
| **WP-03.1** | WS-03 | G4-01..03 | Isolasi legacy | Engineering Baseline | **A2** | **Blocked** (classify core) |
| **WP-03.2** | WS-03 | G5-01..03 | Isolasi historical | Engineering Baseline | **A2** | **Blocked** (classify core) |
| **WP-04.1** | WS-04 | G9-01 | Matriks end-to-end Mission→Cap→Prog→Release | Convergence | **A3** | Ready (setelah Q-03) |
| **WP-04.2** | WS-04 | G9-02, G8-03 | Checker traceability | Convergence | **A3** | Ready (setelah Q-03) |
| **WP-05.1** | WS-05 | G10-01, G10-03 | SoT kode check + audit | Compliance | **A5** | **Blocked** (QA-01 diff) |
| **WP-05.2** | WS-05 | G10-04 | Standardisasi report/evidence compliance | Compliance | **A5** | **Blocked** (QA-01) |
| **WP-05.3** | WS-05 | G9-03 | Readiness checker | Compliance | **A5** | **Blocked** (QA-01) |
| **WP-06.1** | WS-06 | G10-02 | Scope compliance/testing | Governance Readiness | **A6** | **Blocked** (Architect) |

**Total:** 6 workstream · **15 work package** · **36 gap** ter-cover (37 slot dgn G8-03 cross-ws).

> **Gate A4 (Legacy Boundary Verified)** dipetakan lintas-workstream (mencakup WP-03.x + kliring overlap WS-02/WS-03 dari
> EA-004-004 §3) — tidak terikat satu WP tunggal; diverifikasi sebagai gate lintas di EA-005-003/005-005.
> **Readiness Dimension per WS (AP-2A-007):** WS-01/WS-03/WS-04 → Engineering Baseline; WS-02 → Repository Baseline;
> WS-05 → Compliance/Developer Readiness; WS-06 → Governance Readiness.

---

## 2. Dependencies (Level-2)

Dependency antar Work Package (dari EA-004-004 §3 + EA-004-005 §7).

| Work Package | Bergantung pada | Menjadi prerequisite utk |
|---|---|---|
| WP-02.x (semua) | WP-01.1 (SoT stabil) | WP-04.x |
| WP-03.x | WP-01.1 (classify core) | WP-04.x, WP-02.x (kliring overlap) |
| WP-04.x | WP-01.1 (anchor), WP-03.x (objek bersih) | WP-05.x |
| WP-05.x | WP-04.x (traceability), QA-01 (diff) | WP-06.x |
| WP-06.1 | WP-05.x (scope compliance) | Mission acceptance |

**Chain kritis:** WP-01.1 → WP-02 → WP-03 → WP-04 → WP-05 → WP-06 → Acceptance.

---

## 3. Milestone Binding (ringkas)

Milestone detail di EA-005-003; di sini WBS menetapkan **3 milestone utama** sbg jangkar.
> **Pasca-reklasifikasi Architecture (2026-08-08):** M-0 tidak lagi "menunggu Foundation Authorization"
> (ea-006 sudah Historical). Awal eksekusi dimulai dari **keputusan Architecture aktif** (klasifikasi normatif artefak),
> bukan dari artefak historis Foundation.

| Milestone | Terikat Work Package | Kondisi |
|---|---|---|
| **M-0 Unblock** | WP-01.1, QA-01, klasifikasi core | Keputusan Architecture aktif (klasifikasi normatif artefak) |
| **M-1 Structure Stable** | WP-02.1..06 (selesai) | Struktur repo konsisten; 0 duplikasi |
| **M-2 Isolated** | WP-03.1..02 (selesai) | Legacy/historical terisolasi |
| **M-3 Traceable** | WP-04.1/04.2 (selesai) | Matriks + checker tersedia |
| **M-4 Compliance Valid** | WP-05.1..03 | SoT kode + 99 audit + readiness |
| **M-5 Test Scoped** | WP-06.1 | Scope testing tegas |
| **M-6 Acceptance** | Mission gate | Program A accepted |

---

## 4. Ownership (ringkas)

Detail di EA-005-004; jangkar authority per workstream tetap dari EA-004-005 §6 & EA-004-006 §4.

| Workstream | Owner | Keputusan | Acceptance |
|---|---|---|---|
| WS-01 | Software Architect | SoT + docs/core | Mission |
| WS-02 | Engineering | normalisasi | Mission (via SP) |
| WS-03 | Engineering | legacy isolation | Mission |
| WS-04 | Engineering + Arch review | matriks form | Mission |
| WS-05 | Engineering | compliance kode | Mission |
| WS-06 | Software Architect | scope testing | Mission |

---

## 5. Verification Hook

Setiap Work Package pada WBS wajib punya **verification hook** (diisi di EA-005-005): output harus dapat diverifikasi eksekusi (EA-LL-001), bukan asumsi statis.

| Work Package | Verification Hook (bukti eksekusi) |
|---|---|
| WP-01.1 | dokumen SoT terpilih + glossary terupdate |
| WP-02.x | per batch: 0 duplikasi; rujukan valid (semantic diff) |
| WP-03.x | per kelompok: legacy tidak di jalur aktif; rujukan balik PASSED |
| WP-04.x | matriks + checker lulus (anti-siklik) |
| WP-05.x | diff 99==99 + audit 99 PASSED + readiness checker |
| WP-06.1 | scope area tes dgn contoh pass/fail |

---

## 5A. Readiness Pipeline (AP-2A-007/008)

Pipeline acceptance diperbarui dari 3-tahap menjadi **5-tahap** (Add Readiness), tanpa ubah teknis implementasi:

```
Deliverable ─▶ Evidence ─▶ Verification ─▶ Readiness ─▶ Acceptance
```

| Tahap | Definisi |
|---|---|
| Deliverable | output WP diproduksi |
| Evidence | artefak eksekusi (hash, count, diff, audit trail) dihasilkan |
| Verification | evidence diverifikasi (V1-V4, EA-005-005 §1) |
| **Readiness** | readiness dimension dinilai terhadap target (AP-2A-007 / Platform Readiness Model) |
| Acceptance | gate ditutup oleh authority (Milestone / Mission) |

> Setiap WP pada WBS di atas ditutup hanya bila **kelima tahap** tuntas — ini meningkatkan objektivitas
> acceptance tanpa mengubah urutan/ruang lingkup implementasi.

---

## 6. Exit Criteria EA-005-001

| Kriteria | Status |
|---|---|
| WBS terdefinisi | ✅ (6 WS, 15 WP, 36 gap) |
| Dependency terpetakan | ✅ (§2, chain kritis) |
| Milestone binding tersedia | ✅ (§3) |
| Ownership terkait | ✅ (§4) |
| Verification hook terpetakan | ✅ (§5) |
| **Readiness Dimension tercakup** | ✅ (kolom di §1; AP-2A-007) |
| **Gate ID (A0–A6) tercakup** | ✅ (kolom di §1; AP-2A-008) |
| **Readiness pipeline terdefinisi** | ✅ (§5A) |
| **Referensi EA-006 = Historical (bukan gate operasional)** | ✅ (header + §3) |
| **Reklasifikasi G1-02 → Repository Convergence** | ✅ (header, WS-01/WS-02) |
| **Reklasifikasi G1-03 → Documentation Convergence** | ✅ (header, WP-02.1) |
| Repository tetap read-only | ✅ |
| Working tree bersih | ✅ |
| Tanpa commit | ✅ |

---

*— Akhir EA-005-001 Implementation WBS —*
