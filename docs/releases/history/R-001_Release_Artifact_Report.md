# R2 - Release Artifact Verification Report

**Engineering Package:** ENG-R-001 (Product Release)
**Fase:** R2 - Release Artifact Verification (read-only)
**Executor:** ZARA
**Tanggal:** 2026-08-06

> Verifikasi keberadaan dan konsistensi artefak rilis Project SAM pada HEAD
> `e0c52f3` (versi arsitektural 30.0.0). Tidak membuat capability baru.

---

## 1. Keberadaan Artefak

| Artefak | Ada? | Keterangan |
|---|---|---|
| Wheel (`sam_ops-30.0.0-py3-none-any.whl`) | LULUS (build-temp) | 2.695.130 bytes, 2575 entri |
| Source dist (`sam_ops-30.0.0.tar.gz`) | LULUS (build-temp) | 1.661.648 bytes, 2910 entri |
| LICENSE | LULUS | Apache License 2.0 (`LICENSE`) |
| README | LULUS | `README.md` |
| CHANGELOG | LULUS | `CHANGELOG.md` |
| Release notes | LULUS | `docs/releases/release_notes/v1.0.md`, `v29.md`, `v30.md` |
| Manifest & versi | LULUS | `docs/releases/manifest.md`, `version-history.md` |
| Launcher entry point | LULUS | `sam.launcher.cli_entry` (5 entry) |

> Wheel/sdist dibangun dari HEAD ke folder temp (di luar repo) untuk verifikasi
> tanpa mengotori working tree; bukan artefak yang di-commit ke repo.

## 2. Konsistensi Metadata Wheel

| Field | Nilai pada wheel | Konsisten? |
|---|---|---|
| Name | `sam-ops` | LULUS (sama dengan `pyproject name`) |
| Version | `30.0.0` | LULUS |
| License | `Apache-2.0` | LULUS (sesuai `LICENSE`) |
| Requires-Python | `>=3.8` | LULUS |
| License-File | `LICENSE` | LULUS |

## 3. Dependency pada Wheel

Dependency inti yang tercantum (`Requires-Dist`):

- `structlog>=21.0`
- `pydantic<3,>=1.10`
- Extra `console`: `rich`, `typer`, `pyyaml`, `aiosqlite`, `anyio`
- Extra `desktop`: `PySide6>=6.5`
- Extra `server`: `fastapi`, `uvicorn`, `httpx>=0.24`, `jinja2`
- Extra `all`: gabungan console+desktop+server
- Extra `dev`: pytest, ruff, build, wheel, setuptools, dll.

> **Catatan:** `httpx` (dipakai Program K2 - `ProviderExecutor`) sudah terdaftar
> pada `extra == server` dan wheel menyertakannya. Konsisten dengan implementasi.

## 4. Entry Points (console_scripts)

| Command | Target |
|---|---|
| `sam` | `sam.launcher.cli_entry:sam_main` |
| `sam-console` | `sam.launcher.cli_entry:console_main` |
| `sam-desktop` | `sam.launcher.cli_entry:desktop_main` |
| `sam-diagnostic` | `sam.launcher.cli_entry:diagnostic_main` |
| `sam-headless` | `sam.launcher.cli_entry:headless_main` |

## 5. Program K Termasuk dalam Distribusi

| Modul | Di wheel? | Di sdist? |
|---|---|---|
| `src/sam/api/llm_wiring.py` | LULUS | LULUS |
| `src/sam/providers/execution/provider_executor.py` | LULUS | LULUS |

Program K (aktivasi jalur LLM) telah **masuk ke dalam artefak rilis** - distribusi
mencerminkan implementasi HEAD.

---

## Temuan R2 (non-blocking)

| ID | Tingkat | Temuan |
|---|---|---|
| R2-1 | Rendah (dokumentasi) | `CHANGELOG.md` belum mencatat Program K (aktivasi LLM). Perlu ditambahkan pada fase R7 (Release Notes). Tidak mengubah implementasi. |
| R2-2 | Info | Wheel/sdist dibangun untuk verifikasi dan tidak di-commit ke repo (sesuai `.gitignore`: `dist/`, `build/`). |

## Ringkasan

Seluruh artefak rilis inti **terverifikasi ada dan konsisten** dengan versi
`30.0.0` dan implementasi HEAD. **R2 status: PASS** dengan 1 temuan dokumentasi
rendah (R2-1) yang akan dituntaskan pada R7.
