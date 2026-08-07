@echo off
rem ============================================================
rem  SAM CLI  ->  Launcher mode: CONSOLE  (sam-console)
rem  Jalur resmi: sam.launcher.cli_entry:sam_main
rem  Menjalankan SAM via pipeline startup terpadu.
rem  Memakai python dalam .venv SAM (bukan python global).
rem ============================================================
cd /d "D:\Project AI\SAM"
set PYTHONPATH=D:\Project AI\SAM\src
set PYTHONIOENCODING=utf-8
".\.venv\Scripts\python.exe" -B -c "import sys; sys.path.insert(0, r'D:\Project AI\SAM\src'); from sam.launcher.cli_entry import sam_main; sam_main(argv=['--host','console'])"
echo.
echo  SAM CLI selesai.
pause >nul
