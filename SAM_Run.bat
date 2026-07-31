@echo off
cd /d "D:\Project AI\SAM"
set PYTHONPATH=D:\Project AI\SAM\src
set PYTHONIOENCODING=utf-8
python -B -m sam.cli.main %*
pause
