# Tutorial 3: Custom Plugin

> Plugin sederhana yang menambahkan capability baru.

## Tujuan

Buat plugin `log-utils` dengan dua capability: `log-read` dan `log-search`.

## Struktur

```
log-utils/
├── plugin.yaml
├── capabilities/
│   ├── __init__.py
│   └── log_ops.py
└── tests/
    └── test_log_ops.py
```

## 1. Plugin Manifest

```yaml
# log-utils/plugin.yaml
name: log-utils
version: "1.0.0"
author: "Anda"
description: "Utility untuk membaca dan mencari log"
entrypoint: "capabilities"
capabilities:
  - id: log-read
    description: "Membaca file log"
    inputs:
      path:
        type: string
        required: true
      lines:
        type: integer
        default: 100
        description: "Jumlah baris terakhir"

  - id: log-search
    description: "Mencari pattern di file log"
    inputs:
      path:
        type: string
        required: true
      pattern:
        type: string
        required: true
```

## 2. Capability

```python
# log-utils/capabilities/log_ops.py
import os
from sam.plugin.capability import BaseCapability

class LogReadCapability(BaseCapability):
    id = "log-read"
    
    async def execute(self, inputs: dict) -> dict:
        path = inputs["path"]
        lines = inputs.get("lines", 100)
        
        if not os.path.exists(path):
            return {"status": "error", "error": f"File not found: {path}"}
        
        try:
            with open(path, 'r') as f:
                all_lines = f.readlines()
            last_lines = all_lines[-lines:]
            return {
                "status": "success",
                "total_lines": len(all_lines),
                "returned_lines": len(last_lines),
                "lines": last_lines,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


class LogSearchCapability(BaseCapability):
    id = "log-search"
    
    async def execute(self, inputs: dict) -> dict:
        path = inputs["path"]
        pattern = inputs["pattern"]
        
        if not os.path.exists(path):
            return {"status": "error", "error": f"File not found: {path}"}
        
        try:
            matches = []
            with open(path, 'r') as f:
                for i, line in enumerate(f, 1):
                    if pattern in line:
                        matches.append({"line": i, "content": line.strip()})
            return {
                "status": "success",
                "pattern": pattern,
                "matches": len(matches),
                "results": matches[:100],  # Max 100 hasil
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
```

## 3. Instalasi

```bash
# Dari direktori log-utils
sam plugin install ./log-utils

# Cek
sam plugin list
# Output: log-utils v1.0.0

# Tes
sam run log-read --inputs '{"path": "/var/log/sam.log", "lines": 50}'
```

## 4. Test

```python
# log-utils/tests/test_log_ops.py
import pytest
import tempfile
import os

class TestLogReadCapability:
    @pytest.mark.asyncio
    async def test_read_lines(self):
        from log_utils.capabilities.log_ops import LogReadCapability
        cap = LogReadCapability()
        
        # Create test log
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            for i in range(200):
                f.write(f"Line {i}\n")
            fname = f.name
        
        try:
            result = await cap.execute({"path": fname, "lines": 10})
            assert result["status"] == "success"
            assert result["returned_lines"] == 10
        finally:
            os.unlink(fname)
```
