# WP-D2.1 — H1 Portable Deployment — Engineering Evidence

**Program:** D (MISSION-2D — Production Readiness)
**Phase:** EA-002 — Production Readiness Implementation
**Priority:** P1 · **Gap:** H1 Portable Deployment
**Type:** Working Report (evidence) → `reports/`
**Date:** 2026-08-08
**Status:** ✅ COMPLETE (menunggu Verdict Lead Engineer)

---

## Objective (ruang lingkup implementasi)

1. Menghilangkan ketergantungan deployment terhadap path non-portabel.
2. Membuat deployment single-node deterministik.
3. Menyiapkan bootstrap yang dapat direproduksi.
4. Mempertahankan kompatibilitas dengan baseline runtime yang ada.
5. Tidak mengubah perilaku runtime maupun governance.

---

## Gap yang Diperbaiki (H1)

Sebelumnya, kelima launcher `.bat` di root repo memakai **absolute path hardcoded** `D:\Project AI\SAM`:

```bat
cd /d "D:\Project AI\SAM"
set PYTHONPATH=D:\Project AI\SAM\src
... sys.path.insert(0, r'D:\Project AI\SAM\src') ...
```

**Dampak:** deployment tidak portable — `.bat` hanya berjalan di mesin dengan path persis itu; relokasi/copy ke environment lain memerlukan edit manual.

---

## Implementasi

Kelima launcher `.bat` di-refactor menjadi **portable** — path di-resolve dari lokasi script (`%~dp0`), bukan hardcoded:

| File | Perubahan |
|---|---|
| `SAM_CLI.bat` | `cd /d "D:\Project AI\SAM"` → `cd /d "%~dp0"`; `PYTHONPATH=%CD%\src`; `sys.path.insert(0, %CD%\src)` |
| `SAM_Desktop.bat` | sama (desktop_main) |
| `SAM_Ops.bat` | sama (headless_main) |
| `SAM_Run.bat` | sama (diagnostic_main) |
| `SAM_Web.bat` | sama (uvicorn sam.web.server) |

Pattern portable (`%~dp0` = direktori tempat script berada, `%CD%` = working directory setelah cd):

```bat
@setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "PYTHONIOENCODING=utf-8"
".\.venv\Scripts\python.exe" -B -c "import sys; sys.path.insert(0, r'%CD%\src'); from sam.launcher.cli_entry import sam_main; sam_main(argv=['--host','console'])"
@endlocal
```

Semantik & nama entry point **tidak berubah** — hanya mekanisme resolusi path yang dibuat portable.

---

## Evidence Suite (otomatis, bagian CI integration)

**`tests/integration/test_launcher_portable.py`** — 8 test, memverifikasi portabilitas:

| # | Test | Assert |
|---|---|---|
| 1 | `test_all_launcher_bats_exist` | 5 `.bat` ada |
| 2 | `test_no_absolute_drive_path_in_bat` | tidak ada `C:`/`D:` drive path di baris perintah |
| 3 | `test_no_hardcoded_project_src_path` | tidak ada `<drive>\\...\\src` hardcoded |
| 4 | `test_uses_relative_script_dir` | memakai `%~dp0` |
| 5 | `test_uses_cd_to_relative_dir` | `cd /d "%~dp0"` |
| 6 | `test_uses_relative_pythonpath` | `PYTHONPATH=%CD%` |
| 7 | `test_python_entry_point_intact` | entry point `sam.launcher.cli_entry` (kecuali Web: `sam.web.server`) |
| 8 | `test_python_executable_resolution` | python `.venv` relatif |

Test ini masuk **CI integration job** (`python -m pytest tests/integration/`) — jadi otomatis ter-verifikasi di baseline CI.

---

## Bukti Verifikasi Nyata

Jalankan launcher portable di repo (tanpa path absolut):

| Uji | Hasil |
|---|---|
| `SAM_Run.bat` (diagnostic) | ✅ "SAM Diagnostics - 8 checks, Passed: 8, Failed: 0" |
| `SAM_CLI.bat` (console) | ✅ mencapai prompt `sam>` (pipeline startup 8-stage sukses) |

## Regression Check

| Suite | Hasil |
|---|---|
| `tests/integration/test_service_deployment.py` + `test_launcher_portable.py` | ✅ 21 passed |
| Baseline CI scope (unit + runtimes + observation) | ✅ 4290 passed, 1 skipped, 2 xfailed |

**Tidak ada regression.** Perilaku runtime, startup pipeline, dan entry point tidak berubah — hanya resolusi path launcher yang dibuat portable.

---

## Compliance

- Foundation: tidak diubah ✅
- Constitution: tidak diubah ✅
- Governance: tidak diubah ✅
- Accepted ADR: tetap berlaku ✅
- Runtime konstitusional baru: tidak ditambah ✅
- Responsibility runtime: tidak diubah ✅

---

## Status

H1 **Portable Deployment** terimplementasi, ter-verifikasi, ter-test. Seluruh ruang lingkup P1 terpenuhi.

*— Engineering evidence WP-D2.1 (H1). Meneruskan ke Verdict Lead Engineer.*
