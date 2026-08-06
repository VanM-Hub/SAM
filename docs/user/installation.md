# Panduan Instalasi SAM

> SAM Framework v30.0.0 (Capability Release - Program G-K)

## Prasyarat

- **Python:** 3.12+ (direkomendasikan) atau 3.8-3.11
- **Pip:** versi terbaru
- **Git:** untuk clone repository
- **OS:** Windows (10/11), Linux, macOS

## Instalasi Standar

```bash
# 1. Clone repository
git clone https://github.com/VanM-Hub/SAM.git
cd SAM

# 2. Buat virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# 3. Install SAM
pip install -e .

# 4. Install dengan extras (opsional)
pip install -e ".[console]"  # Dukungan CLI (typer, rich)
pip install -e ".[server]"   # Dukungan REST API (fastapi, uvicorn, httpx, jinja2)
pip install -e ".[desktop]"  # Dukungan GUI (PySide6)
pip install -e ".[all]"      # Semua extras
pip install -e ".[dev]"      # Pengembangan (pytest, ruff)
```

## Verifikasi Instalasi

Way 1 - launcher CLI (rekomendasi, tidak butuh ekstra tambahan):

```bash
# Cek versi launcher
python -m sam.launcher.cli_entry --version

# Cek health via launcher
python -m sam.launcher.cli_entry health
```

Output yang diharapkan (health):

```
SAM ready -- host: console   mode: NORMAL
```

Way 2 - CLI legacy (butuh extra `console`):

```bash
# Cek health via CLI klasik
sam health
```

> Catatan: perintah yang tersedia bergantung pada ekstra yang diinstal dan
> apakah `SAM_WORKSPACE` (folder dengan aset mission/database) tersedia.

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError: No module named 'typer'` | Install ekstra console: `pip install -e ".[console]"` |
| `ModuleNotFoundError: No module named 'fastapi'` | Install ekstra server: `pip install -e ".[server]"` |
| Database error | Hapus file database lalu jalankan ulang |
| `asyncio.to_thread` error | Upgrade ke Python 3.9+ |

## Jalur Runtime Aktif

Rilis v30.0.0 (Program G-K) mengaktifkan jalur runtime berikut:

- **Presentation Hosts** (Program G-J): Conversation, Dashboard, CLI, REST API
  - semuanya melalui `runtime_service.api` (tidak ada bypass).
- **Jalur LLM** (Program K): Connector -> Provider -> Agent.
  - Aktif dengan menyetel env kredensial provider (mis. `OPENAI_API_KEY`).

Lihat panduan terpisah:

- REST API: `docs/user/rest_api_guide.md`
- Integrasi LLM: `docs/user/llm_integration_guide.md`
