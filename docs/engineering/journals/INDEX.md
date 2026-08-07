# docs/engineering/journals — Catatan Kerja & Riset

Folder ini = catatan kerja / riset engineering yang **masih dirujuk** (ringkas; bukan report final).
Yang selesai permanen → report/history.

## Riset Repository (RSR) & Keputusan Terkait

| Dokumen | Lokasi | Nilai |
|---|---|---|
| **Ringkasan Sesi 2026-08-06** (posisi engineering, status gap, tata letak) | `journals/2026-08-06_ringkasan-sesi.md` | konteks lanjutan (tanpa file audit internal) |
| **Perbaikan Launcher 2026-08-07** (Desktop/CLI/Ops jalan; selaras 5 mode .bat) | `journals/2026-08-07_launcher-fix.md` | akar masalah & verifikasi 5 mode launcher |
| **Program G — Simulation Capability 2026-08-07** (SimulationEvidence/Engine/Integration + Preview & Dry Run; add ke ROADMAP) | `journals/2026-08-07_programg-simulation.md` | implementasi Simulation V1 + arah roadmap |

| Dokumen | Lokasi | Nilai |
|---|---|---|
| **RSR-A01** Activation Inventory Study | backup eksternal (arsip) | arsip (fase) |
| **RSR-I01** Intelligence Activation Study | backup eksternal (arsip) | arsip (fase) |
| **RSR-S10** Final Activation Decision | `docs/engineering/decisions/` (ringkasan); asli di catatan internal | keputusan S10 = TDR |
| RSR-S01..S09 (riset per-sesi) | catatan internal (referensi audit; sudah digantikan laporan sesi) | referensi audit; sudah digantikan laporan sesi |

## Prinsip isi journal
- Ringkas & struktural: Tujuan → Kerja → Hasil → Blocker → Handoff.
- Bukan diary/steno. Yang selesai permanen → `docs/engineering/reports/` / arsip eksternal.
- Catatan yang murni proses transient (plan sesi) tetap di luar repo (tidak di-commit).

## Navigasi
- Riset/keputusan bernilai → `docs/engineering/decisions/` + `docs/engineering/journals/`
- Laporan sesi final → `docs/engineering/reports/` / arsip eksternal
- Catatan kerja aktif per-sesi → tambahkan di folder ini (ringkas, bersih).
