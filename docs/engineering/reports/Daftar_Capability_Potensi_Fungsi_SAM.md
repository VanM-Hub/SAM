# Daftar Capability SAM - Potensi Fungsi Baru

**Tujuan:** Menginventarisasi capability yang sudah ada di kode (SAM 4.x) yang bisa
dikapitalisasi menjadi fungsi yang bisa dipakai operator, plus gap capability nyata
yang belum dibangun.
**Disusun:** 2026-08-09 (untuk diskusi Chief Architect)
**Sifat:** Inventarisasi & rekomendasi - TIDAK ada perubahan kode.

---

## Bagian A - Capability yang SUDAH ADA -> siap dikapitalisasi jadi fungsi

> Semua ini bahan bakunya sudah diimplementasikan (MISSION-4.1..4.6). Yang kurang
> adalah menyajikannya sebagai fungsi yang bisa dipakai manusia (UI + API).

| # | Capability Teknis (di kode) | Fungsi yang bisa dibuat | Lokasi kode | Bahan baku | Prioritas |
|---|---|---|---|---|---|
| A1 | **SAM Memory jangka panjang** | "Tanya SAM tentang masa lalu" - SAM ingat semua pengalaman/kejadian meski aplikasi di-restart | `src/sam/operational_learning/` (persistent storage) | Persistent Experience Repository (restart-survive) | TINGGI |
| A2 | **Early Warning / Proactive Alert** | SAM menegur operator SEBELUM masalah memburuk (notifikasi dini dari kondisi runtime/provider) | `src/sam/autonomous_operations/` (trigger + health monitor) | Investigation Trigger, Operational Health | TINGGI |
| A3 | **Case Matching / "SAM pernah lihat ini?"** | Saat ada masalah baru, SAM cari kasus serupa untuk dipelajari -> rekomendasi lebih cepat & terbukti | `src/sam/operational_learning/` | Case Repository, Similarity Engine, Case Retrieval | TINGGI |
| A4 | **Explain "Kenapa?"** | SAM menjelaskan alasan di balik sebuah diagnosis/rekomendasi/keputusan (bukan cuma hasil) | `src/sam/governed_reasoning/` | Structured Reasoning, Reasoning Explainability | SEDANG |
| A5 | **Trust Score tampil** | Operator melihat seberapa andal rekomendasi SAM sebelum memutuskan menjalankan | `src/sam/governed_reasoning/` + `operational_workspace/` | Trust Assessment, Trust Visualization | SEDANG |
| A6 | **Kelola Kredensial Provider** | Halaman untuk menambah/mengelola API key provider secara aman (selalu dimasking, tidak pernah tampil polos) | `src/sam/execution_runtime/` + `governed_reasoning/` | Credential Management, mask_secret | SEDANG |
| A7 | **Self-Health SAM** | SAM memeriksa kesehatannya sendiri dan menampilkan status diri (semua capability normal?) | `src/sam/autonomous_operations/` | Self-Debugging, Readiness, Metrics | RENDAH |
| A8 | **Satu Tombol "Jalankan Siklus"** | Operator menjalankan siklus lengkap (deteksi->analisis->rekomendasi->approval->eksekusi->verifikasi->belajar) dari satu pintu | `src/sam/operational_workspace/` | End-to-End Flow (ASK->LEARN) | TINGGI |

---

## Bagian B - Capability BARU yang belum ada -> butuh Mission baru

> Ini bukan "mengkapitalisasi" tapi **menambah capability baru**. Perlu Mission &
> persetujuan arsitektur (bukan sekadar wiring UI).

| # | Capability Baru | Fungsi yang dimungkinkan | Status di SAM | Kompleksitas |
|---|---|---|---|---|
| B1 | **Federated Governance antar-instance SAM** | Dua/multiple SAM dapat berkoordinasi, berbagi pembelajaran, atau saling memverifikasi keputusan | Belum ada (di visi "Federated Governance Platform") | TINGGI |
| B2 | **Cross-instance Knowledge Sharing** | Knowledge dari satu SAM bisa dipakai SAM lain (jika B1 disetujui) | Belum ada (turunan B1) | MENENGAH |
| B3 | **Scheduler / Penjadwalan Otonom** | SAM menjalankan verifikasi/monitor otomatis berkala (cron-like) tiap interval | Belum ada (autonomy belum di-wiring ke event loop) | MENENGAH |

---

## Rekomendasi Prioritas

**Fase 1 (nilai tertinggi, modal sudah kuat, aman tanpa mission baru):**
- A1 SAM Memory (tanya masa lalu)
- A2 Early Warning (proaktif)
- A3 Case Matching (gunakan pengalaman)
- A8 Tombol siklus end-to-end

**Fase 2 (memperkuat kepercayaan operator):**
- A4 Explain "kenapa?"
- A5 Trust Score tampil

**Fase 3 (opsional / pelengkap):**
- A6 Kelola kredensial
- A7 Self-health SAM
- B1/B2 Federasi (butuh keputusan arsitektur & Mission baru)
- B3 Penjadwalan otonom

---

## Catatan

- Semua fungsi Bagian A **tidak mengubah Foundation / Governance / capability**
  - hanya menyajikan apa yang sudah ada.
- Semua Bagian B **menambah capability baru** -> butuh Mission baru & review Chief
  Architect (bukan sekadar wiring).
- Eksekusi & recovery tetap **approval-gated (Article V)** di semua fungsi di atas.

---

*Dokumen inventarisasi - untuk diskusi & keputusan arsitektur.*
