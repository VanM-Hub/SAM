# STRUCTURE.md SAM 1.0 Foundation: Konstitusi Struktur Repository

> **Dokumen ini adalah definisi baku (canonical) struktur folder repository SAM.**
> Ini menjadi rujukan tunggal bagi semua pihak saat menempatkan file tidak boleh asal menaruh.
> Bukan sekadar usulan: **kontrak ini selaras dengan kode compliance**
> (`src/sam/compliance/baseline/loader.py`, tabel `_DOC_DIR_TYPES`, `_ROOT_FILE_TYPES`).
> Status: Blueprint WAJIB diverifikasi terhadap kode sebelum mengeksekusi pemindahan.

---

## 1. Prinsip Dasar

1. **Kode compliance adalah otoritas tertinggi.** Folder/berkas yang dirujuk kode tidak boleh hilang; yang dirujuk tapi belum ada harus dibuat.
2. **Setiap folder punya satu peran tegas** tidak ada folder "tumpang tindih" atau "asal".
3. **History tidak dihapus, hanya diarsipkan.** Semua jejak masa lalu tetap bernilai dan bisa dibuka kembali.
4. **Fondasi bersifat read-only** (frozen). Empat tingkat atas hierarki kewenangan hampir tidak berubah:
 `Mission Constitution Architecture ADR Engineering Code`.
5. **Dokumen Engineering ke depan ringkas**, mengikuti format release (Added / Fixed / Changed / Architecture Impact / Compliance / Decision) bukan laporan puluhan halaman.

---

## 2. Hierarki Kewenangan (frozen)

```
Mission
 
Constitution
 
Architecture
 
ADR
 
Engineering
 
Code
```

Empat tingkat pertama hampir tidak pernah berubah lagi. Dokumen di tingkat itu diperlakukan read-only.

---

## 3. Struktur Wajib `docs/` dijamin kode compliance

Folder berikut **dikontrak** oleh `_DOC_DIR_TYPES` (kode). Wajib ada, dan di-scan kode sebagai "jenis" tertentu:

| Folder `docs/...` | Jenis compliance | Status sekarang | Peran (definisi baku) |
|---|---|---|---|
| `foundation/` | foundation | **ada (9 md)** | Misi & identitas: Mission, Vision, Charter, Constitution, Governance, Philosophy, Principles, Glossary, Citizen Spec (semua versi 1.0.0) |
| `specifications/` | specification | ada (7 md) | Spesifikasi resmi (kontrak perilaku/format) |
| `adr/` | adr | ada (25 md) | Architecture Decision Records keputusan arsitektur, immutable |
| `architecture/` | architecture | ada (21 md) | Desain & fondasi arsitektur (hasil akhir, read-only) |
| `blueprint/` | blueprint | **ada (1 md)** | Cetak biru / rancangan resmi (niat desain sebelum dibangun). Berisi STRUCTURE.md ini |
| `compliance/` | compliance | ada (8 md) | Basis & bukti kepatuhan terhadap aturan |
| `engineering/` | engineering | ada (46 md, 1 root README + subfolder) | Laporan rekayasa & catatan proses (ringkas). Subfolder: decisions(8), journals(7), references(26), roadmap(2), templates(2); reports/ kosong - akan terisi laporan ringkas baru |
| `runtime/` | runtime | ada (15 md) | Spesifikasi & referensi runtime |
| `core/` | foundation | ada (2 md) | Fondasi tambahan (Execution Model, Thinking Protocol) |
| `design/` | engineering | ada (30 md) | **DIPINDAH ke dalam `engineering/`** (keputusan Van) hasil rancangan/jejak |

> Catatan: `blueprints` (jamak) TIDAK dipakai keputusan Van: pakai `blueprint` (tunggal) saja. Kode menerima keduanya; kita pilih satu.

---

## 4. File Root Wajib (kontrak kode — UPDATED 2026-08-07)

**Status: `_ROOT_FILE_TYPES` kini KOSONG.** Seluruh 9 dokumen foundation (`MISSION.md`, `VISION.md`, `CHARTER.md`, `CONSTITUTION.md`, `GOVERNANCE.md`, `PHILOSOPHY.md`, `PRINCIPLES.md`, `GLOSSARY.md`, `CITIZEN_SPECIFICATION.md`) **dipindah ke `docs/foundation/`** (2026-08-07) dan dipindai lewat `_DOC_DIR_TYPES["docs/foundation"]`. Komentar kode (`loader.py`) menjelaskan: "moved to docs/foundation/ ... intentionally absent from this root map to keep compliance aligned with the actual repository layout."

**Tidak ada dokumen foundation yang wajib di root repo lagi.** Root hanya berisi file package (`_PACKAGE_TYPES`: pyproject.toml, README.md, setup.py, setup.cfg).

> Catatan authority: `_authority_for_type("foundation")` → `"CONSTITUTION"` (L205) hanya label otoritas, bukan merujuk lokasi file. Karena semua foundation kini di `docs/foundation/`, tidak ada pemindahan ke root yang diperlukan.

---

## 5. Struktur Dipertahankan (bukan kontrak kode, tapi aset penting)

| Folder `docs/...` | Peran |
|---|---|
| `user/` | Panduan pengguna (instalasi, CLI, REST API, integrasi) |
| `releases/` | Manifest rilis, daftar versi, riwayat rilis |
| `templates/` | Template dokumen |
| `assets/` | Aset pendukung (gambar, dsb.) |
| `operations/` | Catatan operasional |
| `performance/` | Catatan performa |
| `security/` | Catatan keamanan |

---

## 6. History Arsip (JANGAN dihapus, JANGAN di-scan compliance)

`docs/history/` = arsip seluruh jejak masa lalu. Kode compliance **tidak** memindai folder ini (tidak ada di `_DOC_DIR_TYPES`), jadi isinya murni dokumentasi historis.

> **Status 2026-08-07 (SAM 1.0 Foundation):** folder ini sementara **kosong**. Seluruh arsip masa lalu (sprint-reports ~210 md, reports ~62 md, Program A-K, release R-001, ADR lama, architecture lama, audit 3 md, legacy v3.x) telah diarsipkan ke **backup eksternal arsip proyek** (di luar repo, tidak di-commit). Folder `docs/history/` tetap dipertahankan untuk menampung arsip masa depan.

Yang masuk sini (ke depan):
- **Program AK** (laporan lengkap fase pengembangan)
- **Product-Release** (laporan rilis lama)
- **runtime-evolution** (evolusi runtime: R4, R5, E1, dan jejak perjalanan lain)
- **sprint-reports** (laporan sprint)
- Dokumen "jalan" (review/closure/audit/validation) yang bukan hasil akhir

> Prinsip: isi arsip tetap dibaca siapa pun yang ingin tahu "kenapa keputusan ini muncul". Engineering harian tidak perlu membukanya.

---

## 7. Folder yang Disatukan / Kosong (keputusan tata kelola)

| Saat ini | Aksi |
|---|---|
| `design/` (30 md) | **Pindah isi `docs/engineering/design/`** dianggap engineering oleh kode |
| `backlog/`, `glossary/`, `research/`, `decisions/`, `knowledge/`, `playbooks/`, `incidents/` (kosong) | **Satukan ke folder yang paling dekat perannya** dokumen tidak boleh "tergelantung" di folder tanpa definisi |
| `development/`, `documentation/`, `implementation/`, `models/` | Tumpang tindih satukan/map ke folder kontrak (engineering/architecture) |
| `__pycache__/` | Hapus (sampah Python, bukan bagian repo) |

---

## 8. Struktur Target SAM 1.0 (ringkas)

```
SAM/
 docs/
 foundation/ misi & identitas (9 md, versi 1.0.0; FROZEN, read-only)
 specifications/ spesifikasi resmi
 architecture/ desain & fondasi arsitektur (FROZEN)
 blueprint/ cetak biru / rancangan (termasuk STRUCTURE.md)
 adr/ keputusan arsitektur (immutable)
 runtime/ spesifikasi runtime
 engineering/ laporan rekayasa (ringkas; 46 md) berisi design/
 compliance/ bukti kepatuhan
 core/ fondasi tambahan
 user/ panduan pengguna
 releases/ rilis (manifest, checklist)
 templates/ template
 assets/ aset
 operations/ operasional
 performance/ performa
 security/ keamanan
 history/ ARSIP (kosong 2026-08-07; backup eksternal; akan terisi lagi)
 src/ kode sumber
 tests/ pengujian
 scripts/ skrip pendukung
 README.md
 pyproject.toml (root; foundation ada di docs/foundation/, tidak di root)
```

---

## 9. Prosedur Eksekusi Aman

1. **Backup** state sebelum memindahkan (git commit "checkpoint" atau catatan file id).
2. **Pindah satu kategori per langkah**, verifikasi kode compliance masih berjalan:
 - `design/` dalam `engineering/`
 - `CONSTITUTION.md`, `PHILOSOPHY.md` ke root
 - `backlog/glossary/research/...` ke folder target
3. **Jalankan baseline compliance** sebelum & sesudah buktikan tidak ada dokumen yang hilang dari scan, atau catat perubahan sadar.
4. **Jangan pernah `rm` permanen** pakai pindah/arsip. History tetap ada.

---
*Dokumen ini disusun berdasarkan kode compliance + visi SAM 1.0 Foundation. Wajib direview Van sebelum eksekusi.*

