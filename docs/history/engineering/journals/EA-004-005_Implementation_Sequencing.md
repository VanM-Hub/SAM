# EA-004-005 — Implementation Sequencing

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Implementation Sequencing · **Status:** AUTHORIZED
**Mode:** 100% READ-ONLY · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini menyusun **urutan implementasi deterministik** Program A berdasarkan seluruh evidence
> EA-001 sampai EA-004. **BUKAN WBS rinci / bukan implementasi teknis / bukan pemilihan SoT.**
> Urutan yang dihasilkan: deterministic · dependency-safe · rollback-aware · evidence-driven · dapat diaudit.
>
> **Label:** aturan sequencing diri bentuk **Engineering Execution Rules** (reusable — dapat dipakai pada program konvergensi berikutnya, bukan khusus Program A).

---

## 1. Workstream Identification

Pengelompokan seluruh **36 Gap ID** (verifikasi: 36/36 ter-cover, tidak ada yang tertinggal) ke workstream logis. G8-03 bersifat **cross-cutting** (muncul di WS-01 & WS-04).

| Workstream | Gap ID | Jumlah | Tema (evidence) |
|---|---|---|---|
| **WS-01 Source of Truth** | G1-02, G8-03 | 2 (1 unik + cross-cutting) | Resolusi klaim SoT roadmap & konsistensi istilah SoT (QA-06, QA-07) |
| **WS-02 Repository Normalization** | G1-01, G1-03, G2-01, G2-02, G2-03, G2-04, G3-01, G3-02, G3-03, G6-01, G6-02, G6-03, G6-04, G6-05, G6-06, G7-01, G7-02, G7-03, G7-04, G8-01, G8-02 | 21 | Duplicate/orphan/naming/repo-structure (konsolidasi & klasifikasi) |
| **WS-03 Legacy Isolation** | G4-01, G4-02, G4-03, G5-01, G5-02, G5-03 | 6 | Isolasi legacy & historical (EA-004-003 input) |
| **WS-04 Documentation Traceability** | G9-01, G9-02, G8-03(**) | 3 | Matriks end-to-end Mission→Capability→Program→Release (QA-03, QA-04) |
| **WS-05 Compliance Normalization** | G10-01, G10-03, G10-04, G9-03 | 4 | Resolusi SoT kode check, audit eksekusi, readiness checker (QA-01, QA-02, QA-05) |
| **WS-06 Testing Normalization** | G10-02 | 1 | Petakan area compliance & pertegas scope testing |

> (**) G8-03 = **Cross-Workstream Dependency** (label eksplisit): mempengaruhi WS-01 (istilah SoT) DAN WS-04 (terminologi navigasi traceability). Bukan duplikasi pekerjaan — satu dependency yang berdampak lintas workstream.

**Ringkasan:** 36 gap = WS-01(2) + WS-02(21) + WS-03(6) + WS-04(3, incl. cross) + WS-05(4) + WS-06(1). Total 37 slot karena G8-03 cross-cutting.

---

## 2. Engineering Execution Rules

Aturan formal penyusunan urutan (berasal dari evidence EA sebelumnya). **Label: Engineering Execution Rules** — reusable untuk program konvergensi berikutnya, bukan hanya Program A.

| # | Aturan | Sumber evidence |
|---|---|---|
| **R1** | **Upstream sebelum downstream** | EA-004-004 §3 (topologis: Foundation→Spec→ADR→Arch→Runtime→Comp→Testing) |
| **R2** | **Blocker sebelum dependent** | EA-004-004 §5 (SoT G1-02 = gerbang tersembunyi; QA dependency) |
| **R3** | **Classification sebelum modification** | EA-004-001 P-02 (classify-before-archive); EA-004-003 (Unknown tidak diisolasi) |
| **R4** | **Verification sebelum acceptance** | EA-LL-001 (eksekusi langsung sebelum menyimpulkan); prinsip Program A |
| **R5** | **Evidence over Opinion** | semua EA; QA-01 perlu verify 99==99 via diff, bukan klaim |
| **R6** | **Tidak ada cycle → urutan topologis aman** | EA-004-004 §4 (No Circular Dependency Found) |
| **R7** | **Keputusan di luar kewenangan Engineering → gate** | G1-02 = Architecture Blocking Decision (catatan Engineering EA-004-004) |
| **R8** | **Workstream paralel wajib input/output/sync point** | catatan Engineering EA-004-004 §Parallelization |

---

## 3. Execution Phases

Fase implementasi (objective · workstream · prerequisite · expected output). **Bukan detail teknis.**

| Fase | Objective | Workstream | Prerequisite | Expected Output |
|---|---|---|---|---|
| **Phase 0** | Menetapkan keputusan SoT & baseline klasifikasi | WS-01 (G1-02), klasifikasi docs/core | — | 1 SoT/domain ditetapkan (Architect); status docs/core final |
| **Phase 1** | Normalisasi struktur repositori (dedupe, naming, orphan) | WS-02 (21 gap) | Phase 0 (SoT stabil) | Struktur repositori konsisten; 0 duplicate aktif; naming tunggal |
| **Phase 2** | Isolasi legacy & historical | WS-03 (6 gap) | Phase 0 (classify), Phase 1 (area aktif bersih) | Legacy/historical di area history; tidak di jalur aktif |
| **Phase 3** | Bangun traceability end-to-end | WS-04 (G9-01/02) | Phase 0 (SoT, traceability punya anchor), Phase 2 (objek traceable bersih) | Matriks Mission→Capability→Program→Release + checker |
| **Phase 4** | Normalisasi compliance + readiness checker | WS-05 (G10, G9-03) | Phase 3 (traceability sbg basis), QA-01 diff | 1 SoT kode check; audit eksekusi 99 PASSED; readiness checker |
| **Phase 5** | Normalisasi testing & scope compliance | WS-06 (G10-02) | Phase 4 | Scope testing tegas; compliance area terpetakan |

> Urutan fase mengikuti **Engineering Normalization Order** (EA-004-004 §3).

---

## 4. Synchronization Points

Titik sinkronisasi wajib antar workstream. Setiap SP memiliki **Entry Condition + Entry Evidence** dan **Exit Condition + Exit Evidence** (agar Mission dapat acceptance berbasis artefak).

### SP-1 .. SP-6

| SP | Workstream disinkronkan | Entry Condition / Entry Evidence | Exit Condition / Exit Evidence |
|---|---|---|---|
| **SP-1** | WS-01 → semua | SoT belum ditetapkan / 2+ klaim SoT (G1-02) | 1 SoT/domain final; istilah konsisten / dokumen SoT terpilih + glossary updated (QA-06/07) |
| **SP-2** | WS-01 → WS-04 | Traceability butuh anchor / belum ada anchor tunggal | SoT + klasifikasi core final / status docs/core terdokumentasi |
| **SP-3** | WS-03 → WS-04 | Isolasi legacy selesai / legacy masih di area aktif | Tidak ada legacy di jalur aktif / verifikasi rujukan balik PASSED |
| **SP-4** | WS-04 → WS-05 | Compliance butuh traceability / matriks belum ada | Matriks+checker traceability / matriks PASSED |
| **SP-5** | WS-05 → WS-06 | Testing butuh scope compliance / scope ambiguous | 1 SoT kode; audit 99 / diff 99==99 + hasil PASSED |
| **SP-6** | Verification gate | Sebelum acceptance fase / status unknown | Eksekusi PASSED / verifikasi evidence |

> **Prinsip rollback terkait SP (catatan Engineering):** **Rollback Boundary TIDAK boleh melintasi Synchronization Point yang telah di-accept.** Rollback hanya berlaku di dalam fase aktif; setelah sebuah SP diterima, pemulihan harus lewat prosedur baru, bukan membatalkan fase yang sudah ditutup. Ini menjaga determinisme Program A.

---

## 5. Rollback Boundaries

Batas rollback alami per fase (implementasi bisa dihentikan tanpa repo ambigu).

| Fase | Rollback Boundary | Alasan (mencegah state ambigu) |
|---|---|---|
| **Phase 0** | Sebelum klasifikasi dipublikasi | Keputusan Architecture reversible; belum ada perubahan repo |
| **Phase 1** | Per-batch dedupe/naming (revert per perubahan) | Memindahkan/gabung file: batas = per kelompok artefak, bukan satu fase utuh |
| **Phase 2** | Sebelum legacy dipindah final | Isolasi = pemindahan + verifikasi rujukan; rollback = kembalikan lokasi bila rujukan putus |
| **Phase 3** | Sebelum matriks diuji | Traceability matrix anti-siklik; rollback bila checker tidak lulus |
| **Phase 4** | Sebelum `_placeholders.py` diarsip | Jangan hapus—arsip dulu; rollback = pulihkan deklarasi |
| **Phase 5** | Setelah scope testing disepakati | Perubahan scope testing; rollback = kembalikan scope lama |

**Prinsip (dari EA-004-003 §6):** isolasi = pemindahan ≠ penghapusan; verifikasi balik; klasifikasi asal terdokumentasi.

---

## 6. Authority Gates

Keputusan per fase berada di: **Engineering · Software Architect · Mission**.

| Fase | Keputusan kunci | Authority | Alasan |
|---|---|---|---|
| **Phase 0** | Pilih SoT roadmap (G1-02 — opsi A/B/C); klasifikasi docs/core | **Software Architect** | AP-2A: keputusan arsitektur & SoT = Architecture Authority; G1-02 TETAP Architecture Blocking Decision (NOT engineering task) |
| **Phase 1** | Normalisasi struktur/naming repository | **Engineering** | Operasional repositori; dalam kewenangan engineering |
| **Phase 2** | Isolasi legacy | **Engineering** | Klasifikasi + pemindahan dgn evidence; verifikasi engineering |
| **Phase 3** | Matriks traceability | **Engineering + Architect review** | Desain matriks di engineering; form final = keputusan arsitektur |
| **Phase 4** | SoT kode check (catalog Builder) | **Engineering** | Resolusi teknis katalog; verifikasi eksekusi |
| **Phase 5** | Scope compliance/testing | **Software Architect** | Batas lingkup compliance lintas area |

> **Mission gate:** seluruh fasa dijalankan dalam lingkup **Program A (Foundation Convergence)** sesuai MISSION-2A. Tidak ada fase yang mengubah misi/roadmap intrinsik tanpa persetujuan Mission.

---

## 7. EA-005 Input

### 7.1 Urutan final
`Phase 0 (WS-01 SoT) → Phase 1 (WS-02 Normalisasi) → Phase 2 (WS-03 Legacy) → Phase 3 (WS-04 Traceability) → Phase 4 (WS-05 Compliance) → Phase 5 (WS-06 Testing)`

### 7.2 Dependency final
- Rantai topologis: Foundation → Spec → ADR → Arch → Runtime → Compliance → Testing (EA-004-004 §3).
- SoT (G1-02) = **blocker utama** di Phase 0 (harus selesai dulu).
- Legacy/Vendor/Engineering/Release/Documentation = leaf parallel (tidak memblokir fase utuh).

### 7.3 Blocker Architecture
- **G1-02** (SoT roadmap — opsi A/B/C) → Phase 0, keputusan Software Architect.
- Klasifikasi final `docs/core/*` (Unknown) → Phase 0.

### 7.4 Blocker Engineering
- **QA-01** diff 99==99 (`_placeholders.py` vs Builder) → sebelum QA-02 audit.
- Klasifikasi legacy lengkap → sebelum Phase 2 isolasi.

### 7.5 Peluang paralelisasi
- **Phase 1∥**: WS-02 (21 gap) bisa dipecah per-batch (dedupe, naming, orphan) paralel — dengan sync point per batch.
- **Phase 3∥ Phase 4 sebagian**: traceability matrix (G9-01/02) bisa paralel dengan audit compliance builder (QA-02) — asal SP-4 diterapkan (matrix jadi input compliance).
- **Embedded leaf parallel**: Vendor, Engineering/Roadmap, Release normalize bisa jalan paralel di sela-sela fase — dengan input/output/sync point (R8).

### 7.6 Evidence yang harus diwariskan
| Evidence | Asal | Dipakai oleh |
|---|---|---|
| 36 Gap ID + severity | EA-001 | WS-01..06 |
| Revision severity (G10→Medium) | EA-003 | WS-05 |
| QA-01..07 queue | EA-003-ANNEX-A | semua |
| Legacy classification (Archived/Dormant/Unknown) | EA-004-003 | WS-03 |
| Engineering Normalization Order | EA-004-004 §3 | semua |
| No Circular Dependency Found | EA-004-004 §4 | sequencing safety |
| Critical path + SoT gate | EA-004-004 §5 | Phase 0 |
| Snapshot baseline (canonical=88 dll.) | EA-004-001 §1 | perbandingan hasil |

---

## 8. Batasan (Larangan EA-004-005 — dipatuhi)

- ❌ Tidak membuat WBS rinci (itu EA-005)
- ❌ Tidak memilih Source of Truth
- ❌ Tidak memindahkan artefak
- ❌ Tidak mengubah repository
- ❌ Tidak mengubah Architecture
- ❌ Tidak menentukan implementasi teknis
- ✅ Hanya menetapkan urutan eksekusi

---

## 9. Exit Criteria EA-004-005

| Kriteria | Status |
|---|---|
| Seluruh workstream teridentifikasi | ✅ (WS-01..06; 36 gap ter-cover) |
| Aturan sequencing terdokumentasi | ✅ (§2, 8 aturan) |
| Execution phases lengkap | ✅ (§3, Phase 0-5) |
| Synchronization points tersedia | ✅ (§4, SP-1..6) |
| Rollback boundaries tersedia | ✅ (§5) |
| Authority gates lengkap | ✅ (§6) |
| Input EA-005 lengkap | ✅ (§7) |
| Repository tetap read-only | ✅ |
| Working tree bersih | ✅ (cek git status) |
| Tanpa commit | ✅ |

---

*— Akhir EA-004-005 Implementation Sequencing —*
