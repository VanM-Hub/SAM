@echo off
cd /d "D:\Project AI\SAM"
set PYTHONPATH=D:\Project AI\SAM\src
set PYTHONIOENCODING=utf-8
python -B -c "import sys; sys.path.insert(0, 'D:/Project AI/SAM/src'); from sam.desktop.main import run; run()"
pause
