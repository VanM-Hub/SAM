@echo off
rem ============================================================
rem  SAM CLI  ->  Launcher mode: CONSOLE  (sam-console)
rem  Jalur resmi: sam.launcher.cli_entry:sam_main
rem  Menjalankan SAM lewat satu-satunya pipeline startup terpadu
rem ============================================================
cd /d "D:\Project AI\SAM"
set PYTHONPATH=D:\Project AI\SAM\src
set PYTHONIOENCODING=utf-8
python -B -c "import sys; sys.path.insert(0, r'D:\Project AI\SAM\src'); from sam.launcher.cli_entry import sam_main; sam_main(argv=['--host','console'])"
echo.
echo  SAM CLI selesai. (Tekan tombol untuk menutup.)
pause >nul
