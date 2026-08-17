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
rem
rem  PORT GUARD: jika port 8080 sudah aktif (server SAM jalan),
rem  langsung buka browser ke UI yang aktif, jangan start ulang
rem  (hindari error 10048).
rem ============================================================
@setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "PYTHONIOENCODING=utf-8"
rem --- AUTH (login nyata operator) aktif. ---
rem Hanya SAM_ENABLE_AUTH=1 (tanpa SAM_ENV=production) agar cookie tidak
rem secure (server jalan di http 127.0.0.1, bukan HTTPS). SAM_ENV=production
rem dipakai bila di belakang Caddy/HTTPS (cookie secure + auth mandatory).
set "SAM_ENABLE_AUTH=1"

rem --- POSTGRES PERSISTENT (Ward tahan restart). ---
rem Aktifkan store Postgres bila SAM_PG_PASSWORD tersedia (di env User Windows,
rem di-reset via docker exec pada 2026-08-17). SAM_ENV=production tetap TIDAK
rem dipakai (cookie non-secure di 127.0.0.1). SAM_PG_DSN/ENABLE ini membuat
rem WardStore memilih PostgresWardStore (bukan InMemory) -> Ward tahan restart.
if defined SAM_PG_PASSWORD set "SAM_ENABLE_PG=1"

rem --- Cek port 8080 (apakah SAM sudah jalan) ---
netstat -ano | findstr "8080" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 goto :start_server
echo  SAM sudah berjalan (port 8080 aktif).
echo  Buka browser ke UI yang sudah aktif...
start "" http://127.0.0.1:8080/ui
exit /b 0

:start_server
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
