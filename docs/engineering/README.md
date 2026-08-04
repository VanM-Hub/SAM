# docs/engineering — Proses Implementasi

Peran folder ini (sesuai filosofi ATLAS): **proses implementasi yang hidup**.
Dokumen di sini = peran **Engineering**; pisah dari Architecture (aturan) & History (arsip).

## Struktur

```
docs/engineering/
├── decisions/    ← Keputusan engineering/arsitektur implementasi (AD-ENG-001..003, AD-S*)
├── reports/      ← Laporan sesi/release yang masih relevan (Engineering Session Report)
├── journals/     ← Catatan kerja per-sesi/area (aktif; ringkas)
└── templates/    ← Template laporan/ADR/keputusan (format baku)
```

## Aturan
- **`decisions/`** = keputusan yang menjadi dasar implementasi (record; jangan edit, tambah AD baru).
- **`reports/`** = hasil akhir yang masih dirujuk. Yang **selesai permanen & tak lagi dirujuk** → pindah ke `docs/history/`.
- **`journals/`** = kerja aktif lintas sesi; ringkas (tujuan → kerja → hasil → blocker → handoff). Yang selesai → report/history.
- **`templates/`** = format baku utk laporan/ADR/keputusan baru.

## Dokumen Keputusan (decisions/)
- `AD-ENG-001_Activation_Readiness_Rule.md`
- `AD-ENG-002_Activation_Pattern_Standard.md`
- `AD-ENG-003_Engineering_Session_Eligibility.md`
- (AD-S02..S09 keputusan sesi — lihat `docs/engineering/decisions/`)

## Navigasi
- Ingin laporan sesi → `docs/engineering/reports/`
- Ingin keputusan → `docs/engineering/decisions/`
- Ingin catatan kerja → `docs/engineering/journals/`
- Ingin template → `docs/engineering/templates/`
- Ingin arsip lama → `docs/history/`
