# ROADMAP ENGINEERING — Rencana Kerja Engineering (Sprint 1–7)

**Status:** Engineering Plan (disetujui)
**Disetujui oleh:** Software Architect · Guardian Mission (2026-08-06)
**Jenis dokumen:** Engineering Plan — **BUKAN** Source of Truth arsitektur.
**Batas:** Dokumen ini tidak mengubah / tidak menambah ADR, tidak merevisi Specification, tidak mengubah boundary, dependency, ownership, maupun runtime model.

---

## Konteks

Engineering beroperasi di atas **baseline Architecture yang sudah final**. Peran Engineering: menyelaraskan implementasi dengan Architecture yang ditetapkan, tanpa membuat keputusan arsitektur baru.

- Engineering **tidak menetapkan** Architecture Drift, perubahan Architecture/ADR, perubahan Runtime Model/Boundary/Dependency/Ownership.
- Bila selama implementasi ditemukan konflik nyata terhadap Source of Truth, Engineering **menghentikan pekerjaan** pada area tersebut, mengumpulkan evidence, dan **mengesklasikannya ke Software Architect**.

---

## Rencana Sprint

### Sprint 1 — Implementation Gap Closure ✅ Disetujui
- Sesuai keputusan Architecture: **L1 ditutup**; **L2 dan L6 adalah implementation gap**.
- Tidak mengubah Architecture.

### Sprint 2 — Architecture Compliance ✅ Disetujui
- Bila ditemukan **dugaan** Architecture Drift, Engineering tidak memutuskan sendiri.
- Wajib menyertakan:
  - Klausul Source of Truth
  - Evidence repository
  - Analisis konflik
- Selanjutnya diekskalasikan ke Software Architect.

### Sprint 3 — Code Quality ✅ Disetujui
- Batas: tidak mengubah public behavior, tidak mengubah dependency rule, tidak mengubah ownership, tidak mengubah boundary.

### Sprint 4 — Testing ✅ Disetujui
- Testing adalah **validasi implementasi**, bukan validasi Architecture.

### Sprint 5 — Compliance ✅ Disetujui
- Checker digunakan untuk **memverifikasi implementasi terhadap baseline Architecture**, bukan sebagai sumber keputusan Architecture.

### Sprint 6 — Technical Debt ✅ Disetujui
- Batas: tidak menghapus compatibility layer apabila masih merupakan bagian dari Architecture.
- Penghapusan hanya untuk komponen yang benar-benar tidak lagi memiliki fungsi dan tidak dilindungi oleh Architecture.

### Sprint 7 — Release Readiness ✅ Disetujui
- Kriteria: **tidak ada Architecture Drift yang telah dikonfirmasi oleh Software Architect**.
- Penentuan Architecture Drift bukan kewenangan Engineering.

---

## Kewenangan Engineering

**Engineering bertanggung jawab atas:** implementasi, refactoring, testing, integration, observability, performance, CI/CD, technical debt reduction, implementation gap closure.

**Engineering TIDAK menetapkan:** Architecture Drift, perubahan Architecture, perubahan ADR, perubahan Runtime Model, perubahan Boundary, perubahan Dependency, perubahan Ownership.

---

## Aturan Eskalasi

Jika implementasi menemukan fakta yang bertentangan dengan Source of Truth:
1. Hentikan pekerjaan pada area tersebut.
2. Kumpulkan evidence.
3. Buat laporan: fakta · evidence · dampak · area implementasi terdampak.
4. Eskalasikan ke Software Architect.

Tidak ada keputusan arsitektur yang diambil di level Engineering.

---

## Status

Rencana Engineering disetujui dengan satu penyesuaian pada kriteria Sprint 7 mengenai kewenangan penetapan Architecture Drift. Fokus selanjutnya: menuntaskan implementation gap, menjaga kepatuhan terhadap baseline Architecture, serta mempertahankan hasil compliance dan pengujian.

*Dokumen ini adalah Engineering Plan dan tidak mengubah maupun menambah Source of Truth arsitektur.*
