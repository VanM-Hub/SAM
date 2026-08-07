# EA-005-004 — Engineering Resource & Ownership Matrix

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Engineering Resource & Ownership Matrix · **Status:** AUTHORIZED
**Mode:** PLANNING (READ-ONLY) · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini menetapkan **ownership** per workstream/work package, jalur eskalasi, dan pembagian peran
> sesuai AP-2A-001/002/005/006. Konsisten dgn EA-004-005 §6 (authority gates) & EA-004-006 §4.
> **BUKAN penugasan personel nyata / bukan daftar sumber daya manusia** — ini **role/ownership matrix** berbasis kewenangan.

---

## 1. Role vs Authority

| Role | Kewenangan (AP-2A) | Contoh keputusan |
|---|---|---|
| **Software Architect** | Architecture authority; SoT; scope lintas area | G1-02 (SoT), klasifikasi docs/core, scope compliance/testing |
| **Engineering (Lead/ZARA)** | Operasional repositori; normalisasi; legacy; compliance kode; rollback implementasi | WP-02.x, WP-03.x, WP-05.x |
| **Engineering + Architect review** | Desain engineering + validasi arsitektur | WP-04.x (matriks form) |
| **Mission** | Acceptance akhir Program A | M-6 |

> **Prinsip (EA-004-006 §6):** **Rollback Authority ≠ Acceptance Authority.** Engineering memutuskan rollback implementasi; Mission tetap acceptance authority.

---

## 2. Ownership Matrix

| Work Package | Primary Owner | Reviewer | Acceptance | Escalation path (saat blocked) |
|---|---|---|---|---|
| WP-01.1 (SoT) | Software Architect | Mission | SP-1 | Mission (keputusan arsitektur) |
| WP-02.1..06 | Engineering | — | SP-2 | Architect (bila overlap arsitektur) |
| WP-03.1..02 | Engineering | — | SP-3 | Architect (classify core) |
| WP-04.1..02 | Engineering | Software Architect | SP-4 | Architect (form matriks) |
| WP-05.1..03 | Engineering | — | SP-5 | Architect / Mission (scope) |
| WP-06.1 | Software Architect | Engineering | SP-6 | Mission |

---

## 3. Blocker Ownership

Blocker Program A (dari EA-004-007 §3) — siapa yang **berwenang unblock** (bukan siapa yg bekerja).

| Blocker | Kategori | Owner unblock | Evidence yg dibutuhkan |
|---|---|---|---|
| G1-02 (SoT) | Architecture Blocker | Software Architect | opsi A/B/C final |
| klasifikasi docs/core | Architecture Blocker | Software Architect | status Unknown → final |
| QA-01 (diff 99==99) | Engineering Evidence Blocker | Engineering | evidence diff |
| evidence tambahan | Engineering Evidence Blocker | Engineering | audit/eksekusi |
| acceptance akhir | Mission Acceptance Blocker | Mission | seluruh M-0..M-5 evidence |

---

## 4. Resource Readiness

Setiap WP memiliki **owner berwenang** yang siap dieksekusi begitu unblock. Tidak ada kebutuhan sumber daya tambahan di luar peran existing.

| Work Package | Owner ready? | Catatan |
|---|---|---|
| WP-02.x (6) | ✅ | Engineering — siap setelah M-0 |
| WP-04.x (2) | ✅ | Engineering + review Architect — setelah Q-03 |
| WP-03.x, WP-05.x, WP-06.1, WP-01.1 | ⏳ **Not Ready** | menunggu blocker (Architecture/QA-01) |

---

## 5. Exit Criteria EA-005-004

| Kriteria | Status |
|---|---|
| Ownership per WP jelas | ✅ |
| Escalation path tersedia | ✅ |
| Blocker ownership eksplisit | ✅ |
| Resource readiness diverifikasi | ✅ |
| Repository tetap read-only | ✅ |
| Working tree bersih | ✅ |
| Tanpa commit | ✅ |

---

*— Akhir EA-005-004 Engineering Resource & Ownership Matrix —*
