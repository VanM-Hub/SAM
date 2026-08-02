# Capability SDK

> **Document Type: Developer Documentation** (Implementation Guide).
> This document is NOT a Domain Specification. The Capability domain is specified in `docs/specifications/CAPABILITY_SPECIFICATION.md`. This guide explains SDK usage only.

> Panduan lengkap membuat capability baru untuk SAM.

## Daftar Isi

1. [Pengertian](#pengertian)
2. [BaseCapability API](#basecapability-api)
3. [Membuat Capability Pertama](#membuat-capability-pertama)
4. [Input & Output](#input--output)
5. [Error Handling](#error-handling)
6. [Testing](#testing)
7. [Best Practices](#best-practices)

## Pengertian

**Capability** adalah unit fungsional terkecil di SAM. Setiap capability adalah operasi spesifik yang:

- Menerima input (dict)
- Memproses secara synchronous atau asynchronous
- Mengembalikan output (dict)
- Dapat divalidasi sebelum eksekusi

## BaseCapability API

```python
from sam.plugin.capability import BaseCapability

class MyCapability(BaseCapability):
    # Metadata (wajib)
    id = "my-capability"
    description = "Deskripsi capability"
    
    # Methods
    async def validate_inputs(self, inputs: dict) -> list:
        """Validasi input. Kembalikan list error (kosong = valid)."""
        return []
    
    async def execute(self, inputs: dict) -> dict:
        """Eksekusi utama. Wajib diimplementasi."""
        raise NotImplementedError
    
    async def on_start(self) -> None:
        """Hook sebelum execute (opsional)."""
        pass
    
    async def on_complete(self, result: dict) -> None:
        """Hook setelah execute sukses (opsional)."""
        pass
    
    async def on_error(self, error: Exception) -> None:
        """Hook ketika execute error (opsional)."""
        pass
```

## Membuat Capability Pertama

```python
# my_capability.py
from sam.plugin.capability import BaseCapability

class GreeterCapability(BaseCapability):
    id = "greeter"
    description = "Menyapa pengguna"
    
    async def execute(self, inputs: dict) -> dict:
        name = inputs.get("name", "World")
        return {
            "status": "success",
            "message": f"Hello, {name}!",
        }
```

## Input & Output

### Format Input

```python
# Input selalu dictionary
{
    "param1": "value1",
    "param2": 42,
    "param3": ["a", "b", "c"],
}
```

### Format Output

```python
# Sukses
{
    "status": "success",
    "message": "Optional message",
    "data": {...},  # Data tambahan (opsional)
}

# Error
{
    "status": "error",
    "error": "Deskripsi error",
    "code": "ERR_001",  # Kode error (opsional)
}
```

## Error Handling

```python
class SafeCapability(BaseCapability):
    id = "safe-op"
    
    async def execute(self, inputs: dict) -> dict:
        try:
            result = await self._risky_operation(inputs)
            return {"status": "success", "data": result}
        except ValueError as e:
            return {"status": "error", "error": str(e), "code": "INVALID_INPUT"}
        except TimeoutError as e:
            return {"status": "error", "error": "Operation timed out", "code": "TIMEOUT"}
        except Exception as e:
            return {"status": "error", "error": f"Unexpected: {e}", "code": "UNKNOWN"}
```

## Testing

```python
import pytest

class TestGreeterCapability:
    @pytest.mark.asyncio
    async def test_greet_default(self):
        cap = GreeterCapability()
        result = await cap.execute({})
        assert result["status"] == "success"
        assert "World" in result["message"]
    
    @pytest.mark.asyncio
    async def test_greet_with_name(self):
        cap = GreeterCapability()
        result = await cap.execute({"name": "SAM"})
        assert "SAM" in result["message"]
```

## Best Practices

1. **Validasi input** — selalu validasi sebelum eksekusi
2. **Gunakan tipe yang jelas** — string, int, list — bukan dict tanpa skema
3. **Handle error** — jangan biarkan exception tidak tertangani
4. **Test semua path** — sukses, error, timeout, edge case
5. **Dokumentasi input/output** — minimal docstring
