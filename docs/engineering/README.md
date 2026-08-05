# docs/engineering — Proses Implementasi

Peran folder ini (sesuai filosofi ATLAS): **proses implementasi yang hidup**.
Dokumen di sini = peran **Engineering**; pisah dari Architecture (aturan) & History (arsip).

## Struktur

```
docs/engineering/
├── decisions/    ← Keputusan engineering/arsitektur implementasi (AD-ENG-001..003, AD-S*)
├── reports/      ← Laporan sesi/release yang masih relevan (Engineering Session Report)
├── journals/     ← Catatan kerja per-sesi/area (aktif; ringkas)
├── references/   ← Referensi engineering yang tidak lapuk (EC-001..025, format laporan)
├── roadmap/      ← Rencana kerja Engineering (Engineering Plan; bukan Source of Truth)
└── templates/    ← Template laporan/ADR/keputusan (format baku)
```

## Aturan
- **`decisions/`** = keputusan yang menjadi dasar implementasi (record; jangan edit, tambah AD baru).
- **`reports/`** = hasil akhir yang masih dirujuk. Yang **selesai permanen & tak lagi dirujuk** → pindah ke `docs/history/`.
- **`journals/`** = kerja aktif lintas sesi; ringkas (tujuan → kerja → hasil → blocker → handoff). Yang selesai → report/history.
- **`references/`** = pengetahuan engineering bernilai tetap (aturan, pola, kosakata, direktori status capability) — bukan keputusan, bukan journal.
- **`roadmap/`** = rencana kerja Engineering (Engineering Plan). Bukan Source of Truth arsitektur; tidak berisi keputusan ADR/spesifikasi/boundary.
- **`templates/`** = format baku utk laporan/ADR/keputusan baru.

## Dokumen Keputusan (decisions/)
- `AD-ENG-001_Activation_Readiness_Rule.md`
- `AD-ENG-002_Activation_Pattern_Standard.md`
- `AD-ENG-003_Engineering_Session_Eligibility.md`
- `AD-S02-001_Payload_Execution_Context.md`
- `AD-S03-001_Provider_Preview_Integration.md`
- `AD-S04_Presentation_RuntimeService_DI.md`
- `AD-S05_Knowledge_Memory_Activation.md`
- (keputusan sesi lain: lihat isi folder)

## Referensi (references/)
- `README.md` (indeks)
- `EC-001..EC-025` — konteks engineering (peta/aturan/pola/kosakata/readiness) dari fase engineering
- `Format_Laporan_Engineer.md` — format baku laporan sesi

## Navigasi
- Ingin rencana kerja → `docs/engineering/roadmap/ROADMAP_ENGINEERING.md`
- Ingin laporan sesi → `docs/engineering/reports/`
- Ingin keputusan → `docs/engineering/decisions/`
- Ingin catatan kerja → `docs/engineering/journals/`
- Ingin referensi/konteks → `docs/engineering/references/`
- Ingin template → `docs/engineering/templates/`
- Ingin arsip lama → `docs/history/`
