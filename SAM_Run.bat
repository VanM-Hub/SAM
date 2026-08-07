@echo off
rem ============================================================
rem  SAM Run  ->  Launcher mode: DIAGNOSTIC  (sam-diagnostic)
rem  Jalur resmi: sam.launcher.cli_entry:diagnostic_main
rem  Menjalankan diagnosa pipeline startup lalu keluar
rem ============================================================
cd /d "D:\Project AI\SAM"
set PYTHONPATH=D:\Project AI\SAM\src
set PYTHONIOENCODING=utf-8
python -B -c "import sys; sys.path.insert(0, r'D:\Project AI\SAM\src'); from sam.launcher.cli_entry import diagnostic_main; diagnostic_main()"
echo.
echo  SAM Diagnostic selesai.
pause >nul
