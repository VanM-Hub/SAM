# E1-000 — Architecture Validation: Composition Root Placement

**Document ID:** E1-000
**Title:** Architecture Validation: Composition Root Placement
**Status:** Pending Decision
**Date:** 2026-08-03
**Author:** Zara (Architecture Validation, atas arahan Van)
**Audience:** Architecture, Engineering
**Source of Authority (trace chain):** Foundation → Specification → Blueprint (G0-001) → ADR-000..ADR-007 → R4-001 → R4-002 → R5-001 → I0-001 → I1-001 → P0-001 → P1-001..P1-008

---

## 1. Tujuan

Membuktikan secara arsitektural **di mana Composition Root untuk 7 Reference Runtime Unit seharusnya berada**, **sebelum satu baris kode pun di-commit**. Dokumen ini adalah Deliverable latihan Architecture Validation (E1-000) untuk rencana kerja E1-001 (Reference Runtime Composition).

Rencana E1-001 menuntut path `src/sam/runtime/composition/` **TETAPI** juga menuntut DILARANG mengubah Compliance/Baseline/ADR/Architecture. Folder baru tersebut memicu pelanggaran checker compliance **L0-11** (bagian P1-008, tak boleh diubah). Dokumen ini memutuskan konflik tersebut dari sisi arsitektur, bukan dari sisi kerjaan.

---

## 2. Klasifikasi Artifak — "composition" itu APA?

Empat kategori yang Van berikan, diverifikasi terhadap source of truth:

| # | Kategori | Verdict Arc | Bukti |
|---|---|---|---|
| 1 | **Runtime Component** | ❌ **BUKAN** | R4-001: "7 komponen ... tidak ada komponen ke-8" (Executive Summary; §Audit 1). R5-001 S1: "Tepat 7 Unit — tidak ada Unit ke-8". MC1: "Tidak boleh menambah, tidak boleh mengurangi, tidak boleh menggabungkan". |
| 2 | **Runtime Composition Root** | ✅ **YA — inilah esensinya** | Konsep ini **absen total** dari seluruh rantai otoritas (R4-001, R4-002, R5-001, I0-001, I1-001, G0-001, 8 ADR). Ia bukan unit, bukan komponen, bukan modul — ia adalah **aktivitas perakitan (wiring/assembly) waktu-implementasi** yang merangkai 7 unit yang sudah ada menjadi konfigurasi hidup. Ini persis domain **Implementation Freedom** R5-001 §8 (IF2/IF17: struktur package & organisasi kode bebas), selama 7 unit tidak digabung/dipisah dan boundary tidak diubah. |
| 3 | **Bootstrap Layer** | ⚠️ **Sama keluarga** | Yang ada di repo adalah bootstrap **level aplikasi** (`sam/runtime/bootstrap.py` — legacy "Phase 0", `RuntimeCoordinator`, dipakai agent/api/cli). Itu **bukan** entitas yang merakit 7 Reference Runtime Unit. Composition Root untuk 7 unit adalah concern yang **berbeda** dan belum ada tempatnya. |
| 4 | **Application Host** | ❌ **BUKAN** | R4-001/R4-002: Host adalah **Citizen Host Unit** — unit permukaan Runtime, titik masuk interaksi eksternal via Contracts + Registry. Bukan container yang meng-host seluruh unit. |

**Kesimpulan klasifikasi:** `composition` adalah **Runtime Composition Root** — lapisan perakitan yang **menyalin keluar** dari paket Reference Runtime (`sam/runtime`), bukan entitas internalnya.

---

## 3. Verdict: Path `src/sam/runtime/composition/` DIBATALKAN

### 3.1 Bukti struktural (tidak macam-macam, dari dokumen)

**I1-001 (Repository Skeleton) — struktur final dan mengikat:**

| Sumber | Aturan | Dampak pada `runtime/composition/` |
|---|---|---|
| §1.2 Module Count | **Tepat 21 direktori** = 7 unit + 4 infra (`shared, contracts, registry, internal`) + 9 test + 1 tools | `composition/` = direktori ke-22 → **melanggar** |
| §5.1 Directory Purposes | `runtime/` hanya boleh berisi 7 unit + 4 infra yang punya peran spesifik | Tidak ada peran "composition root" di daftar izin |
| §2.8–2.11 | 4 infra punya batas dependency ketat (tidak boleh import unit) | `composition/` yang meng-import semua 7 unit **melanggar IR4/DR3** (unit → unit lateral) dari sudut repositori |

**R4-001 / R5-001 / ADR — sudah tidak ada komponen ke-8:**
- R4-001: "tidak ada komponen ke-8" (Exec Summary, Audit 1 — "7 komponen = 7 modul, tidak ada yang ditambahkan").
- R5-001 S1/MC1: 7 unit, tidak boleh ditambah/digabung.
- ADR-007 (via R4-001 L464): "adds no 8th component" — preseden eksplisit bahwa Verification pun bukan komponen baru; ia state transition **di dalam** Audit Recorder. Analog: Composition Root bukan komponen ke-9.

### 3.2 Bukti compliance (konsekuensi praktis)

Checker **L0-11** (`RuntimeNoExtraTopLevelCheck`, bagian P1-008) memindai `_RUNTIME_PREFIX = "src/sam/runtime/"` dan melarang direktori top-level selain 7 unit + 4 support (`contracts, internal, registry, shared`). Menambah `composition/` → L0-11 GAGAL (verdict D, `deviating: 1`), sementara E1-001 DILARANG mengubah Compliance & Baseline. **Konflik tidak bisa didamaikan dengan tetap berada di dalam `sam/runtime/`.**

### 3.3 Keputusan

> **`src/sam/runtime/composition/` DIBATALKAN** — melanggar I1-001 (struktur 11 source-module) dan memicu L0-11 (P1-008) yang tak boleh diubah.

---

## 4. Lokasi Baru yang Disarankan

Composition Root harus diletakkan **di lapisan aplikasi (assembly layer)**, **di luar** `sam/runtime/`, mengikuti konvensi namespace `*_runtime/` yang sudah ada di level `sam` (mis. `runtime_service/`, `runtime_kernel/`, `presentation/runtime/`).

### 4.1 Kriteria lokasi valid
| Kriteria | Terpenuhi oleh lokasi baru |
|---|---|
| Tidak mengubah 7 Runtime Units | ✅ Unit tetap utuh di `sam/runtime/*/` |
| Tidak mengubah Runtime Boundary | ✅ Boundary (Contracts + Registry + Citizen Host) utuh |
| Tidak mengubah Compliance Baseline | ✅ L0-11 & seluruh checker hanya scan `src/sam/runtime/` → folder baru di luar prefix tidak terlihat |
| Tidak mengubah ADR | ✅ Tidak ada ADR baru yang dibutuhkan |
| Tidak mengubah Runtime Architecture (R4-001) | ✅ Arsitektur 7 komponen tetap; Composition Root hanyalah perakitan, bukan komponen |
| Sesuai Implementation Freedom R5-001 §8 (IF2/IF17) | ✅ Struktur package/organisasi kode = keputusan bebas selama unit utuh |

### 4.2 Kandidat & rekomendasi

| Lokasi | Cocok? | Catatan |
|---|---|---|
| `src/sam/runtime/composition/` | ❌ | Dibatalkan (lihat §3) |
| `src/sam/runtime_kernel/` (tambahkan sub-package) | ⚠️ | Sudah ada, isinya coordinator/manifest/startup aplikasi — **campur** dengan concern Reference Runtime |
| `src/sam/runtime_service/` (tambahkan sub-package) | ⚠️ | Sudah ada, isinya service/container aplikasi — concern aplikasi, bukan perakitan Reference Runtime |
| **`src/sam/runtime_root/` (paket baru, disarankan)** | ✅ | Namespace bersih, satu tujuan: **merakit 7 Reference Runtime Unit jadi runtime hidup**. Di luar `sam/runtime/`, mematuhi seluruh 6 kriteria §4.1. Mengikuti konvensi `*_runtime/` yang sudah ada. |

**Rekomendasi:** `src/sam/runtime_root/` sebagai **paket perakitan bersih** (composition root murni untuk 7 Reference Runtime Unit), terpisah dari kernel/service aplikasi yang sudah mencampur banyak concern.

---

## 5. Verifikasi Non-Teknis atas Rekomendasi

| Aspek | Hasil |
|---|---|
| Compliance L0-11 (P1-008) | ✅ Folder di luar `src/sam/runtime/` tidak dipindai; **99 checker tetap HIJAU, nol perubahan baseline** |
| Import DAG (I1-001 §3) | ✅ Composition Root boleh import semua 7 unit (ia lapisan atas, bukan unit); unit tetap `must not depend` pada composition root. Tidak ada cycle (arah: units → root, bukan sebaliknya). |
| PHP/kesatuan arsitektur | ✅ 7 unit tetap 7 direktorat; composition lahir sebagai konsumen, bukan penyusup |

---

## 6. Dampak pada Rencana E1-001

- Path di IMPLEMENTATION E1-001 **berubah** dari `src/sam/runtime/composition/` → **`src/sam/runtime_root/`** (atau lokasi lain yang Van setujui).
- Seluruh artefak yang sudah ditulis di `src/sam/runtime/composition/` (builder, container, composition, lifecycle, health, registry, graph, validator, exceptions) dan `tests/runtime/composition/` **dipindah** ke lokasi baru — **tidak di-commit di lokasi lama**.
- Delphi tidak mengubah: 7 unit, boundary, baseline, ADR, arsitektur.
- E1-001 doc nantinya akan mencatat **interpretasi path aktual** ini sebagai hasil Architecture Validation E1-000.

---

## 7. Rekomendasi untuk Van

1. **Setujui** bahwa `composition` = **Runtime Composition Root** (bukan Runtime Component / Application Host), dan path lama dibatalkan.
2. **Setujui lokasi baru**: `src/sam/runtime_root/` (rekomendasi) **atau** beri nama/lokasi yang Van inginkan.
3. Setelah disetujui, saya akan **memindahkan** seluruh artefak composition (kode + 48 test) ke lokasi baru, menyesuaikan import, menjalankan ulang seluruh compliance (99 checker) + suite test composition, lalu commit/push.

**TIDAK ADA perubahan kode hingga Van menyetujui verdict ini.**
