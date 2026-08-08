@echo off
rem ============================================================
rem  SAM Ops  ->  Launcher mode: HEADLESS  (sam-headless)
rem  Jalur resmi: sam.launcher.cli_entry:headless_main
rem  Headless = tanpa GUI; telemetry + health server via asyncio.
rem  Memakai python dalam .venv SAM (bukan python global).
rem
rem  PORTABLE (H1): path di-resolve dari lokasi script ini (%~dp0).
rem  Tidak ada path absolut hardcoded.
rem ============================================================
@setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "PYTHONIOENCODING=utf-8"
".\.venv\Scripts\python.exe" -B -c "import sys; sys.path.insert(0, r'%CD%\src'); from sam.launcher.cli_entry import headless_main; headless_main()"
echo.
echo  SAM Headless (Ops) ditutup.
pause >nul
@endlocal
