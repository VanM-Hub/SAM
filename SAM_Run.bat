@echo off
rem ============================================================
rem  SAM Run  ->  Launcher mode: DIAGNOSTIC  (sam-diagnostic)
rem  Jalur resmi: sam.launcher.cli_entry:diagnostic_main
rem  Menjalankan diagnosa pipeline startup lalu keluar.
rem  Memakai python dalam .venv SAM (bukan python global).
rem
rem  PORTABLE (H1): path di-resolve dari lokasi script ini (%~dp0).
rem  Tidak ada path absolut hardcoded.
rem ============================================================
@setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "PYTHONIOENCODING=utf-8"
".\.venv\Scripts\python.exe" -B -c "import sys; sys.path.insert(0, r'%CD%\src'); from sam.launcher.cli_entry import diagnostic_main; diagnostic_main()"
echo.
echo  SAM Diagnostic selesai.
pause >nul
@endlocal
