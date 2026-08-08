# Journal — Perbaikan Launcher Desktop/CLI/Ops & Selarasan 5 Mode (.bat) (2026-08-07)

## Tujuan
Memperbaiki seluruh mode launcher yang "langsung selesai / tidak menampilkan tampilan" saat
dijalankan lewat 5 shortcut `.bat`, sehingga masing-masing mode berperilaku sesuai desainnya.

## Kerja
Ditemukan & diperbaiki beberapa akar masalah (struktur launcher memanggil API yang tidak lengkap,
exception ditelan pipeline, dependency hilang, versi ter-hardcode):

1. **Host selection mismatch** — `startup_pipeline.py` mencocokkan `selected_host`
   (display_name seperti "Desktop Host") ke kunci lowercase "desktop" → selalu fallback CONSOLE.
   Perbaikan: normalisasi case-insensitive (strip/lower/alias) di tempat konsumsi. `_select_host`
   tetap menyimpan display_name untuk metadata.
2. **`psutil` dependency inti hilang** — `SAM()` → `_get_runtime_provider()` → `import psutil`
   → `ModuleNotFoundError` ditelan pipeline → desktop keluar diam-diam. Install `psutil` ke `.venv`
   + daftarkan `"psutil>=5.9"` di `[project.dependencies]` `pyproject.toml`.
3. **Versi About Desktop ter-hardcode** — `src/sam/desktop/main.py` `VERSION="4.0.0"` → dinamis
   dari `sam.__version__` (sumber tunggal, pola sama dgn `cli/status.py`).
4. **Mode headless (`SAM_Ops.bat`) keluar langsung** — `_launch_headless` memanggil
   `telemetry.start()`/`telemetry.stop()` yang TIDAK ada di `TelemetryService` (API aslinya
   `close`/`emit`/`subscribe`, bukan start/stop) → `AttributeError` ditelan → proses selesai.
   Perbaikan: instansiasi telemetry + `HealthServer.mark_ready/start` + `Event().wait()` menahan
   proses; pembersihan pakai `telemetry.close()` + `server.stop()`.
5. **Mode console (`SAM_CLI.bat`) selesai langsung** — `_launch_console` hanya memanggil
   `console/app.py run()` yang merupakan lifecycle manager murni (state READY→RUNNING) tanpa event
   loop/REPL. Perbaikan: pakai `ConsoleSession` + loop input interaktif (prompt `sam> `, render
   dashboard, `exit`/Ctrl+C keluar); `ConsoleApp` tetap diinisialisasi lalu di-shutdown.
6. **5 file `.bat` diselaraskan** ke jalur resmi `sam.launcher.cli_entry` dan pakai
   `.\.venv\Scripts\python.exe` (python global 3.8 tanpa dependency SAM). ASCII bersih.

## Hasil (verifikasi run per mode)
- `SAM_Desktop.bat` → window Desktop Qt terbuka (proses hidup >12s saat uji).
- `SAM_CLI.bat` → terminal interaktif: prompt `sam> `; feed `help` render dashboard, `exit` keluar.
- `SAM_Ops.bat` → headless aktif terus (telemetry + health server; proses >12s saat uji).
- `SAM_Web.bat` → uvicorn `sam.web.server:app` berjalan, HTTP **200** di `127.0.0.1:8080`.
- `SAM_Run.bat` → diagnostic: 8 checks, 0 failed, exit 0 (desain: diagnosa lalu selesai).
- Test launcher+compliance+desktop: **136 passed**; validator docs: PASS.
- Ready pada setup: `pip` 25.0.1, PySide6 6.11.1, psutil 7.2.2 di `.venv` SAM.

## Commit terkait (riwayat lokal)
- `d4e615f` fix(launcher): selaraskan 5 shortcut .bat & perbaiki launcher console (tambah `run()`
  level modul di `console/app.py`).
- `bae2161` test(compliance/cli): perbaiki flaky test determinisme report (strip `duration`).
- `c6c530e` fix(desktop): perbaiki launcher desktop tidak muncul + daftarkan psutil
  (5 .bat + pyproject + startup_pipeline).
- `13898ef` fix(desktop): selaraskan versi About ke 1.0.0 via `sam.__version__`.
- `55d883d` fix(headless): perbaiki mode headless keluar langsung (`SAM_Ops.bat`).
- `08ce7ba` feat(console): mode SAM CLI jadi terminal interaktif (REPL).

## Catatan teknis
- `ConsoleSession`/`ConsoleIntegration`/`PromptRuntime` sudah tersedia sebagai infrastruktur sesi;
  `_launch_console` sebelumnya tidak menghubungkannya ke loop input (sebab mode selesai langsung).
- Mode console terhubung ke `ConsoleSession`; perintah inti (`help`, `exit`, navigasi 1-8,
  `refresh`, `back`) terverifikasi via dispatcher. Sebagian command (mis. `dashboard`, `missions`)
  belum terdaftar di dispatcher pustaka — di luar fokus perbaikan ini.

## Blocker
Tidak ada.

## Handoff
Sesi berikut:
- Jika Van ingin publish ke depan: buat repo GitHub baru + `git remote add origin <URL>` + push
  (remote `origin` sudah dihapus sebelumnya).
- Opsi tampilan CMD pada `SAM_Desktop.bat` (biarkan sebagai penampung vs sembunyikan via
  `pythonw.exe`+VBS) — menunggu keputusan Van.
- Keputusan Van untuk isi `docs/design/A0-001_Repository_Architecture_Integrity_Audit.md`
  (biarkan vs sesuaikan) dan placeholder Project Owner di `CHARTER.md` — masih menunggu.
