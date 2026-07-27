# Capability Guide

> Cara membuat capability baru di SAM.

## Apa Itu Capability?

Capability adalah unit fungsional terkecil di SAM — sebuah operasi spesifik yang bisa dijalankan secara mandiri. Contoh: `diagnose-runtime`, `repair-provider`, `deploy-workspace`.

## Capability Sederhana

```python
# capabilities/my_capability.py
from sam.plugin.capability import BaseCapability

class MyCapability(BaseCapability):
    id = "my-capability"
    description = "Capability contoh"
    
    async def execute(self, inputs: dict) -> dict:
        """Eksekusi utama capability."""
        name = inputs.get("name", "World")
        return {
            "message": f"Hello, {name}!",
            "status": "success",
        }
    
    async def validate_inputs(self, inputs: dict) -> list:
        """Validasi input sebelum eksekusi."""
        errors = []
        if "name" in inputs and not isinstance(inputs["name"], str):
            errors.append("'name' harus berupa string")
        return errors
```

## BaseCapability API

| Method | Wajib | Deskripsi |
|---|---|---|
| `execute(inputs)` | ✅ | Logika utama capability |
| `validate_inputs(inputs)` | ❌ | Validasi input (default: tidak ada validasi) |
| `on_start()` | ❌ | Hook sebelum eksekusi |
| `on_complete(result)` | ❌ | Hook setelah eksekusi sukses |
| `on_error(error)` | ❌ | Hook ketika terjadi error |

## Input/Output Convention

**Input:** Dictionary — key-value pairs.

```python
# Baik
{"target": "all", "timeout": 30}

# Hindari
inputs = "all"  # String tidak memiliki struktur
```

**Output:** Dictionary — minimal berisi `status`.

```python
# Sukses
{"status": "success", "message": "Done", "data": {...}}

# Error
{"status": "error", "error": "Detail pesan error"}
```

## Capability dengan Side Effects

```python
class DatabaseBackupCapability(BaseCapability):
    id = "db-backup"
    
    async def validate_inputs(self, inputs: dict) -> list:
        errors = []
        if "db_path" not in inputs:
            errors.append("'db_path' wajib diisi")
        return errors
    
    async def execute(self, inputs: dict) -> dict:
        import shutil
        import os
        from datetime import datetime
        
        db_path = inputs["db_path"]
        backup_dir = inputs.get("backup_dir", "./backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_name)
        
        try:
            shutil.copy2(db_path, backup_path)
            return {
                "status": "success",
                "backup_path": backup_path,
                "size_bytes": os.path.getsize(backup_path),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
```

## Mendaftarkan Capability

Capability didaftarkan melalui **plugin manifest**:

```yaml
# plugin.yaml
name: my-plugin
version: "1.0.0"
entrypoint: "capabilities"
capabilities:
  - id: my-capability
    description: "Capability contoh"
    inputs:
      name:
        type: string
        description: "Nama yang akan disapa"
```

## Testing Capability

```python
import pytest

class TestMyCapability:
    @pytest.mark.asyncio
    async def test_basic(self):
        from capabilities.my_capability import MyCapability
        cap = MyCapability()
        result = await cap.execute({"name": "SAM"})
        assert result["status"] == "success"
        assert "SAM" in result["message"]
    
    @pytest.mark.asyncio
    async def test_invalid_input(self):
        cap = MyCapability()
        errors = await cap.validate_inputs({"name": 123})
        assert len(errors) > 0
```
