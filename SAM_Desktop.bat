@echo off
rem ============================================================
rem  SAM Desktop  ->  Launcher mode: DESKTOP  (sam-desktop)
rem  Jalur resmi: sam.launcher.cli_entry:desktop_main
rem  Menampilkan jendela Desktop Qt (PySide6).
rem  Memakai python dalam .venv SAM (bukan python global).
rem ============================================================
cd /d "D:\Project AI\SAM"
set PYTHONPATH=D:\Project AI\SAM\src
set PYTHONIOENCODING=utf-8
".\.venv\Scripts\python.exe" -B -c "import sys; sys.path.insert(0, r'D:\Project AI\SAM\src'); from sam.launcher.cli_entry import desktop_main; desktop_main()"
echo.
echo  SAM Desktop ditutup.
pause >nul
