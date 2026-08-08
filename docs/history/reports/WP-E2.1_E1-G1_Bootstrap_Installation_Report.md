# WP-E2.1 — E1-G1 Automatic Bootstrap Installation

**Mission:** MISSION-2E — Program E (Early Adopter Experience)
**Package:** AP-2E-001
**Work Package:** WP-E2.1 — Automatic Bootstrap Installation (Priority 1, E1-G1)
**Status:** DONE

---

## Gap yang Ditutup

**E1-G1** (dari EA-001-007 Early Adopter Readiness Matrix, High):
> Tidak ada bootstrap installer otomatis — pengguna menyiapkan SAM secara manual (venv + pip + PYTHONPATH).

## Objective Terpenuhi

"Menghilangkan friksi instalasi sehingga pengguna dapat menyiapkan SAM melalui satu proses bootstrap yang deterministik."

## Implementasi

Modul baru **`src/sam/devx/`** — Developer Experience capability (stand-alone, stdlib-only):

| File | Peran |
|---|---|
| `state.py` | DTOs immutable (ADR-023): `InstallationReport`, `DependencyCheck`, `ComponentCheck`, enums (`CheckStatus`, `CheckSeverity`, `DependencyStatus`, `EnvStatus`, `InstallPhase`) |
| `dependencies.py` | `DependencyChecker` — validasi python, pip, setuptools/wheel, `sam` importable |
| `environment.py` | `EnvironmentValidator` — validasi executable, venv, repo structure, PYTHONPATH, writable |
| `installer.py` | `BootstrapInstaller` + `bootstrap()` — orchestrator satu-perintah (6 fase berurutan) |
| `verifier.py` | `InstallationVerifier` — verifikasi import, version, entry points, first-run API |
| `report.py` | `InstallationReportBuilder` — laporan text & dict |
| `__init__.py` | 18 public exports |

## Alur (One-Command, Deterministik)

```
bootstrap()  ->  dependency_validation
             ->  environment_validation
             ->  environment_init        (venv create, opsional)
             ->  installation            (pip install -e ., opsional)
             ->  install_verification    (verify-after-install)
             ->  diagnostics
```

- **`apply=False` (default)** = dry-run: validasi + susun rencana, TIDAK mengubah filesystem.
- **`apply=True`** = eksekusi venv create + pip install via subprocess.
- Berhenti (break) pada blocking failure.
- **Design (fix CI):** dalam dry-run, phase `install_verification` mencatat "verification ditunda" (non-blocking) karena TIDAK ada instalasi nyata yang terjadi. Verifikasi import/entry-point/version hanya bermakna & dijalankan setelah `apply=True` benar-benar install. Ini membuat dry-run deterministik di semua environment (tidak menggantung pada apakah `sam` kebetulan importable dari proses pytest saat itu).

## Exit Criteria

| Kriteria | Status |
|---|---|
| One-command installation tersedia | ✅ `bootstrap()` / `sam.devx.BootstrapInstaller.run()` |
| Dependency tervalidasi otomatis | ✅ `DependencyChecker` (python/pip/build-backend/sam) |
| Environment tervalidasi | ✅ `EnvironmentValidator` (executable/venv/repo/PYTHONPATH/writable) |
| First-run berhasil tanpa konfigurasi manual | ✅ `InstallationVerifier.check_first_run()` |
| Tidak ada regresi | ✅ baseline 4290 passed (lihat Verifikasi) |

## Evidence

- **28 test** di `tests/integration/test_devx_bootstrap.py` (6 area + round-trip):
  - DependencyChecker 7, EnvironmentValidator 7, BootstrapInstaller 7, Verifier 4, ReportBuilder 3, Round-trip 1.
- Semua test memakai `tmp_path` fixture (BUKAN folder repo) — aman untuk CI baseline.
- Stand-alone: tidak menyentuh runtime/launcher/governance/Foundation existing.

## Verifikasi

| Scope | Hasil |
|---|---|
| Compile (7 file) | OK |
| `import sam.devx` | Clean, 18 exports |
| test_devx_bootstrap | **28/28 passed** |
| Integration suite (CI Python 3.11) | hijau (28 baru + suite existing) |
| Baseline CI scope | **4290 passed, 1 skipped, 2 xfailed** — **no regression** |

> Catatan: di mesin lokal (Python 3.8.7), `tests/integration/test_iam.py` gagal collection karena `frozenset[str]` (PEP 585 butuh 3.9+) — **pre-existing sejak H5 (commit 629854d)**, bukan regresi WP-E2.1. CI memakai Python 3.10–3.12 sehingga suite tersebut hijau di CI (telah terverifikasi pada commit H5).

## Compliance EA-002

- ✅ Mengurangi friksi adopsi (one-command bootstrap).
- ✅ Menjaga determinisme instalasi (6 fase berurutan, blocking stop).
- ✅ Mempertahankan backward compatibility (modul baru, tidak ada perubahan existing).
- ✅ Mempertahankan seluruh batas arsitektur (Developer Experience layer saja).
- ✅ SHALL NOT: tidak mengubah Foundation/Constitution/Governance/Runtime/ADR.

---

*— WP-E2.1 DONE. Lanjut ke WP-E2.2 (E2-G1 CLI Onboarding: sam init / doctor / version).* 
*Reporting per Engineering Rule: laporan hanya saat WP selesai / Stop Condition / Architecture Issue / Program selesai.*
