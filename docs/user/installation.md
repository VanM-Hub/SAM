# Panduan Instalasi SAM

> SAM Framework v1.0.0

## Prasyarat

- **Python:** 3.12+ (direkomendasikan) atau 3.8–3.11
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
pip install -e ".[metrics]"   # Dukungan metrik sistem (psutil)
pip install -e ".[knowledge]" # Dukungan knowledge graph (pyyaml)
pip install -e ".[dev]"       # Pengembangan (pytest)
```

## Verifikasi Instalasi

```bash
# Cek versi Python
python --version

# Cek SAM health
python -m sam.cli.main health

# Cek CLI
python -m sam.cli.main --help
```

Output yang diharapkan:

```
=== SAM Health ===
  Python      : 3.12.x
  Database    : OK
  cognition   : OK
  healing     : OK
  autonomy    : OK
System status: HEALTHY
```

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError` | Pastikan `pip install -e .` sudah jalan |
| Database error | Hapus `sam.db` lalu jalankan ulang |
| `asyncio.to_thread` error | Upgrade ke Python 3.9+ |
