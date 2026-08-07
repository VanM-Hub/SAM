# EA-003-003 — Source of Truth Resolution Report

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Package:** EA-003 · **Status:** AUTHORIZED · **Bersifat:** 100% READ-ONLY
**Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)
**Scope:** P1 — G1-02, G8-03 (Source of Truth Claim)

---

## 1. Ringkasan Eksekutif

Ditemukan **konflik klaim Source of Truth** antara dua dokumen roadmap:
**`ROADMAP.md` (root)** dan **`docs/engineering/roadmap/ROADMAP SAM 2.x.md`**.
Keduanya berperan sebagai "roadmap" tetapi punya isi, status, dan riwayat yang berbeda.
Resolusi adalah **keputusan Architecture** — EA-003 hanya menyajikan fakta deterministik.

---

## 2. Fakta Deterministik — Perbandingan Kedua Dokumen

| Dimensi | `ROADMAP.md` (root) | `ROADMAP SAM 2.x.md` (engineering/roadmap) |
|---|---|---|
| Ukuran | 157 baris, 8.102 bytes | 69 baris, 1.421 bytes |
| Hash SHA-256 | `2A0D078D…7833418` | `2813B4B6…5C45C5854` (berbeda total) |
| Klaim SoT | **YA** — baris 3: *"Sumber kebenaran tunggal (single source of truth) untuk seluruh fase SAM"*; baris 195: *"Satu-satunya sumber kebenaran fase proyek & rencana"* | **TIDAK ada klaim eksplisit** |
| Metadata | Tidak ada header Version/Status formal | `Version: 2.0.0`, `Status: Active Development`, `Authority: Chief Architect` |
| Isi utama | Histori Fase I–XXIII (0.01→0.23), Program A–K (0.24→0.30), **SAM 1.0 release (2026-08-07)**, "Roadmap Produk post-1.0", kebijakan sinkronisasi dokumen | Purpose, Definition of Success, Engineering Principle (Platform Readiness), **Program Order A–E**, Readiness Targets, Exit Criteria |
| Commit terakhir | `0881c09` — **2026-08-07** (riwayat panjang, aktif di-repo) | `35d37c0` — **2026-08-08** (1 commit, baru dibuat) |
| Dirujuk ATLAS (navigasi) | Tidak langsung | **YA** — ATLAS arahkan ke `docs/engineering/roadmap/` (SAM 2.x, Program A–E, Milestone, Appendix) |

**Overlap konten:** `ROADMAP.md` juga menyebut "SAM 2.0" (Skalabilitas cluster, distributed runtime,
federation) dan "Program A" (Program C Simulation = Execution Evolution) — sehingga ada tumpang-tindih
tema dengan `ROADMAP SAM 2.x` namun dua dokumen berbeda.

---

## 3. Analisis Konflik SoT

### 3.1 Akar masalah

- `ROADMAP.md` **secara eksplisit mengklaim dirinya satu-satunya SoT** fase proyek & rencana,
  dan menetapkan "Kebijakan Sinkronisasi Dokumen (permanen)" yang menempatkan dirinya sebagai induk.
- Namun **ATLAS (navigasi resmi)** sudah mengarahkan pembaca ke `docs/engineering/roadmap/`
  (`ROADMAP SAM 2.x.md`) — sehingga ada **dua titik rujukan roadmap** untuk audiens yang sama.

### 3.2 Status keduanya (deterministik)

| Dokumen | Peran terlihat | Kesiapan jadi SoT |
|---|---|---|
| `ROADMAP.md` | Historis + roadmap produk (histori 0.01→0.30, SAM 1.0, Roadmap post-1.1) | Lengkap/aktif tapi berperan lebih sbg **record sejarah** |
| `ROADMAP SAM 2.x` | Strategi operasionalisasi ke Platform Governance (SAM 2.x) | **Baru (2026-08-08)**, ringkas, strategis; ATLAS memihak |

### 3.3 Dampak bila dibiarkan

- Pembaca navigasi ganda → bisa mengikuti roadmap yang berbeda.
- "Kebijakan Sinkronisasi" di ROADMAP.md bisa memberi kesan induk, padahal navigasi menunjuk tempat lain.
- Risiko Program A–E (inti Program A) direncanakan di satu tempat tapi direferensikan dari tempat lain.

---

## 4. Opsi Resolusi (keputusan Architecture — TIDAK dieksekusi EA-003)

| Opsi | Deskripsi | Risiko | Authority |
|---|---|---|---|
| **A. Pisahkan peran** | `ROADMAP.md` = **histori + status produk** (record); `ROADMAP SAM 2.x` = **SoT strategi/rencana** (Program A–E). Hapus klaim "satu-satunya" di ROADMAP.md | Rendah; klaris peran | Architecture |
| **B. ROADMAP.md tetap induk** | Biarkan ROADMAP.md jadi SoT, `SAM 2.x` dijadikan lampiran/di-link | Sedang; bertentangan dgn ATLAS & kebaruan | Architecture |
| **C. Konsolidasi tunggal** | Gabung histori + strategi ke satu dokumen, redirect lain | Tinggi; banyak perubahan | Architecture |

> **Catatan ⚠️ Read-only:** EA-003 **tidak mengubah** dokumen manapun. Seluruh opsi di atas adalah
> rekomendasi untuk fase implementasi EA-004+, menunggu keputusan Chief Architect.

---

## 5. G8-03 — Sinkronisasi Istilah "Single Source of Truth"

**Fakta:** Istilah "single source of truth / sumber kebenaran" dipakai tidak konsisten:
- `ROADMAP.md` (baris 3, 195): mengklaim sebagai SoT.
- ATLAS + dokumen lain: mengarahkan ke folder strategi (tanpa klaim eksplisit di `SAM 2.x`).
- `docs/foundation/` canonicals: `GLOSSARY.md` ada tapi folder `glossary/` kosong (G8-01) —
  sehingga definisi istilah tak terindeks tunggal.

**Dampak:** Ambigu siapa sumber sebenarnya untuk roadmap/rencana.

**Rekomendasi (fase lanjut):** Tetapkan definisi SoT di satu glossary; pastikan hanya SATU dokumen
yang boleh mengklaim SoT untuk tiap jenis konten (roadmap, spec, adr, release).

---

## 6. Exit Criteria EA-003-003

| Kriteria | Status |
|---|---|
| Analisis konflik SoT ROADMAP.md vs SAM 2.x (G1-02) | ✅ (fakta deterministik lengkap) |
| Sinkronisasi istilah SoT (G8-03) | ✅ (temuan tidak konsisten + rekomendasi) |
| Opsi resolusi disajikan (bukan dieksekusi) | ✅ |
| Read-only | ✅ |

---

*— Akhir EA-003-003 Source of Truth Resolution Report —*
