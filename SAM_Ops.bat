@echo off
cd /d "D:\Project AI\SAM"
set PYTHONPATH=D:\Project AI\SAM\src
set PYTHONIOENCODING=utf-8
echo.
echo === SAM Operations CLI ===
echo Commands: task, history, settings, knowledge, explain
echo.
echo Examples:
echo   ops.py settings list
echo   ops.py task list
echo   ops.py history show
echo   ops.py knowledge show
echo   ops.py explain recent
echo.
cmd /k
