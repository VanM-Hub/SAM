# EA-004-006 — Rollback Matrix

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Rollback Matrix · **Status:** AUTHORIZED
**Mode:** 100% READ-ONLY · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini mendefinisikan **model rollback deterministik** Program A: kapan rollback perlu,
> sampai mana diperbolehkan, siapa berwenang, evidence apa yang wajib dipertahankan.
> **BUKAN prosedur Git / strategi branch / VCS baru / bukan eksekusi rollback.**
> Mendefinisikan MODEL ROLLBACK saja, berbasis evidence sequencing (EA-004-005).

---

## 1. Rollback Scope

Area implementasi yang berpotensi memerlukan rollback (sesuai EA-004-004 §3 Engineering Normalization Order).

| Scope | Area | Alasan (evidence) |
|---|---|---|
| **Repository** | Struktur/naming/dedupe (WS-02, Phase 1) | 21 gap duplikasi/orphan/naming — pemindahan/rename berisiko rujukan putus |
| **Documentation** | Konsistensi & klasifikasi dokumen (WS-02/03, Phase 1-2) | Isi/mutasi dokumen; rujukan silang rentan |
| **Compliance** | SoT kode check + audit (WS-05, Phase 4) | QA-01 diff 99==99; arsip `_placeholders.py` |
| **Testing** | Scope compliance/testing (WS-06, Phase 5) | G10-02 scope ambiguous |
| **Legacy** | Isolasi legacy/historical (WS-03, Phase 2) | 6 gap G4/G5 — pemindahan artefak |
| **Traceability** | Matriks Mission→Capability→Program→Release (WS-04, Phase 3) | G9-01/02 — matriks + checker |

---

## 2. Rollback Unit

Unit rollback terkecil per workstream/fase (dari evidence sequencing, bukan asumsi).

| Fase | Workstream | Rollback Unit (terkecil) | Alasan (evidence) |
|---|---|---|---|
| **Phase 1** | WS-02 Repository Normalization | **1 batch normalisasi** (1 kelompok dedupe / 1 pola naming / 1 group orphan) | 21 gap beragam; batch kecil = isolasi dampak per kelompok artefak |
| **Phase 2** | WS-03 Legacy Isolation | **1 kelompok dokumen legacy** | 6 gap; isolasi per kelompok artefak (EA-004-003 §4) |
| **Phase 3** | WS-04 Documentation Traceability | **1 artifact matriks / 1 checker** | G9-01/02; matriks anti-siklik per artefak |
| **Phase 4** | WS-05 Compliance Normalization | **1 kategori check / 1 arsip deklarasi** | QA-01 diff; arsip utk `_placeholders.py` bersifat deklaratif |
| **Phase 5** | WS-06 Testing Normalization | **1 scope-area** | G10-02; per-tegasan scope |
| **Phase 0** | WS-01 Source of Truth | **1 keputusan SoT (revisable)** | Keputusan Architecture; reversible sebelum dipublikasi |

> **Prinsip (dari EA-004-005 §5):** Rollback unit TIDAK boleh melintasi **Synchronization Point yang telah di-accept** — rollback hanya berlaku di dalam fase aktif.

---

## 3. Rollback Trigger

Trigger formal untuk memulai rollback (per unit).

| Trigger | Definisi | Contoh evidence |
|---|---|---|
| **T1 Verification failure** | Verifikasi eksekusi gagal (EA-LL-001: eksekusi, bukan statis) | Checker PASSED→gagal; diff 99≠99 |
| **T2 Dependency unmet** | Prasyarat tidak terpenuhi saat fase dimulai | Rantai upstream belum stabil (EA-004-004 §3) |
| **T3 Architecture blocking decision berubah** | Keputusan SoT / klasifikasi core berubah | G1-02 opsi A/B/C berubah; docs/core status berubah |
| **T4 Evidence inconsistent** | Bukti bertentangan dgn klaim | Rujukan putus setelah dedupe; legacy masih di jalur aktif |
| **T5 Sync point tidak tercapai** | Exit evidence SP tidak terpenuhi | Matriks traceability gagal PASSED di SP-4 |

---

## 4. Rollback Authority

Siapa berwenang memutuskan rollback (konsisten AP-2A & EA-004-005 §6).

| Scope / Fase | Keputusan rollback diputuskan oleh | Alasan |
|---|---|---|
| **Phase 0 — SoT** | **Software Architect** | Keputusan arsitektur & SoT = Architecture Authority (G1-02) |
| **Phase 1 — Normalisasi** | **Engineering** | Operasional repositori engineering |
| **Phase 2 — Legacy** | **Engineering** | Klasifikasi & pemindahan engineering |
| **Phase 3 — Traceability** | **Engineering (dgn review Architect)** | Matriks desain engineering; form = arsitektur |
| **Phase 4 — Compliance** | **Engineering** | Resolusi kode check engineering |
| **Phase 5 — Testing** | **Software Architect** | Batas scope compliance lintas area |
| **Lingkup Program A** | **Mission** | Acceptance program (mission gate) |

---

## 5. Rollback Evidence

Evidence minimum yang **wajib tetap tersedia** setelah rollback — rollback tidak boleh menghilangkan jejak audit.

| Evidence | Sumber | Wajib ada setelah rollback |
|---|---|---|
| **Gap ID** | EA-001 (36 gap) | ✅ — untuk traceability gap↔unit rollback |
| **Mapping** | EA-003-ANNEX-A (QA-01..07) | ✅ — item↔workstream |
| **Traceability** | EA-004-005 §7 / EA-004-004 | ✅ — urutan & dependency |
| **Verification result** | hasil eksekusi checker/diff | ✅ — bukti lulus/gagal (T1) |
| **Audit trail** | catatan perubahan (sebelum/sesudah) | ✅ — jejak tidak boleh hilang |

> Prinsip: **rollback memulihkan state, TIDAK menghapus evidence.** Alasan dan bukti yang memicu rollback (trigger) dipertahankan.

---

## 6. Rollback Boundary Matrix

Matriks: Phase · Rollback Unit · Maximum Boundary · Sync Point terkait · Authority.

| Phase | Rollback Unit | Max Rollback Boundary | Sync Point terkait | Authority |
|---|---|---|---|---|
| **Phase 0** | 1 keputusan SoT | Sampai sebelum klasifikasi dipublikasi | SP-1 (masuk) | Software Architect |
| **Phase 1** | 1 batch normalisasi | Dlm fase aktif; **tidak melewati SP-2** | SP-2 (keluar Phase1) | Engineering |
| **Phase 2** | 1 kelompok dokumen legacy | Dlm fase aktif; **tidak melewati SP-3** | SP-3 (keluar Phase2) | Engineering |
| **Phase 3** | 1 artifact matriks/checker | Dlm fase aktif; **tidak melewati SP-4** | SP-4 (keluar Phase3) | Engineering + Arch review |
| **Phase 4** | 1 kategori check / arsip | Dlm fase aktif; **tidak melewati SP-5** | SP-5 (keluar Phase4) | Engineering |
| **Phase 5** | 1 scope-area | Dlm fase aktif; **tidak melewati SP-6** | SP-6 (verification gate) | Software Architect |
| **Program A** | — (acceptance) | Setelah SP-6 di-accept → rollback via prosedur baru, bukan membatalkan fase | SP-6 (acceptance) | Mission |

> **Prinsip inti (catatan Engineering EA-004-005):** Maximum Rollback Boundary = **Synchronization Point fase tersebut**, selama fase masih aktif. Begitu SP di-accept, rollback dilakukan lewat **prosedur recovery baru**, bukan membatalkan fase yang sudah ditutup.

> **Penegasan authority (catatan Engineering EA-004-006):** **Rollback Authority ≠ Acceptance Authority.** Keduanya tidak boleh dicampur —
> - Engineering dapat memutuskan **rollback** implementasi (fase 1-4);
> - **Mission** tetap menjadi **acceptance authority** Program A;
> - Software Architect memegang rollback utk fase SoT (0) & Testing (5).

---

## 7. EA-005 Input

Wariskan untuk EA-005 (Implementation WBS).

| Item | Nilai warisan |
|---|---|
| **Rollback dependency** | Rollback unit = batch/kelompok 1 unit; batas = SP fase |
| **Rollback sequencing** | Urutan rollback mengikuti urutan fase; tidak mundur melewati SP |
| **Authority gate** | rollback Engineering (fase 1-4) · Architect (fase 0,5) · Mission (Program) |
| **Blocker rollback** | G1-02 (fase 0) + docs/core klasifikasi jadi prasyarat rollback legacy penuh |
| **Evidence preservation** | Gap ID, mapping QA, traceability, verification result, audit trail — wajib dipertahankan |

---

## 8. Batasan (Larangan EA-004-006 — dipatuhi)

- ❌ Tidak menjelaskan prosedur Git
- ❌ Tidak menentukan strategi branch
- ❌ Tidak membuat mekanisme version control baru
- ❌ Tidak melakukan rollback
- ❌ Tidak mengubah repository
- ✅ Hanya mendefinisikan model rollback Program A

---

## 9. Exit Criteria EA-004-006

| Kriteria | Status |
|---|---|
| Rollback scope terpetakan | ✅ (§1, 6 scope) |
| Rollback unit tersedia | ✅ (§2) |
| Rollback trigger terdokumentasi | ✅ (§3, T1-T5) |
| Rollback authority lengkap | ✅ (§4) |
| Rollback evidence lengkap | ✅ (§5) |
| Rollback boundary matrix tersedia | ✅ (§6) |
| Input EA-005 tersedia | ✅ (§7) |
| Repository tetap read-only | ✅ |
| Working tree bersih | ✅ |
| Tanpa commit | ✅ |

---

*— Akhir EA-004-006 Rollback Matrix —*
