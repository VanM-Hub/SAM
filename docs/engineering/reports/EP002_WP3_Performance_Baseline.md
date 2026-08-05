# EP-002 — WP-3 Performance Baseline: Engineering Report

**Date:** 2026-08-06 · **Status: ✅ Completed**

## Tujuan
Performance Baseline Report — ukur startup, preview, workflow, memory, package size. **Tidak melakukan optimasi; hanya membangun baseline.**

## Pengukuran (baseline di mesin ini — Windows / Python 3.8.7)
| Metrik | Nilai | Catatan |
|---|---|---|
| Package size (source) | 2547 file `.py`, ~7.2 MB | keseluruhan `src/sam` |
| Startup (import `launcher.cli_entry`) | 0.312 s | waktu import pipeline launcher |
| Preview execution | 0.0002 s | satu preview (preview-only, tanpa provider call) |
| Workflow list (`workflow_consumer.list_workflows`) | <0.0001 s (n=0) | registry kosong (belum ada workflow di-register) |
| Memory (tracemalloc peak, import `web.server`) | 37.4 MB | footprint import web + objek |

## Evidence
- Timing via `time.perf_counter` & `tracemalloc`; hitung file & ukuran.

## Risiko / Kesimpulan
- Ini **baseline kasar** (bukan benchmark resmi/standar), cukup sebagai titik referensi. Preview sangat cepat (preview-only, konsisten ADR-024). Startup reasonable. Memory wajar untuk platform besar.
- **Tidak ada optimasi dilakukan** (sesuai instruksi — baseline dulu). Tidak ada perubahan Architecture/kode.

## Verification Report (WP-3)
- Test: pengukuran berhasil (semua metrik tercatat). Working tree clean.
- **Keputusan WP-3: ✅ Completed** (baseline dibangun; tanpa optimasi).
