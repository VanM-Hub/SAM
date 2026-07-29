# Contributing to SAM Framework

Terima kasih sudah berkontribusi ke SAM Framework! Berikut panduan untuk menjaga kualitas kode.

## Coding Standards

### Python
- Target: **Python 3.8+** (backward compatible)
- Ikuti PEP 8
- Gunakan `snake_case` untuk fungsi dan variabel
- Gunakan `PascalCase` untuk class
- Gunakan `UPPER_CASE` untuk constants

### Constraints (Python 3.8)
- Hindari `match-case` — tidak didukung
- Hindari backslash dalam f-string — assign ke variable dulu
- Gunakan `dict()` untuk serialisasi, bukan `.dict()` (dapat berubah di Pydantic v3)
- String concatenation dengan `+` untuk pesan dinamis di Python 3.8

### Logging
- Jangan gunakan `print()` di kode produksi
- Gunakan `structlog` untuk semua logging
- Setiap modul: `logger = structlog.get_logger()`

## Project Structure

```
src/sam/
  autonomous/     # Autonomous operations
  cli/            # Operations Console CLI (17 commands)
  contracts/      # Pydantic contracts
  dos/            # Desired Operational State
  guardian/       # Guardian Kernel (GDP)
  hosting/        # Hosting adapters
  intelligence/   # Incident detection, RCA, recommendations
  knowledge/      # Knowledge store
  launcher/       # Desktop launcher
  mission/        # Mission loader
  openclaw/       # OpenClaw integration
  runtime/        # Runtime Kernel (coordinator, bootstrap, session, recovery, shutdown)
  service/        # Windows Service, systemd, ServiceManager
  telemetry/      # Events, metrics, collector
  web/            # Web Dashboard (FastAPI + Jinja2 + HTMX)
```

## Making Changes

### Workflow
1. **Buat branch** dari `main`
2. **Implementasi** — ikuti Contract First (Pydantic model -> Protocol -> implementasi)
3. **Test** — tambahkan unit test di `tests/unit/`, integration test di `tests/integration/`
4. **Dokumentasi** — update docs jika API berubah
5. **PR** — buka pull request ke `main`

### Commit Messages
- `feat:` — fitur baru
- `fix:` — bug fix
- `refactor:` — refaktor tanpa perubahan fungsional
- `test:` — test baru atau update
- `docs:` — dokumentasi
- `chore:` — maintenance, tooling, config
- `perf:` — performance improvement

## Testing

### Running Tests
```powershell
$env:PYTHONPATH = ".\src"
$env:PYTHONIOENCODING = "utf-8"
python -m pytest tests/unit/ tests/integration/ -v --tb=short
```

> Jalankan perintah di atas dari root direktori SAM menggunakan PowerShell.

### Test Structure
- `tests/unit/` — unit tests (tanpa dependency eksternal)
- `tests/integration/` — integration tests (antar modul)
- `tests/legacy/` — test warisan v1.0 (tidak termasuk dalam suite utama)

### Test Naming
- Class: `Test<NamaModul>`
- Method: `test_<deskripsi>`
- Setiap test function harus independen

### Coverage Target
- Unit test: coverage >= 80% per modul
- Integration test: semua flow utama

## Documentation

- Arsitektur: `docs/architecture/`
- ADR: `docs/adr/ADR-NNN-NNN.md`
- Design: `docs/design/`
- Performance: `docs/performance/`

Setiap perubahan pada API publik harus disertai update dokumentasi.

## PR Process

1. Branch dari `main`
2. Implementasi + test + docs
3. Commit dengan pesan jelas
4. PR ke `main`
5. Review oleh setidaknya 1 kontributor
6. Merge setelah semua test lulus

## License

Apache-2.0 — dengan kontribusi, Anda setuju bahwa kontribusi Anda dilisensikan di bawah lisensi yang sama.

Lihat file LICENSE untuk detail lengkap.
