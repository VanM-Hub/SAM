@echo off
rem ============================================================
rem  SAM Desktop  ->  Launcher mode: DESKTOP  (sam-desktop)
rem  Jalur resmi: sam.launcher.cli_entry:desktop_main
rem  Menampilkan jendela Desktop Qt (PySide6).
rem  Memakai python dalam .venv SAM (bukan python global).
rem
rem  PORTABLE (H1): path di-resolve dari lokasi script ini (%~dp0).
rem  Tidak ada path absolut hardcoded.
rem ============================================================
@setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "PYTHONIOENCODING=utf-8"
".\.venv\Scripts\python.exe" -B -c "import sys; sys.path.insert(0, r'%CD%\src'); from sam.launcher.cli_entry import desktop_main; desktop_main()"
echo.
echo  SAM Desktop ditutup.
pause >nul
@endlocal
