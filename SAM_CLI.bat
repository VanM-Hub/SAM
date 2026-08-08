@echo off
rem ============================================================
rem  SAM CLI  ->  Launcher mode: CONSOLE  (sam-console)
rem  Jalur resmi: sam.launcher.cli_entry:sam_main
rem  Menjalankan SAM via pipeline startup terpadu.
rem  Memakai python dalam .venv SAM (bukan python global).
rem
rem  PORTABLE (H1): path di-resolve dari lokasi script ini (%~dp0),
rem  sehingga .bat dapat dipindah/copy ke environment lain
rem  tanpa edit manual. Tidak ada path absolut hardcoded.
rem ============================================================
@setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "PYTHONIOENCODING=utf-8"
".\.venv\Scripts\python.exe" -B -c "import sys; sys.path.insert(0, r'%CD%\src'); from sam.launcher.cli_entry import sam_main; sam_main(argv=['--host','console'])"
echo.
echo  SAM CLI selesai.
pause >nul
@endlocal
