# AD-ENG-003 — Engineering Session Eligibility + Baseline Project

**Status:** Accepted · **Tanggal:** 2026-08-04 · **Tipe:** Engineering Decision (fase transisi ke Operationalization)

Keputusan arsitektur (disampaikan via kolaborasi Chief Architect/Developer). Baseline
Project SAM — tidak diubah kecuali repository berubah nyata.

## Eligibility Checklist (Engineering Session)
Sebelum capability boleh jadi target Engineering Session, WAJIB lulus SEMUA:
- ✅ Registry tersedia
- ✅ Bridge tersedia
- ✅ Dapat di-DI ke entry
- ✅ Tidak butuh Runtime baru
- ✅ Tidak butuh Provider baru
- ✅ Tidak butuh Architecture Decision baru
- ✅ Punya Activation Pattern sesuai AD-ENG-002
- ✅ Memberi nilai operasional yang terukur

Satu saja ❌ → capability masuk **Architecture Backlog** (bukan target Engineering).
Menjadikan keputusan engineering **objektif**, bukan intuisi.

## Tiga Jenis Pekerjaan (pasca S10)
1. **Engineering Session** — mengaktifkan capability siap (ikut Activation Pattern).
2. **Architecture Session** — kebutuhan perubahan arsitektur (penyatuan dunia lama-baru).
3. **Maintenance Session** — bugfix/regression/dokumentasi/refactor kecil; tidak ubah
   arsitektur & tidak aktivasi capability baru.

## Definition of Success
Keberhasilan SAM BUKAN jumlah Runtime/folder/ADR/dokumen.
Keberhasilan SAM = "Semakin banyak capability yang **AKTIF** melalui Activation Pattern
Standard tanpa menambah kompleksitas arsitektur" — metrik terukur.

## Roadmap Engineering (arah SAM 2.x)
S01..S10 — lihat `docs/engineering/reports/` (Session Report) & `docs/engineering/roadmap/ROADMAP SAM 2.x.md` (prioritas program).

## Architecture Backlog (resmi)
Intelligence Runtime · Agent Runtime · Reasoning — sampai ada Architecture Decision baru
yang menunjukkan activation path nyata.

## Baseline Dokumen
- AD-ENG-001 (Activation Readiness Rule)
- AD-ENG-002 (Activation Pattern Standard)
- `docs/engineering/strategy/SAM Platform Readiness Model.md` (Readiness Levels)
- `docs/engineering/roadmap/ROADMAP SAM 2.x.md` (program & prioritas)
