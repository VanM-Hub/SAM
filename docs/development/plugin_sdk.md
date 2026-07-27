# Plugin SDK

> Panduan membuat plugin untuk SAM.

## Daftar Isi

1. [Apa Itu Plugin?](#apa-itu-plugin)
2. [Struktur Plugin](#struktur-plugin)
3. [Plugin Manifest](#plugin-manifest)
4. [Membuat Plugin](#membuat-plugin)
5. [Testing Plugin](#testing-plugin)
6. [Distribusi Plugin](#distribusi-plugin)

## Apa Itu Plugin?

Plugin adalah paket yang berisi satu atau lebih **capability** yang bisa diinstal ke SAM. Plugin memungkinkan ekstensi fungsionalitas tanpa mengubah kode inti.

## Struktur Plugin

```
my-plugin/
├── plugin.yaml              # Manifest (wajib)
├── capabilities/
│   ├── __init__.py
│   ├── cap_one.py
│   └── cap_two.py
├── tests/
│   └── test_my_plugin.py
├── requirements.txt          # Dependencies (opsional)
└── README.md                 # Dokumentasi plugin
```

## Plugin Manifest

```yaml
# plugin.yaml — format lengkap
name: my-plugin
version: "1.0.0"
author: "Nama Anda"
description: "Plugin untuk melakukan X dan Y"
entrypoint: "capabilities"    # Subdirektori yang berisi capability

capabilities:
  - id: cap-one
    description: "Capability pertama"
    inputs:
      param1:
        type: string
        description: "Parameter pertama"
        required: true
      param2:
        type: integer
        description: "Parameter kedua"
        default: 42

  - id: cap-two
    description: "Capability kedua"
    inputs:
      target:
        type: string
        required: true

dependencies:
  - requests>=2.0
  - pyyaml
```

## Membuat Plugin

### Langkah 1: Buat struktur

```bash
mkdir -p my-plugin/capabilities my-plugin/tests
```

### Langkah 2: Buat manifest

```yaml
# my-plugin/plugin.yaml
name: file-utils
version: "1.0.0"
author: "Anda"
description: "Utility untuk operasi file"
entrypoint: "capabilities"
capabilities:
  - id: file-read
    description: "Membaca isi file"
    inputs:
      path:
        type: string
        required: true
  - id: file-write
    description: "Menulis ke file"
    inputs:
      path:
        type: string
        required: true
      content:
        type: string
        required: true
```

### Langkah 3: Buat capability

```python
# my-plugin/capabilities/file_ops.py
from sam.plugin.capability import BaseCapability

class FileReadCapability(BaseCapability):
    id = "file-read"
    
    async def execute(self, inputs: dict) -> dict:
        path = inputs["path"]
        try:
            with open(path, 'r') as f:
                content = f.read()
            return {"status": "success", "content": content, "size": len(content)}
        except FileNotFoundError:
            return {"status": "error", "error": f"File not found: {path}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

class FileWriteCapability(BaseCapability):
    id = "file-write"
    
    async def execute(self, inputs: dict) -> dict:
        path = inputs["path"]
        content = inputs["content"]
        try:
            with open(path, 'w') as f:
                f.write(content)
            return {"status": "success", "path": path, "bytes_written": len(content)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
```

### Langkah 4: Buat `__init__.py`

```python
# my-plugin/capabilities/__init__.py
from .file_ops import FileReadCapability, FileWriteCapability

__all__ = ["FileReadCapability", "FileWriteCapability"]
```

## Testing Plugin

```python
# my-plugin/tests/test_file_ops.py
import pytest
import tempfile
import os

class TestFileReadCapability:
    @pytest.mark.asyncio
    async def test_read_existing_file(self):
        from my_plugin.capabilities.file_ops import FileReadCapability
        cap = FileReadCapability()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            fname = f.name
        
        try:
            result = await cap.execute({"path": fname})
            assert result["status"] == "success"
            assert result["content"] == "test content"
        finally:
            os.unlink(fname)
```

## Distribusi Plugin

Plugin bisa didistribusikan sebagai direktori atau arsip ZIP:

```bash
# Instal dari direktori
sam plugin install ./my-plugin

# Buat arsip
cd my-plugin && zip -r ../my-plugin.zip .

# Instal dari ZIP
sam plugin install ./my-plugin.zip
```
