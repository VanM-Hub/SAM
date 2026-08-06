# R1 - Release Audit Report

**Engineering Package:** ENG-R-001 (Product Release)
**Fase:** R1 - Release Audit (Read-only)
**Executor:** ZARA
**Tanggal:** 2026-08-06

> Laporan fase R1 - audit kondisi rilis Project SAM berdasarkan baseline program
> G-K yang telah selesai, tanpa perubahan implementasi maupun arsitektur.

---

## 1. HEAD Commit

| Item | Nilai |
|---|---|
| Commit hash | `e0c52f3` |
| Subjek | `chore: hapus tests/legacy (test warisan v1.0 yang usang)` |
| Tanggal | 2026-08-06 16:57:13 +0800 |
| Branch | `main` |

HEAD berada pada garis keturunan stabilisasi v30.0.0 setelah penyelesaian
Engineering Package Program G-K dan pembersihan test legacy.

## 2. Version

| Item | Nilai |
|---|---|
| `pyproject.toml` | `version = "30.0.0"` |
| Nama distribusi | `sam_ops` |
| `requires-python` | `>=3.8` |
| Build backend | `setuptools.build_meta` (`setuptools>=64`, `wheel`) |

Versi arsitektural **tetap `30.0.0`**. Seluruh perubahan sejak tag `v30.0.0`
(Program G, H, I, J, K + stabilisasi dokumentasi) berada dalam garis keturunan
v30.0.0 dan tidak membentuk versi arsitektural baru - konsisten dengan catatan
stabilisasi pada `docs/releases/release_notes/v30.md`.

## 3. Tag Readiness

| Item | Nilai |
|---|---|
| Tag terbaru | `v30.0.0` |
| Commit yang ditunjuk tag `v30.0.0` | `781c630` (commit Program F) |
| HEAD (`e0c52f3`) sudah ditag? | **Belum** |
| Commit post-tag dalam garis v30.0.0 | 4+ (Program G-K, docs, cleanup) |

HEAD **belum ditandai**. Mengikuti precedent `v30.md` (stabilisasi EP-001/EP-002
tidak membuat tag atau versi baru), perubahan post-v30.0.0 pada fase release ini
**tidak menambah tag arsitektural baru**; status rilis tercatat di manifest dan
release notes.

## 4. Working Tree

| Item | Status |
|---|---|
| `git status --porcelain` | **Bersih (kosong)** |
| ZaraNote / file database | 0 ikut ter-commit |
| Non-ASCII pada workflow `.yml` | 0 |
| Path lokal pada file ter-commit | 0 |
| Test tidak pada root repo, `__pycache__` | 0 / di-ignore |

Working tree bersih dan siap untuk proses rilis.

## 5. Branch Utama Sinkron

| Item | Nilai |
|---|---|
| Branch aktif | `main` |
| Ahead dari `origin/main` | 0 |
| Behind `origin/main` | 0 |
| Status | **Sinkron** |

Semua commit (termasuk Program K `9ddb5ad`, docs `4c9cf1a`, cleanup `e0c52f3`)
sudah di-push ke `origin/main`.

## 6. Build Reproducible

| Item | Nilai |
|---|---|
| Python | 3.12.13 |
| `build` | 1.5.0 |
| `setuptools` | 83.0.0 |
| Hasil build | `sam_ops-30.0.0-py3-none-any.whl` + `sam_ops-30.0.0.tar.gz` |
| Lokasi uji | folder temp (di luar repo) - tidak mengotori working tree |

Build dari HEAD **berhasil** menghasilkan wheel dan sdist yang konsisten dengan
versi `30.0.0`. Working tree tetap bersih setelah build.

---

## Ringkasan R1

| Kriteria | Status |
|---|---|
| HEAD commit | LULUS `e0c52f3` |
| Version | LULUS `30.0.0` (tetap, tanpa bump) |
| Tag readiness | [WARN] HEAD belum ditag - konsisten precedent stabilization (tanpa tag baru) |
| Working tree bersih | LULUS |
| Branch sinkron | LULUS `main == origin/main` |
| Build reproducible | LULUS wheel + sdist berhasil |

R1 **PASS** (kecuali catatan tag readiness yang mengikuti precedent v30.0.0
stabilisasi: tanpa tag arsitektural baru untuk perubahan non-arketektural).
