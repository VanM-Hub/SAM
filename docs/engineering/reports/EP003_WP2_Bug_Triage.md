# EP-003 — WP-2 Bug Triage: Engineering Report

**Date:** 2026-08-06 · **Status: ✅ Completed** (triage; belum diperbaiki).

## Tujuan
Mengelompokkan bug yang diketahui ke kategori P1-Critical/P2-Major/P3-Minor/P4-Cosmetic, dengan reproduksi/root cause/impact/owner. **Belum diperbaiki pada WP ini.**

## Tabel Bug Triage
| ID | Kategori | Reproduksi | Root Cause | Impact | Owner |
|---|---|---|---|---|---|
| S10-TDR-001 | **P2 Major** | `import sam.reasoning` → `ImportError: cannot import name 'ExecutionGraphEngine' from 'sam.execution.engine'` | kelas `ExecutionGraphEngine` tidak ada di `sam.execution.engine` (world lama); reference putus | modul legacy `sam.reasoning` tidak dapat di-import; bukan jalur produksi; fix penuh = rekonsiliasi world-lama (TD-3, butuh arsitektur) | Engineering backlog (rekonsiliasi butuh keputusan arsitektur) |
| ENG-BUG-001 | **P3 Minor** | `test_two_runs_same_structure` — pass saat isolasi (0.08s), kadang gagal di suite penuh | interferensi/ordering antar-test (flaky) | suite compliance kadang gagal 1 (stability) tanpa regresi logika | Engineering backlog (backlog; jangan diperbaiki sekarang) |
| ENG-DEBT-001 | **P3 Minor** | `sam/runtime/discovery.py` import `sam.validation` (tak ada) | modul `sam.validation` hilang (legacy); fungsi di file memakainya | dead/broken module bukan jalur produksi; removal butuh keputusan ownership | Engineering (deferred; removal = TD-3) |
| VAL-001 | **P3 Minor** | `validate_layers.py` SIGKILL saat full scan | file walks full tree (os.walk) berat | layer validation tak bisa full-scan (tooling) | Engineering (scoping tooling = TD-2) |
| E6 | **P4 / konfigurasi** | auto-rerun CI failure | secret `ZARA_RERUN_TOKEN` (konfigurasi eksternal GitHub) | workflow helper manual gagal | bukan bug kode; dokumentasi (repo config eksternal) |

## P1 Critical
- **Tidak ada** bug P1 teridentifikasi (regression stabil, CI hijau, jalur produksi tidak terdampak).

## Kesimpulan
- Bug yang ada: **nihil P1**, **1 P2** (S10-TDR-001 legacy), **3 P3** (flaky, dead module, tooling), **1 P4/konfigurasi**. Semua **belum diperbaiki** pada WP ini (sesuai WP-2 / arahan "jangan fix tanpa evidence kebutuhan + dalam kewenangan"). Fix S10-TDR-001 (rekonsiliasi world-lama) menyentuh TD-3 → butuh keputusan arsitektur (bukan di sini).

## Verification Report (WP-2)
- Test: reproduksi S10-TDR-001 (ImportError) & ENG-BUG-001 (PASS isolasi) → klasifikasi berdasar bukti. Tidak ada perubahan kode.
- **Keputusan WP-2: ✅ Completed** (triage selesai; di bawah eskalasi guardrail untuk S10 fix penuh).
