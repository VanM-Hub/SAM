# EA-005-005 — Verification & Acceptance Plan

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Verification & Acceptance Plan · **Status:** AUTHORIZED
**Mode:** PLANNING (READ-ONLY) · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini menetapkan **bagaimana setiap Work Package diverifikasi** (bukti eksekusi, bukan asumsi)
> dan **siapa yang menerima** (acceptance). Mengikuti **EA-LL-001** (execute-to-verify), **EA-LL-002**
> (terminology ≠ dependency; hanya explicit reference/include/canonical/traceable yg dihitung),
> & **Rollback ≠ Acceptance** (EA-004-006 §6).
> **BUKAN prosedur teknis akhir** — ini kerangka verifikasi/acceptance berbasis evidence.

---

## 1. Verification Principles

| Prinsip | Aturan |
|---|---|
| **V1** | Verifikasi = **eksekusi**, bukan inspeksi statis (EA-LL-001) |
| **V2** | Hanya **explicit reference / include / canonical declaration / traceable relation** dihitung sbg dependency (EA-LL-002) |
| **V3** | Evidence **deterministik**: hash, count, diff, semantic diff — tanpa kata "kemungkinan/kandidat" |
| **V4** | Setiap WP punya **verification hook** (EA-005-001 §5) yg menghasilkan artefak audit |

---

## 2. Verification Plan per Work Package

| WP | Verification Method | Bukti (evidence) | Pass Criteria |
|---|---|---|---|
| **WP-01.1** (SoT) | document review + konfirmasi canonical | dokumen SoT terpilih + glossary | 1 SoT/domain; istilah konsisten |
| **WP-02.1..06** | semantic diff + reference check per batch | per batch: grep ref valid + diff | 0 duplikasi; rujukan valid; naming tunggal |
| **WP-03.1..02** | eksekusi reference-back scan | grep: legacy tidak direferensikan jalur aktif | rujukan balik PASSED; terisolasi |
| **WP-04.1..02** | anti-cyclic checker + matriks verifikasi | jalankan checker traceability | matriks + checker PASSED |
| **WP-05.1..03** | diff + audit eksekusi | QA-01 diff 99==99; audit 99 | 1 SoT kode; 99 PASSED; readiness |
| **WP-06.1** | scope test include/exclude | contoh pass/fail per area | scope tegas, non-ambigu |

> Semua verification memakai **execution artifact** (dijalankan), bukan klaim statis — konsisten EA-LL-001.

---

## 2A. Readiness Verification (AP-2A-007/008)

Ditambahkan sebagai tahap sebelum Acceptance untuk setiap WP/milestone. Readiness dinilai terhadap
target **Readiness Dimension** (AP-2A-007) dan **Gate** (AP-2A-008).

| Readiness Dimension | Verifikasi Readiness | Gate | Promosi |
|---|---|---|---|
| Architecture Approved | Keputusan SoT + klasifikasi core terdokumentasi | A0 | M-0 |
| Repository Baseline | Struktur repo konsisten; 0 duplikasi | A1 | M-1 |
| Engineering Baseline Understood | Legacy/historical terkarakterisasi & terisolasi | A2 | M-2 |
| Convergence Planned | Matriks traceability anti-siklik | A3 | M-3 |
| Legacy Boundary Verified | Overlap canon/legacy cleared | A4 | M-3a |
| Compliance Unified | 1 SoT kode + 99 audit + readiness checker | A5 | M-4 |
| Architecture Verified | Scope testing tegas | A6 | M-5 |
| Platform Readiness Gate 2 | Program A accepted + readiness evidence lengkap | Final | M-6 |

> Alur WP: **Production → Evidence → Verification (V1-V4) → Readiness Verification (atas) → Acceptance (gate).**
> Readiness Verification memastikan tiap deliverable tidak hanya benar secara teknis (verification)
> tetapi juga **mencapai target kesiapan** (readiness) sebelum gate acceptance ditutup.

---

## 3. Acceptance Plan

Acceptance berbasis **milestone gate** (EA-005-003 §3). Setiap milestone: **exit evidence SP** + **Readiness Gate** + **authority penutup**.

| Milestone | Readiness Gate | Acceptance evidence | Authority | Sync Point |
|---|---|---|---|---|
| M-0 | A0 | SoT + core klasifikasi + QA-01 | Software Architect | SP-1 |
| M-1 | A1 | verification batch PASSED + readiness repo baseline | Engineering | SP-2 |
| M-2 | A2 | reference-back PASSED + readiness eng-baseline | Engineering | SP-3 |
| M-3 | A3 | matriks + checker PASSED + readiness convergence | Engineering + Arch review | SP-4 |
| M-3a | A4 | overlap cleared + batas legacy tegas | Engineering + Arch review | SP-4 |
| M-4 | A5 | 99 audit + readiness checker + readiness compliance | Engineering | SP-5 |
| M-5 | A6 | scope test tegas + readiness governance | Software Architect | SP-6 |
| M-6 | Final | **Program A accepted** + readiness evidence | **Mission** | acceptance |

> **Penegasan (EA-004-006 §6):** Engineering dapat memutuskan **rollback** implementasi (menggagalkan M-x) — itu TIDAK sama dengan **acceptance**. Hanya **Mission** yang menutup M-6 / acceptance akhir Program A.

---

## 3A. Readiness Pipeline Lengkap

Untuk tiap gate, acceptance hanya ditutup setelah pipeline berikut tuntas:
```
Deliverable → Evidence → Verification → Readiness Verification → Acceptance
```
- **Verification** = terbukti benar secara teknis (V1-V4).
- **Readiness** = terbukti mencapai target dimensi kesiapan (AP-2A-007) pada gate (AP-2A-008).
- **Acceptance** = gate ditutup oleh authority (Engineer/Mission).

---

## 4. Evidence Preservation

Setelah verifikasi & acceptance, seluruh evidence wajib dipertahankan (EA-004-006 §5):
- Gap ID · Mapping QA · Traceability · Verification result · Audit trail.
> **Prinsip:** *Rollback restores repository state, never removes engineering evidence.*

---

## 5. Exit Criteria EA-005-005

| Kriteria | Status |
|---|---|
| Verification plan lengkap | ✅ (§2, per WP) |
| **Readiness Verification plan lengkap** | ✅ (§2A, per dimensi+gate) |
| Acceptance plan lengkap | ✅ (§3, per milestone) |
| Verification berbasis eksekusi | ✅ (V1) |
| **Readiness pipeline terdefinisi** | ✅ (§3A: Deliverable→Evidence→Verification→Readiness→Acceptance) |
| Evidence preservation terdefinisi | ✅ (§4) |
| Repository tetap read-only | ✅ |
| Working tree bersih | ✅ |
| Tanpa commit | ✅ |

---

*— Akhir EA-005-005 Verification & Acceptance Plan —*
