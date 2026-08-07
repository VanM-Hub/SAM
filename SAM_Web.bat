@echo off
rem ============================================================
rem  SAM Web  ->  Web Dashboard (jalur web resmi, bukan launcher)
rem  WebRuntimeService + Presentation + 6 capability
rem  Buka di browser: http://127.0.0.1:8080
rem  (Ctrl+C untuk menghentikan)
rem ============================================================
cd /d "D:\Project AI\SAM"
set PYTHONPATH=D:\Project AI\SAM\src
set PYTHONIOENCODING=utf-8
echo.
echo  SAM Web Dashboard
echo  Jalur resmi: sam.web.server
echo  Buka: http://127.0.0.1:8080
echo  (Ctrl+C untuk menghentikan)
echo.
python -B -m uvicorn sam.web.server:app --host 127.0.0.1 --port 8080
pause
