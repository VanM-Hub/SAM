# R6 - Release Packaging Report

**Engineering Package:** ENG-R-001 (Product Release)
**Fase:** R6 - Release Packaging Verification (read-only)
**Executor:** ZARA
**Tanggal:** 2026-08-06

> Verifikasi kemasan distribusi Project SAM (struktur, metadata, manifest,
> versi, dependency) terhadap HEAD `e0c52f3` versi `30.0.0`. Tidak mengubah kode.

---

## 1. Struktur Release

| Artefak | Status |
|---|---|
| Wheel (`sam_ops-30.0.0-py3-none-any.whl`) | LULUS (2575 entri; modul `sam/` lengkap) |
| Source dist (`sam_ops-30.0.0.tar.gz`) | LULUS (2910 entri) |
| `LICENSE` (Apache-2.0) | LULUS disertakan |
| `README.md`, `CHANGELOG.md`, `pyproject.toml` | LULUS |
| Entry points console_scripts | LULUS 5 (sam, sam-console, sam-desktop, sam-diagnostic, sam-headless) |

Struktur distribusi sesuai konvensi Python packaging; modul Program K
(`llm_wiring`, `provider_executor`) terverifikasi masuk wheel & sdist (R2).

## 2. Metadata

| Field | `pyproject` / manifest | Wheel METADATA | Konsisten |
|---|---|---|---|
| Name | `sam-ops` | `sam-ops` | LULUS |
| Version | `30.0.0` | `30.0.0` | LULUS |
| License | Apache-2.0 | `Apache-2.0` | LULUS |
| Requires-Python | `>=3.8` | `>=3.8` | LULUS |

## 3. Manifest (`docs/releases/manifest.md`)

- Versi: `v30.0.0` LULUS
- License Apache-2.0, Python >=3.8, Build setuptools, Test pytest LULUS
- Dependencies: core (structlog, pydantic), console (rich, typer, pyyaml),
  desktop (PySide6), server (fastapi, uvicorn, httpx, jinja2), dev LULUS
- Subsystem Map mencakup Program A-F (Preview-only -> Runtime Service) LULUS

**Temuan R6-1 (rendah, dokumentasi):** header manifest `Baseline` masih menunjuk
`f4edb87` (baseline EP-001/EP-002) dan Subsystem Map belum mencatat Program
G-K (Conversation/Dashboard/CLI/REST presentation hosts, jalur LLM aktif).
Pembaruan dilakukan pada R7.

## 4. Versi (konsistensi global)

| File | Hit `30.0.0` | Status |
|---|---|---|
| `README.md` | 1 | LULUS |
| `CHANGELOG.md` | 3 | LULUS |
| `ROADMAP.md` | 3 | LULUS |
| `pyproject.toml` | 1 | LULUS |
| `docs/releases/manifest.md` | 4 | LULUS |
| `docs/releases/release_notes/v30.md` | 5 | LULUS |
| `docs/releases/version-history.md` | - | [WARN] belum catat Program G-K (R7) |

## 5. Dependency

- Wheel `Requires-Dist` mencakup seluruh dependency inti + extra (console,
  desktop, server, dev) - konsisten dengan `[project.optional-dependencies]`.
- `httpx` (Program K2) terdaftar pada extra `server` LULUS.

---

## Kesimpulan R6

Kemasan distribusi (wheel, sdist, metadata, manifest, versi, dependency)
**terverifikasi valid dan konsisten**. Tidak ada perubahan kode. Dua gap
dokumentasi release dituntaskan pada R7 (manifest baseline + version-history).
**R6 status: PASS** (dengan catatan dokumentasi R6-1).
