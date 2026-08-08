# EA-001-001 — Deployment Inventory Report

**Program:** D (MISSION-2D — Production Readiness)
**Phase:** EA-001 — Production Readiness Assessment
**WP:** D1 — Deployment Assessment
**Type:** READ-ONLY ASSESSMENT (evidence only — no repository change)
**Date:** 2026-08-08
**Status:** COMPLETE

---

## Objective

Memetakan baseline deployment aktual SAM menuju Milestone M4 (Production Platform), berdasarkan pencapaian M3. Assessment hanya menghasilkan evidence terverifikasi.

---

## Evidence: Deployment Topology Aktual

| Aspek | Evidence | Referensi |
|---|---|---|
| Distribution | Python package (`sam-ops`), installable via pip; single-node deployment | `pyproject.toml` (project name, dependencies) |
| Entry points (5 CLI) | `sam`, `sam-console`, `sam-desktop`, `sam-headless`, `sam-diagnostic` | `pyproject.toml` `[project.scripts]` |
| Launcher modes (host) | console, desktop, headless, web, ops — via `.bat` scripts | `SAM_CLI.bat`, `SAM_Desktop.bat`, `SAM_Web.bat`, `SAM_Ops.bat`, `SAM_Run.bat` |
| Runtime environment | Python dalam `.venv` lokal; `PYTHONPATH` diarahkan ke `src` | `SAM_CLI.bat` (`".\.venv\Scripts\python.exe" -B ...`) |
| Workspace | Singleton working directory; default `os.getcwd()`, override via `SAM_WORKSPACE` env | `cli_entry.py:35` |
| Composition root | RuntimeService (all-in-one) + launcher pipeline | `runtime_service/`, `launcher/` |

**Keterangan topology:** SAM menganut single-node deployment. Tidak ada komponen server terpisah yang wajib (FastAPI server bersifat opsional extra `server`). Desktop memerlukan `PySide6` (extra `desktop`), server memerlukan `fastapi/uvicorn` (extra `server`).

---

## Evidence: Bootstrap Sequence

Pipeline startup resmi (urutan stage, synchronous):

```
APPLICATION → ENVIRONMENT → DIAGNOSTICS → CONFIGURATION
→ RUNTIME_REGISTRY → GUARDIAN_RUNTIME → HOST → READY
```

| Referensi | Isi |
|---|---|
| `launcher/startup_pipeline.py` | `PipelineStage` enum + `PIPELINE_ORDER` (8 stage berurutan) |
| `launcher/startup_pipeline.py` | `StartupPipeline.run()` — synchronous, tidak ada background worker |
| `launcher/runtime_bootstrap.py` | `RuntimeBootstrapOrchestrator` — orchestration, tanpa business logic |
| `launcher/runtime_registry.py` | `RuntimeRegistry`, `RuntimeType` + `RuntimeDescriptor` |
| `launcher/host_launcher.py` | `HostLauncher`, `HostLaunchResult`, `HostType` |
| `launcher/startup_report.py` | `StartupReport`, `StageResult`, `StartupIssue`, `IssueSeverity` |

---

## Evidence: Startup Dependency & Runtime Startup Ordering

Runtime diinisialisasi melalui `RuntimeBootstrapOrchestrator` dengan urutan:

```
Application → BootstrapManager → EnvironmentValidator → Diagnostics
→ Guardian Runtime → Host Manager → Host
```

Dependency utama composition:
- `config_loader.py` — `ConfigLoader`/`LauncherConfig` (immutable, `__slots__`)
- `environment.py` — `EnvironmentValidator` (memvalidasi env prasyarat)
- `diagnostics.py` — `DiagnosticsEngine`
- `runtime_registry.py` — registry runtime
- `host_manager.py` — `HostType`
- `startup_report.py` — pelaporan stage + issue

---

## Evidence: Configuration Loading

| Aspek | Evidence | Referensi |
|---|---|---|
| Konfigurasi launcher | `LauncherConfig` immutable via `__slots__`; field: theme, workspace, language, log_level, host, provider, refresh_rate, safe_mode, readonly | `launcher/config_loader.py` |
| Sumber konfigurasi | Nilai default ditimpa dari environment variable (`os.environ.get(env_key)`) | `config_loader.py:212` |
| Env-var utama | `SAM_WORKSPACE`, `SAM_HOST`, `SAM_SAFE_MODE`, `PYTHONPATH` | `cli_entry.py`, `config_loader.py` |
| Konfigurasi runtime | Dilakukan via Composition Root (RuntimeService) — bukan file `.env` root | `runtime_service/` |
| Validasi | `EnvironmentValidator` sebagai stage tersendiri di pipeline | `launcher/environment.py` |

---

## Evidence: Environment Requirements

| Kebutuhan | Detail | Referensi |
|---|---|---|
| Python | Wajib Python 3.10+ (pakai `asyncio.to_thread`, dataclasses, typing modern) | `pyproject.toml`; `persistence/database.py` (polyfill 3.8 note) |
| Dependency inti | `structlog`, `pydantic>=1.10,<3`, `psutil` | `pyproject.toml` `dependencies` |
| Extra optional | `console` (rich, typer, pyyaml, aiosqlite, anyio), `desktop` (PySide6), `server` (fastapi, uvicorn, httpx, jinja2) | `pyproject.toml` `[project.optional-dependencies]` |
| Persistence | SQLite via stdlib `sqlite3` (tidak butuh DB server eksternal) | `persistence/database.py` |
| Venv | `.venv` lokal di root project; launch script menunjuk ke sana | `SAM_*.bat` |
| Path | `PYTHONPATH` diarahkan ke `src` (hardcoded absolute path di `.bat`) | `SAM_CLI.bat` |

---

## Gaps Teridentifikasi (D1)

> Assessment mencatat gap sebagai gap — **TIDAK diperbaiki** dalam EA-001.

| ID | Gap | Severity | Keterangan |
|---|---|---|---|
| D1-G1 | **Deployment non-portable** — `.bat` scripts memakai absolute path `D:\Project AI\SAM` | **High** | Menghambat deployment ke environment lain tanpa edit manual; tidak mendukung relokasi/packaging terstandar |
| D1-G2 | Tidak ada environment profile terpisah (dev/staging/prod) — konfigurasi via env-var ad-hoc | **Medium** | `Environment Profiles` belum ada (roadmap D2.3) |
| D1-G3 | Entry point package belum diverifikasi instalasi clean-environment | **Low** | Roadmap D1.3 Environment Validation & D1.6 Installation Certification belum dieksekusi |

---

## Kesimpulan WP-D1

Baseline deployment SAM terdokumentasi: single-node Python package, 5 entry point, pipeline startup 8-stage synchronous, konfigurasi via env-var + LauncherConfig immutable, dependency modular via extras. Gap utama: **non-portable deployment path** (High), belum ada environment profiles (Medium), clean-install belum diverifikasi (Low).

*— Assessment read-only. Evidence = file kode + konfigurasi aktual repo.*
