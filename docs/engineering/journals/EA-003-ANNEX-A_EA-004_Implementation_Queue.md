# EA-003-ANNEX-A — EA-004 Implementation Queue

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Package:** EA-003 · **Status:** AUTHORIZED · **Bersifat:** 100% READ-ONLY
**Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Artefak ini memetakan temuan EA-003 menjadi **antrean implementasi** untuk fase berikutnya (EA-004).
> EA-004 TETAP read-only planning kecuali diotorisasi ulang untuk mengubah repo.
> Setiap item = fakta + severity revisi + rekomendasi + authority.

---

## 1. Ringkasan Koreksi Severitas (EA-002 → EA-003)

| Gap | Severity EA-002 | Severity EA-003 (revisi) | Alasan |
|---|---|---|---|
| G10-01 | Critical | **Medium — duplikasi** | 99 checker executable SUDAH ADA via Builder; `_placeholders.py` = katalog deklaratif paralel (obsolete). Bukan "implementasi belum ada". |
| G10-03 | Mixed | **Medium — dua jalur paralel** | Jalur produksi (Builder) fungsional & PASSED; jalur placeholder tak dipakai. Perlu resolusi SoT kode, bukan implementasi baru. |
| G9-02 | High | **Medium** | TraceabilityCheck framework + L4-03 ADA & executable; yang kurang matriks end-to-end. |
| G9-01 | High | **Medium — gap desain** | Tidak ada matriks end-to-end Mission→Capability→Program→Release. |
| G9-03 | High | **Medium** | Appendix A readiness matrix ada; checker-nya TIDAK ada. |
| G1-02 | Medium | **Medium — keputusan Architecture** | Konflik SoT terkonfirmasi (ROADMAP.md klaim "satu-satunya" vs ATLAS→SAM 2.x). |
| G8-03 | Medium | **Medium** | Istilah SoT tidak konsisten; tak ada glossary terindeks tunggal (G8-01). |

---

## 2. Implementation Queue (untuk EA-004+, read-only planning)

| Item | Gap | Tindakan (rencana) | Authority | Depends On | Target Fase |
|---|---|---|---|---|---|
| QA-01 | G10-01 | **Resolusi SoT kode**: tentukan 1 sumber kebenaran definisi check (catalog Builder). Verifikasi metadata `_placeholders.py` (99) == catalog builder (99) via diff ID/desc/severity/baseline_ref; lalu arsip `_placeholders.py` (bukan hapus langsung) | Engineering | — | EA-004 |
| QA-02 | G10-03 | Buat audit lengkap 99 check builder: jalankan & catat hasil PASSED/FAILED per check thd baseline P1-007; beri status kematangan (full/pended/skip) | Engineering | QA-01 | EA-004 |
| QA-03 | G9-02 | Rancang penggunaan `TraceabilityCheck` + `L4-03` utk memvalidasi rantai artifact→baseline; petakan ke level capabilitas | Engineering | — | EA-004 |
| QA-04 | G9-01 | Rancang matriks traceability end-to-end Mission→Capability→Program→Release (dokumen desain, bukan build) | Architecture | QA-03 | EA-004 |
| QA-05 | G9-03 | Rancang checker readiness matrix: baca Appendix A (21 capability Current/Target/Program) + verifikasi vs evidence per Program | Engineering | QA-04 | EA-004 |
| QA-06 | G1-02 | Resolusi SoT roadmap: pilih opsi A/B/C (dari EA-003-003 §4) — keputusan Chief Architect | Architecture | — | EA-004 |
| QA-07 | G8-03 | Tetapkan definisi SoT tunggal di glossary; pastikan hanya 1 dokumen klaim SoT tiap jenis konten | Architecture | QA-06, G8-01 | EA-004 |

---

## 3. Exit Criteria EA-003 (keseluruhan)

| Kriteria | Status |
|---|---|
| EA-003-001 Compliance Classification | ✅ (G10-01/03 terkoreksi: implementasi ADP; obsolete = placeholder) |
| EA-003-002 Traceability Resolution | ✅ (G9-01/02/03 fakta deterministik) |
| EA-003-003 Source of Truth Resolution | ✅ (G1-02/08-03 + opsi resolusi) |
| ANNEX-A EA-004 Implementation Queue | ✅ (QA-01..07) |
| Read-only dipertahankan | ✅ (git status: hanya `M ROADMAP.md` sisa lama) |

---

*— Akhir EA-003-ANNEX-A —*
