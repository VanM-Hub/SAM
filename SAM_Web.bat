@echo off
rem ============================================================
rem  SAM Web  ->  Web Dashboard UI (SAM Produk)
rem  Presentation layer (web_ui_server) + UI SAM Produk.
rem  Klik ganda -> server jalan + browser otomatis terbuka ke
rem  http://127.0.0.1:8080 (tanpa perlu ketik alamat).
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
echo  SAM Web Dashboard (SAM Produk)
echo  Server aktif, browser akan terbuka otomatis...
echo  (Ctrl+C untuk menghentikan)
echo.
rem Buka browser default setelah 4 detik (kasih waktu server start)
start "" /min cmd /c "timeout /t 4 /nobreak >nul & start "" http://127.0.0.1:8080"
".\.venv\Scripts\python.exe" -B -m uvicorn sam.operational_workspace.web_ui_server:app --host 127.0.0.1 --port 8080
pause
@endlocal
