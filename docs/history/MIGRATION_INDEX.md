# MIGRATION_INDEX - Arsip Laporan & Riwayat

Daftar migrasi arsip ke `docs/history/`. Folder ini read-only (arsip), bukan authority untuk keputusan baru.

## Aturan (dari `HISTORY_POLICY.md`)
- **Arsip tidak dihapus.** File yang sudah masuk `docs/history/` dipertahankan sebagai rekam jejak.
- Folder `docs/history/` = arsip; baca saja, jangan dipakai untuk keputusan baru.

## Migrasi 2026-08-08 - Program A-F Reports
**Sumber:** `docs/engineering/reports/` (live reports)
**Tujuan:** `docs/history/reports/`
**Jumlah:** 78 file (71 di root, 7 di subfolder `EA-001-E/`)
**Alasan:** Program A-F sudah CLOSED. Per aturan C1-A + ATLAS, laporan program selesai dipindah ke arsip; `docs/engineering/reports/` hanya untuk laporan sesi yang masih berjalan (live).

### Kosong setelah migrasi
- `docs/engineering/reports/` - folder live kini kosong (siap untuk laporan berjalan berikutnya)

### Catatan
- `WP-F5_SAM_2.0_Release_Recommendation.md`, `WP-F2/F3/F4` certification, dan verdict EA-M6/EA-C06/EA-002/EA-004 tetap ada di `docs/engineering/decisions/` + `journals/` (authority, bukan arsip) - TIDAK ikut dipindah.
- Migrasi menggunakan `git mv` (terdeteksi sebagai rename `R`) sehingga riwayat (history) file tetap utuh.

## Riwayat Migrasi Sebelumnya
- **C1-A (commit `d9a4949`)**: pindah 6 folder historis (sprint-reports, reports, legacy, program-e-reports, program-f-reports, audit) -> `docs/history/`. Folder lama `docs/engineering/reports/` (dibuat 2026-08-05) belum ikut saat itu; ditangani migrasi 2026-08-08 ini.
