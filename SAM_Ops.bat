@echo off
rem ============================================================
rem  SAM Ops  ->  Launcher mode: HEADLESS  (sam-headless)
rem  Jalur resmi: sam.launcher.cli_entry:headless_main
rem  Headless = tanpa GUI; telemetry + health server via asyncio.
rem  Memakai python dalam .venv SAM (bukan python global).
rem ============================================================
cd /d "D:\Project AI\SAM"
set PYTHONPATH=D:\Project AI\SAM\src
set PYTHONIOENCODING=utf-8
".\.venv\Scripts\python.exe" -B -c "import sys; sys.path.insert(0, r'D:\Project AI\SAM\src'); from sam.launcher.cli_entry import headless_main; headless_main()"
echo.
echo  SAM Headless (Ops) ditutup.
pause >nul
