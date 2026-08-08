# EA-004-007 — EA-005 Execution Queue

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** EA-005 Execution Queue (penutup fase EA-004) · **Status:** AUTHORIZED
**Mode:** 100% READ-ONLY · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini menyusun **Execution Queue final** yang menjadi masukan langsung EA-005 (Implementation WBS),
> sekaligus **penutup seluruh fase EA-004**. Queue: deterministic · dependency-safe · authority-aware ·
> rollback-aware · evidence-based. **BUKAN WBS / bukan task implementasi / bukan pilih SoT / bukan ubah repo.**
> EA-005 dapat memulai tanpa perlu membaca ulang seluruh EA-001–EA-004 (hand-off package lengkap, §6).
>
> **ARCHITECTURE REVIEW 2026-08-08 (reklasifikasi — Development SAM 2.x):** Sesuai keputusan Software Architect,
> fase Foundation **dipensiunkan menjadi Historical**. Dua gap yang sebelumnya termasuk gate Foundation kini
> diperlakukan sebagai **pekerjaan normalisasi repository aktif** (Development SAM 2.x):
> - **G1-02 → WS Repository Convergence** (bukan lagi "izin implementasi Foundation").
> - **G1-03 → WS Documentation Convergence** (EXECUTION_MODEL.md & THINKING_PROTOCOL.md = objek klasifikasi dokumentasi).
> Reklasifikasi ini **tidak mengubah** dependency, sequencing, rollback, verification, atau readiness. Status
> artefak EA-004 (CLOSED) tetap; catatan ini bersifat administratif/planning.

---

## 0. Execution Context Summary

Halaman pembuka agar Lead Engineer / Engineer baru memahami konteks TANPA membuka seluruh dokumen.

| Konteks | Ringkasan |
|---|---|
| **Tujuan Program A** | Foundation Convergence (Program A / MISSION-2A): menyatukan fondasi dokumen & repositori SAM ke satu state deterministik, dependency-safe, authority-aware, rollback-aware, evidence-based. |
| **Status EA-001..004** | EA-001 (mapping+gap, 36 gap) ✅ · EA-002 (normalization plan) ✅ · EA-003 (compliance+traceability+SoT classification) ✅ · EA-004 (planning: convergence, SoT impact, legacy, dependency graph, sequencing, rollback, execution queue) ✅ **CLOSED** |
| **Blocker aktif** | **Architecture**: G1-02 (Source of Truth) + klasifikasi `docs/core`. **Engineering Evidence**: QA-01 (diff 99==99) + evidence tambahan. **Mission Acceptance**: acceptance akhir Program A. |
| **Authority** | Software Architect (SoT, docs/core, scope testing) · Engineering (normalisasi, legacy, compliance, tracing, rollback implementasi) · Mission (acceptance akhir). *Rollback Authority ≠ Acceptance Authority.* |
| **Urutan workstream** | Q-01 SoT → Q-02 Normalisasi → Q-03 Legacy → Q-04 Traceability → Q-05 Compliance → Q-06 Testing (identik Phase 0-5). |

> **Referensi cepat:** seluruh detail ada di EA-004-001..007; 36 Gap ID di EA-001; QA-01..07 di EA-003-ANNEX-A.

---

---

## 1. Queue Overview

Ringkasan seluruh workstream + jumlah Gap ID + authority + blocker + prerequisite.

| WS | Nama | Gap ID | #Gap | Authority | Blocker | Prerequisite |
|---|---|---|---|---|---|---|
| **WS-01** | Source of Truth | G1-02, G8-03 | 2 | Software Architect | Architecture Blocking Decision (G1-02) | EA-003-003 opsi A/B/C |
| **WS-02** | Repository Normalization | G1-01/03, G2-01/02/03/04, G3-01/02/03, G6-01..06, G7-01..04, G8-01/02 | 21 | Engineering | — | Phase 0 (SoT stabil) |
| **WS-03** | Legacy Isolation | G4-01/02/03, G5-01/02/03 | 6 | Engineering | klasifikasi docs/core | Phase 0 (classify) |
| **WS-04** | Documentation Traceability | G9-01/02 + G8-03(cross) | 3 | Engineering + Arch review | — | Phase 0 (anchor), Phase 2 (objek bersih) |
| **WS-05** | Compliance Normalization | G10-01/03/04, G9-03 | 4 | Engineering | QA-01 diff 99==99 | Phase 3 (traceability) |
| **WS-06** | Testing Normalization | G10-02 | 1 | Software Architect | — | Phase 4 (scope compliance) |

**Total:** 36 gap (37 slot — G8-03 = **Cross-Workstream Dependency**, WS-01 & WS-04).

---

## 2. Ordered Execution Queue

Queue final — urutan **identik dengan sequencing EA-004-005** (Phase 0→5), berbasis Engineering Normalization Order (EA-004-004 §3).

| Queue ID | Workstream | Fase | Gap ID | Dependency | Sync Point | Authority | Target EA |
|---|---|---|---|---|---|---|---|
| **Q-01** | WS-01 SoT | Phase 0 | G1-02, G8-03 | EA-003-003 (opsi) | SP-1 | Software Architect | EA-005 |
| **Q-02** | WS-02 Normalisasi | Phase 1 | G1-01/03, G2-01..04, G3-01..03, G6-01..06, G7-01..04, G8-01/02 | Q-01 (SoT stabil) | SP-2 | Engineering | EA-005 |
| **Q-03** | WS-03 Legacy | Phase 2 | G4-01..03, G5-01..03 | Q-01 (classify core) | SP-3 | Engineering | EA-005 |
| **Q-04** | WS-04 Traceability | Phase 3 | G9-01/02, G8-03 | Q-01 (anchor), Q-03 (objek bersih) | SP-4 | Engineering + Arch | EA-005 |
| **Q-05** | WS-05 Compliance | Phase 4 | G10-01/03/04, G9-03 | Q-04 (traceability), QA-01 diff | SP-5 | Engineering | EA-005 |
| **Q-06** | WS-06 Testing | Phase 5 | G10-02 | Q-05 (scope compliance) | SP-6 | Software Architect | EA-005 |

> **Engine Execution Rules** (EA-004-005 §2) berlaku: upstream→downstream, blocker→dependent, classify→modify, verify→accept. Urutan Q-01..Q-06 identik dgn Phase 0-5.

---

## 3. Blocking Queue

Pisahkan queue yang **menunggu keputusan** (TIDAK dicampur dengan queue implementasi aktif).

### 3.1 Menunggu keputusan Software Architect
| Queue | Gap | Menunggu | Blocker |
|---|---|---|---|
| Q-01 | G1-02, G8-03 | Keputusan SoT roadmap (opsi A/B/C) + klasifikasi docs/core | **Architecture Blocking Decision** — bukan engineering task (EA-004-004 §5) |
| Q-06 | G10-02 | Penegasan scope compliance/testing lintas area | Software Architect |

### 3.2 Menunggu Mission
| Queue | Menunggu | Catatan |
|---|---|---|
| (acceptance) | Acceptance Program A | Mission = acceptance authority; bukan rollback (Rollback Authority ≠ Acceptance Authority — EA-004-006 §6) |

### 3.3 Menunggu evidence baru
| Queue | Gap | Menunggu evidence |
|---|---|---|
| Q-05 | G10-01/03 | **QA-01**: diff 99==99 (`_placeholders.py` vs Builder) sebelum QA-02 audit |
| Q-03 | G4/G5 | klasifikasi legacy lengkap (dari Q-01/Phase 0) |

---

## 4. Parallel Queue

Identifikasi queue yang boleh berjalan paralel (dependency + sync point + conflict risk).

| Queue paralel | Dependency | Sync Point | Conflict Risk |
|---|---|---|---|
| **Q-02 (WS-02)** dipecah per-batch | per batch independen dlm WS-02 | SP-2 (keluar Phase1) | rendah — batch kecil; perlu sync point per batch |
| **Q-03 (WS-03)** ∥ **Q-02** (bagian leaf) | Q-01 (classify) selesai dulu | SP-3 | rendah — legacy vs normalisasi area berbeda; awasi overlap docs/core |
| **Q-04 ∥ Q-05 (sebagian)** | Q-04 matriks selesai sj | SP-4 → Q-05 | q-05 audit compliance butuh matriks traceability sbg basis (SP-4) |
| **Leaf parallel** (Vendor, Engineering/Roadmap, Release, Documentation/Templates/User) | terisolasi (EA-004-004 §6) | masing-masing SP di cluster leaf | sangat rendah |

> **Aturan (R8, EA-004-005 §2):** setiap workstream paralel wajib punya **input, output, sync point** — deterministik.

---

## 5. Execution Readiness

Setiap queue harus punya: input · output · owner · rollback boundary · acceptance target. Queue belum lengkap → **Not Ready** (tidak dipaksakan).

| Queue | Input | Output | Owner | Rollback Boundary | Acceptance Target | Status |
|---|---|---|---|---|---|---|
| **Q-01** | EA-003-003 opsi SoT; klasifikasi core | 1 SoT/domain final; istilah konsisten | Software Architect | 1 keputusan (revisable), sblm publikasi | SP-1 exit | **Not Ready** — menunggu keputusan Architect (blocking) |
| **Q-02** | Q-01 (SoT stabil) | Struktur repo konsisten; 0 duplikasi; naming tunggal | Engineering | 1 batch normalisasi | SP-2 exit | Ready |
| **Q-03** | Q-01 (classify core) | Legacy/historical terisolasi; rujukan balik PASSED | Engineering | 1 kelompok dokumen | SP-3 exit | **Not Ready** — menunggu klasifikasi core |
| **Q-04** | Q-01, Q-03 | Matriks Mission→Cap→Prog→Release + checker | Engineering + Arch | 1 artifact matriks | SP-4 exit | Ready (setelah Q-03) |
| **Q-05** | Q-04, QA-01 diff | 1 SoT kode; audit 99; readiness checker | Engineering | 1 kategori check / arsip | SP-5 exit | **Not Ready** — menunggu QA-01 diff |
| **Q-06** | Q-05 | Scope compliance/testing tegas | Software Architect | 1 scope-area | SP-6 exit | **Not Ready** — keputusan scope Architect |

**Ringkasan readiness:** Q-02 & Q-04 **Ready**; Q-01, Q-03, Q-05, Q-06 **Not Ready** (blocker keputusan/evidence). Bloom blocker = Q-01 & QA-01 (harus unblock dulu agar jalur utama terbuka).

---

## 6. EA-005 Hand-off Package

Artefak yang diwariskan → EA-005 bisa mulai TANPA baca ulang seluruh EA-001–004.
> **Pasca-reklasifikasi (2026-08-08):** G1-02 kini menandai **Repository Convergence**, G1-03 menandai
> **Documentation Convergence** (Development SAM 2.x), bukan gate Foundation Authorization.

| Kategori | Isi | Referensi evidence |
|---|---|---|
| **Workstream** | WS-01..06 + G8-03 cross-ws | EA-004-005 §1 |
| **Sequencing** | Engineering Execution Rules (8) + Phase 0-5 + urutan final | EA-004-005 §2-3 |
| **Rollback** | Model: unit, trigger T1-5, boundary matrix, evidence preservation; prinsip "restores state, never removes evidence"; **Rollback ≠ Acceptance** | EA-004-006 §1-7 |
| **Authority** | Gate: Architect (SoT/core/scope/testing) · Engineering (norm/legacy/compliance) · Mission (acceptance) | EA-004-005 §6, EA-004-006 §4 |
| **Dependency** | Engineering Normalization Order + No Circular Dependency Found + critical path (Foundation→Spec→ADR→Arch→Runtime→Comp→Testing) + SoT gate | EA-004-004 §3-5 |
| **Blocker** | Architecture: G1-02 + docs/core (Q-01). Engineering: QA-01 diff (Q-05). | EA-004-005 §7, EA-004-003 |
| **Lessons Learned** | EA-LL-001 (execute-to-verify) · EA-LL-002 (terminology ≠ dependency; only explicit reference/include/canonical/traceable) | 03_ISSUES.md |
| **Evidence refs** | 36 Gap ID (EA-001) · severity revisi (EA-003) · QA-01..07 (EA-003-ANNEX-A) · legacy classification (EA-004-003) | EA-001/003/004 |

---

## 7. Batasan (Larangan EA-004-007 — dipatuhi)

- ❌ Tidak membuat WBS
- ❌ Tidak membuat task implementasi
- ❌ Tidak mengubah prioritas
- ❌ Tidak memilih Source of Truth
- ❌ Tidak mengubah repository
- ❌ Tidak mengubah Architecture
- ✅ Hanya menyusun queue eksekusi final

---

## 8. Exit Criteria EA-004-007

| Kriteria | Status |
|---|---|
| Queue final lengkap | ✅ (§1-2, Q-01..06; 36 gap ter-cover) |
| Blocking queue terpisah | ✅ (§3: Architecture/Mission/evidence) |
| Parallel queue terdokumentasi | ✅ (§4) |
| Readiness diverifikasi | ✅ (§5) |
| Hand-off package lengkap | ✅ (§6) |
| Seluruh dependency konsisten | ✅ (identik EA-004-005 §7) |
| **Reklasifikasi G1-02 → Repository Convergence** | ✅ (header, §6) |
| **Reklasifikasi G1-03 → Documentation Convergence** | ✅ (header, §6) |
| Repository tetap read-only | ✅ |
| Working tree bersih | ✅ |
| Tanpa commit | ✅ |

---

## 9. Status EA-004

Dengan EA-004-007 diterima, **EA-004 (Planning Phase) dinyatakan CLOSED.** Engineering dapat lanjut ke **EA-005 (Implementation Work Breakdown Structure)** menggunakan seluruh deliverable EA-004 sebagai dasar resmi tanpa analisis ulang.

**Deliverable EA-004 (7):** 001 Convergence Plan · 002 SoT Impact Matrix · 003 Legacy Isolation Plan · 004 Normalization Dependency Graph · 005 Implementation Sequencing · 006 Rollback Matrix · 007 EA-005 Execution Queue.

---

*— Akhir EA-004-007 EA-005 Execution Queue · Penutup Fase EA-004 —*
