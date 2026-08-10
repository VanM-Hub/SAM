@echo off
rem ============================================================
rem  SAM Web  ->  SAM Mission Workspace (SAM Production API)
rem  Server: sam.api.server:app (REST API + UI di GET /ui)
rem  Klik ganda -> server jalan + browser otomatis terbuka ke
rem  http://127.0.0.1:8080/ui (Mission Workspace)
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
echo  SAM Mission Workspace (SAM Production API)
echo  Server aktif, browser akan terbuka otomatis...
echo  (Ctrl+C untuk menghentikan)
echo.
rem Buka browser default setelah 4 detik (kasih waktu server start)
start "" /min cmd /c "timeout /t 4 /nobreak >nul & start "" http://127.0.0.1:8080/ui"
".\.venv\Scripts\python.exe" -B -m uvicorn sam.api.server:app --host 127.0.0.1 --port 8080
pause
@endlocal
