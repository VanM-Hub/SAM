# P8 — Real Investigation

> **Jenis:** Real External E2E (Truth Matrix DoD).
> **Status:** ✅ **PROVEN** — real observation → evidence → diagnosis → root cause → recommendation → lineage.
> **Tanggal:** 2026-08-12 · **Penulis:** Zara (Engineer)

---

## 1. Tujuan

Membuktikan SAM bisa melakukan **Investigasi NYATA** — bukan `investigation("some text")`,
melainkan input dari **state eksternal nyata** (file di disk) yang diobservasi, dijadikan evidence,
didiagnosis, dicari root cause, dan diberi rekomendasi dengan **jejak asal (lineage) yang terdokumentasi**.

---

## 2. Environment

Filesystem (sudah PROVEN P3/P6) sebagai environment pertama. Tiga file nyata di `_demo/`:

| File | Isi | Fakta Nyata |
|---|---|---|
| `env_empty.log` | kosong | 0 baris · size 0 → **EMPTY_FILE** |
| `env_sparse.log` | 8 baris, 5 kosong | rasio kosong tinggi → **SPARSE** |
| `env_healthy.log` | log sehat | 16 baris, 0 kosong → **USABLE** |

Semua diobservasi langsung dari disk (bukan string buatan).

---

## 3. Rantai yang Terbukti

1. **Real Observation** — baca stat/isi file nyata (`observation.collect`): line_count, empty_lines, size.
2. **Evidence** — ekstrak fakta terverifikasi per sumber, beri label kualitas (EMPTY/SPARSE/USABLE).
3. **Investigation → Diagnosis** — tiap evidence didiagnosis (root cause per file).
4. **Root Cause** — agregat: `FILE_KOSONG (1)` + `DATA_SPARSE`.
5. **Recommendation** — berbasis bukti: `TAMBAH_DATA` (file kosong), `BERSIHKAN_ATAU_PADATKAN` (sparse).
6. **Evidence Lineage** — edge `derived_from` (evidence→observation) + `addresses` (recommendation→evidence) terdokumentasi penuh.

---

## 4. Hasil

- 3 observasi nyata → 3 evidence → 3 diagnosis → 2 rekomendasi.
- Root cause keseluruhan: **FILE_KOSONG (1)**.
- Lineage: 8 node + 5 edge (semua menunjuk ke sumber asli di disk).
- Audit: `observation.collect` per file + `investigation.complete`.
- Bukti JSON: `_demo/p8_investigation.json`.

---

## 5. Verdict

> **Investigation capability = PROVEN.** SAM membaca state eksternal nyata, mengubahnya jadi
> evidence terverifikasi, mendiagnosis root cause, memberi rekomendasi berbasis bukti, dan
> membangun **evidence lineage** lengkap — melampaui klaim lama "analisis data internal" (UNPROVEN).

---

## 6. Batasan (jujur)

- Environment saat ini = filesystem (log/teks). Belum observasi sistem live/service/network.
- Diagnosis berbasis aturan heuristik pada statistik file; belum AI-driven (butuh P4).
- Belum terhubung ke Recovery (P9) & Learning (P10) satu rantai — itu diselesaikan di P11.

---

## 7. Artefak

- Kode: `src/sam/execution_runtime/real_harness_investigation.py`
- Env uji: `_demo/env_empty.log`, `_demo/env_sparse.log`, `_demo/env_healthy.log`
- Bukti JSON: `_demo/p8_investigation.json`

---

*Artefak P8. Investigasi nyata terbukti: diagnosa berbasis fakta dari disk, bukan teks buatan.*
