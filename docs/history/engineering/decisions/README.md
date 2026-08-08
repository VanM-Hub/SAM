# docs/engineering/decisions — Keputusan Engineering

Folder ini = **rekam keputusan engineering/arsitektur-implementasi** (Engineering Decision).
Berisi keputusan yang menjadi dasar implementasi. **Jangan diedit** — jika keputusan berubah, tambahkan dokumen keputusan baru (AD).

## Peran
- Mencatat keputusan aktif yang berdampak pada cara engineering bekerja (via Activation Pattern, DI, dsb).
- Berlaku sebagai dasar implementasi (bukan opini/rencana).

## Isi (umumnya AD-*)
- `AD-ENG-001_Activation_Readiness_Rule.md`
- `AD-ENG-002_Activation_Pattern_Standard.md`
- `AD-ENG-003_Engineering_Session_Eligibility.md`
- `AD-S02-001_Payload_Execution_Context.md`
- `AD-S03-001_Provider_Preview_Integration.md`
- `AD-S04_Presentation_RuntimeService_DI.md`
- `AD-S05_Knowledge_Memory_Activation.md`

## Aturan
- **Record-only**: jangan edit AD yang sudah ada; tambah AD baru bila terjadi perubahan keputusan.
- Keputusan arsitektur (bukan engineering) → `docs/adr/`, bukan folder ini.

## Navigasi
- Keputusan engineering → di sini
- Keputusan arsitektur → `docs/adr/`
- Catatan kerja aktif → `docs/engineering/journals/`
