@echo off
rem ============================================================
rem  SAM Web  ->  Web Dashboard (jalur web resmi, bukan launcher)
rem  WebRuntimeService + Presentation + 6 capability.
rem  Buka di browser: http://127.0.0.1:8080
rem  (Ctrl+C untuk menghentikan)
rem  Memakai python dalam .venv SAM (bukan python global).
rem
rem  PORTABLE (H1): path di-resolve dari lokasi script ini (%~dp0).
rem  Tidak ada path absolut hardcoded.
rem ============================================================
@setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "PYTHONIOENCODING=utf-8"
echo.
echo  SAM Web Dashboard
echo  Jalur resmi: sam.web.server
echo  Buka: http://127.0.0.1:8080
echo  (Ctrl+C untuk menghentikan)
echo.
".\.venv\Scripts\python.exe" -B -m uvicorn sam.web.server:app --host 127.0.0.1 --port 8080
pause
@endlocal
