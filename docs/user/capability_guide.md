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

---

## Capability Bawaan Sistem (SAM 1.0, Program G-K)

Selain membuat capability plugin sendiri, SAM menyediakan **capability bawaan**
yang diaktifkan pada rilis SAM 1.0 (Program G-K). Semuanya berjalan melalui
jalur resmi `runtime_service.api` (tanpa bypass).

### Presentation Hosts (Program G-J)

Penyaji yang mengekspos capability sistem ke pengguna:

| Host | Program | Lokasi | Sifat |
|---|---|---|---|
| Conversation | G | `src/sam/presentation/conversation/` | Activity-host via runtime_service |
| Dashboard | H | `src/sam/presentation/dashboard/` | Activity-host via runtime_service |
| CLI | I | `src/sam/presentation/cli/` | Activity-host via runtime_service |
| REST API | J | `src/sam/api/presentation_rest/` | REST endpoint via runtime_service.api |

Semua host TIDAK mengandung business logic; hanya menghubungkan permintaan ke
jalur resmi RuntimeService.

### Capability REST (Program J)

Endpoint capability yang tersedia via REST (semua GET, preview-only):
`/workflow`, `/policy`, `/audit`, `/preview/{execution_id}`, `/knowledge`,
`/memory`, `/artifact`, `/approval/{execution_id}`, `/status`, plus `/health`,
`/runtime`, `/metrics`, `/events`.

Lihat panduan lengkap: `docs/user/rest_api_guide.md`.

### Capability LLM (Program K)

Jalur runtime LLM dengan tipe capability `connector.llm.chat`:

- Connector `llm_chat` terdaftar di ConnectorRegistry (`LLMConnectorLayer`).
- Provider dieksekusi oleh `ProviderExecutor` via HTTP (`httpx`).
- 5 provider LLM active (OpenAI, Anthropic, Gemini, DeepSeek, Ollama) melalui
  `LLMAdapter`; 5 non-LLM terdokumentasi (deferred).
- Aktivasi lewat wiring composition root `sam/api/llm_wiring.py`.

Provider akan aktif/available setelah lingkungan memiliki kredensial provider
(mis. env `OPENAI_API_KEY`) - lihat `docs/user/llm_integration_guide.md`.

### Jalur Resmi vs Bypass

Setiap host dan capability WAJIB memanggil `runtime_service.api`; tidak boleh
mengimpor Runtime/Registry/Provider/Connector/ExecutionRuntime secara langsung.
Pengecekan compliance memastikan **0 bypass** pada Program G-J dan K.
