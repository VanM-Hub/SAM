# Plugin Guide

> Cara menginstal dan mengelola plugin di SAM.

## Apa Itu Plugin?

Plugin adalah paket yang menambahkan **capability** baru ke SAM. Plugin bisa berisi:

- Satu atau lebih capability
- Konfigurasi default
- Dependencies eksternal

## Struktur Plugin

```
my-plugin/
├── plugin.yaml           # Manifest plugin (wajib)
├── capabilities/
│   ├── __init__.py
│   └── my_capability.py  # Implementasi capability
└── requirements.txt      # Dependencies (opsional)
```

## Plugin Manifest (plugin.yaml)

```yaml
name: my-plugin
version: "1.0.0"
author: "Nama Author"
description: "Plugin contoh"
entrypoint: "capabilities"
capabilities:
  - id: my-capability
    description: "Capability contoh"
    inputs:
      message:
        type: string
        description: "Pesan yang akan ditampilkan"
```

## Instalasi Plugin

```bash
# Dari direktori lokal
sam plugin install ./my-plugin

# Dari path absolut
sam plugin install /path/to/my-plugin
```

## Manajemen Plugin

```bash
# Daftar plugin terinstal
sam plugin list

# Lihat detail plugin
sam plugin show my-plugin

# Aktifkan plugin
sam plugin enable my-plugin

# Nonaktifkan plugin
sam plugin disable my-plugin

# Hapus plugin
sam plugin remove my-plugin
```

## Membuat Plugin Sederhana

1. Buat struktur direktori:
```bash
mkdir my-plugin/capabilities -p
```

2. Buat `plugin.yaml`:
```yaml
name: hello-world
version: "1.0.0"
author: "Anda"
entrypoint: "capabilities"
capabilities:
  - id: hello-world
    description: "Mengucapkan hello world"
```

3. Buat `capabilities/hello_world.py`:
```python
from sam.plugin.capability import BaseCapability

class HelloWorldCapability(BaseCapability):
    id = "hello-world"
    
    async def execute(self, inputs: dict) -> dict:
        name = inputs.get("name", "World")
        return {"message": f"Hello, {name}!"}
```

4. Instal:
```bash
sam plugin install ./hello-world
sam plugin enable hello-world
sam run hello-world --inputs '{"name": "SAM"}'
# Output: {"message": "Hello, SAM!"}
```
