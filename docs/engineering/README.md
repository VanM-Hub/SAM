# docs/engineering — Proses Implementasi

Peran folder ini (sesuai filosofi ATLAS): **proses implementasi yang hidup**.
Dokumen di sini = peran **Engineering**; pisah dari Architecture (aturan) & History (arsip).

## Struktur

```
docs/engineering/
├── decisions/    ← Keputusan engineering/arsitektur implementasi (AD-ENG-001..003, AD-S*)
├── reports/      ← Laporan sesi/kerja BERJALAN (ringkas); laporan program SELESAI -> docs/history/reports/
├── journals/     ← Catatan kerja per-sesi/area (aktif; ringkas)
├── strategy/     ← Strategi pengembangan SAM 2.x (DEVELOPMENT_STRATEGY, Planning Standard, Readiness Model)
├── roadmap/      ← Rencana kerja SAM 2.x (ROADMAP SAM 2.x, Program A–E, Milestone, Appendix)
└── templates/    ← Template laporan/ADR/keputusan (format baku)
```

## Aturan
- **`decisions/`** = keputusan yang menjadi dasar implementasi (record; jangan edit, tambah AD baru).
- **`reports/`** = hasil akhir yang masih dirujuk. Yang **selesai permanen & tak lagi dirujuk** → diarsipkan (backup eksternal) / `docs/history/`.
- **`journals/`** = kerja aktif lintas sesi; ringkas (tujuan → kerja → hasil → blocker → handoff). Yang selesai → report/history.
- **`strategy/`** = arah strategis SAM 2.x (Sumber kebenaran strategi: Development Strategy → Planning Standard → Readiness Model).
- **`roadmap/`** = rencana kerja Engineering (Engineering Plan; bukan Source of Truth arsitektur); berisi ROADMAP SAM 2.x + Program A–E + Milestone + Appendix.
- **`templates/`** = format baku utk laporan/ADR/keputusan baru (incl. Format_Laporan_Engineer).

## Dokumen Keputusan (decisions/)
- `AD-ENG-001_Activation_Readiness_Rule.md`
- `AD-ENG-002_Activation_Pattern_Standard.md`
- `AD-ENG-003_Engineering_Session_Eligibility.md`
- `AD-S02-001_Payload_Execution_Context.md`
- `AD-S03-001_Provider_Preview_Integration.md`
- `AD-S04_Presentation_RuntimeService_DI.md`
- `AD-S05_Knowledge_Memory_Activation.md`
- (keputusan sesi lain: lihat isi folder)

## Navigasi
- Ingin strategi pengembangan → `docs/engineering/strategy/`
- Ingin rencana kerja/roadmap → `docs/engineering/roadmap/ROADMAP SAM 2.x.md`
- Ingin laporan sesi baru → `docs/engineering/reports/` (laporan sesi berjalan); laporan program selesai -> docs/history/reports/
- Ingin keputusan → `docs/engineering/decisions/`
- Ingin catatan kerja → `docs/engineering/journals/`
- Ingin template → `docs/engineering/templates/`
- Ingin arsip lama → `docs/history/`
