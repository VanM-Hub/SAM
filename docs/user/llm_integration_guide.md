# LLM Integration Guide

> Panduan integrasi jalur runtime LLM SAM (Program K, SAM 1.0 Foundation).
> Release).

Program K mengaktifkan jalur runtime LLM:
`Connector -> Provider -> Agent`. Jalur ini dioperasionalkan tanpa menambah
Runtime baru dan tanpa mengubah RuntimeService.

## Konsep Jalur

```
Presentation Host
    -> runtime_service.api
        -> Connector  (LLMConnectorLayer, contract connector.llm.chat)
        -> Provider   (ProviderExecutor via httpx -> LLMAdapter)
        -> Agent      (LLMAgentLayer + baseline mission_agent)
```

Seluruh aktivasi dilakukan di **composition root** `sam/api/llm_wiring.py`.
Endpoint handler & presentation host TIDAK mengimpor Runtime/Registry/Provider/
Connector/ExecutionRuntime secara langsung (0 bypass).

## Provider yang Didukung

| Provider | Env kredensial | Base URL (default) |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `https://api.openai.com/v1` |
| Anthropic | `ANTHROPIC_API_KEY` | `https://api.anthropic.com` |
| Gemini | `GEMINI_API_KEY` | `https://generativelanguage.googleapis.com` |
| DeepSeek | `DEEPSEEK_API_KEY` | `https://api.deepseek.com` |
| Ollama | `OLLAMA_HOST` | `http://localhost:11434` |

> API key dibaca dari environment/config dan TIDAK di-hardcode. Setiap provider
> menerapkan interface `LLMAdapter` yang sama (`src/sam/providers/llm/`).

## Kredensial

Provider hanya **available** ketika environment memiliki kredensial. Setel
sebelum menjalankan SAM, misalnya:

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."

# Linux/macOS
export OPENAI_API_KEY="sk-..."
```

Tanpa kredensial, provider tetap terdaftar (status `active`) tetapi
`available: false` - jalur siap, eksekusi nyata menunggu env.

## Memeriksa Readiness (Python)

Dari environment Python yang telah menginstal SAM:

```python
from sam.api import llm_wiring as w

# Status connector manager
print(w.connector_readiness())
# {'ready': True, 'checks': [ {'stage': 'registry', 'ok': True, ...}, ... ]}

# Status per provider
print(w.provider_readiness())
# {'contract': 'connector.llm.chat', 'total': 10, 'active': 5, ...}
```

`provider_readiness()` menampilkan matriks: total provider, berapa yang aktif,
dan detail per provider (adapter ada/tidak, status, available).

## Lapisan Aktivasi

| Lapisan | Kelas / komponen | Peran |
|---|---|---|
| Connector | `LLMConnectorLayer` (contract `connector.llm.chat`) | Mendaftarkan connector `llm_chat` ke ConnectorRegistry |
| Provider | `LLMProviderLayer`, `ProviderExecutor`, 5 `LLMAdapter` | Eksekusi via HTTP (`httpx`), peta adapters via DI |
| Agent | `LLMAgentLayer`, `AgentBridge`, baseline `mission_agent` | Menerapkan contract connector, menghubungkan jalur |

## Keamanan & Batasan

- **TIDAK ada eksekusi eksternal** pada jalur preview: `ProviderActivationExecutor`
  mode preview (ADR-024) - external_calls=0.
- Provider nyata dieksekusi hanya saat `ProviderExecutor.execute(...)` dipanggil
  dengan env kredensial lengkap.
- Semua host & handler wajib lewat `runtime_service.api`; compliance memastikan
  **0 bypass**.

## Error Handling

Jika provider tidak tersedia:

- `ProviderUnavailableError` (dari `provider_executor.py`) - provider tidak
  terdaftar / tanpa base_url / tanpa kredensial.
- Cek env var provider sudah teriset sebelum memanggil eksekusi nyata.
