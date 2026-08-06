# REST API Guide

> Panduan penggunaan REST API SAM (Program J, v30.0.0 - Capability Release).

REST API SAM adalah **presentation host** yang mengekspos capability sistem
melalui HTTP/JSON. Seluruh endpoint berjalan melalui jalur resmi
`runtime_service.api` (tanpa bypass). REST API TIDAK mengeksekusi provider
secara nyata - semua capability dijalankan dalam **mode preview** (tidak ada
efek samping eksternal).

## Prasyarat

- Install SAM dengan ekstra server: `pip install -e ".[server]"`
  (fastapi, uvicorn, httpx, jinja2).

## Menjalankan Server

```bash
uvicorn sam.api.server:app --host 0.0.0.0 --port 8080
```

Setelah berjalan, dokumentasi interaktif (Swagger) tersedia di:

- `http://localhost:8080/docs`
- `http://localhost:8080/redoc`

## Daftar Endpoint

| Endpoint | Method | Deskripsi |
|---|---|---|
| `/` | GET | Metadata API |
| `/health` | GET | Pemeriksaan kesehatan (jalur resmi) |
| `/health/ready` | GET | Readiness probe |
| `/runtime` | GET | Status runtime (jalur resmi) |
| `/metrics` | GET | Metrics terkini |
| `/events` | GET | Event telemetry |
| `/workflow/` | GET | Daftar id workflow |
| `/workflow/{id}` | GET | Detail workflow |
| `/policy/` | GET | Daftar id policy |
| `/policy/{id}` | GET | Detail policy |
| `/audit/` | GET | Daftar id audit |
| `/audit/{id}` | GET | Detail audit |
| `/preview/{execution_id}` | GET | Preview eksekusi (preview-only) |
| `/knowledge/` | GET | Daftar id knowledge |
| `/knowledge/{id}` | GET | Detail knowledge |
| `/memory/` | GET | Daftar id memory |
| `/memory/{id}` | GET | Detail memory |
| `/artifact/` | GET | Daftar nama artifact |
| `/artifact/{name}` | GET | Detail artifact |
| `/approval/{execution_id}` | GET | Status approval (pass-through) |
| `/status/` | GET | Status runtime |

> Endpoint capability (`/workflow`, `/policy`, `/knowledge`, dst.) hanya
> membaca (READ-ONLY, preview). Endpoint `/preview` dan `/approval` memakai
> `ConversationPreviewGateway` dan TIDAK mengeksekusi provider sungguhan
> (ADR-024).

## Contoh Penggunaan

```bash
# Health
curl http://localhost:8080/health

# Status runtime
curl http://localhost:8080/status/

# Daftar workflow
curl http://localhost:8080/workflow/

# Detail audit
curl http://localhost:8080/audit/{id}

# Preview eksekusi (tidak menjalankan provider nyata)
curl http://localhost:8080/preview/exec-001
```

## Arsitektur Singkat

- **Composition root:** `sam/api/wiring.py` - membangun jalur RuntimeAPI +
  ExecutionRuntime (mode preview) + ConversationPreviewGateway + consumer.
- **Router:** `sam/api/presentation_rest/rest_router.py` - membungkus
  FastAPI APIRouter; endpoint di-inject di wiring.
- **Application:** `sam/api/server.py` - `app` FastAPI, mendaftarkan router
  health/runtime/events/metrics + capability router.
- **Serializer:** `sam/api/presentation_rest/rest_serializer.py` - memetakan
  hasil ke JSON (tidak ada business logic).

Seluruh endpoint TIDAK mengimpor Runtime/Registry/Provider/Connector/
ExecutionRuntime secara langsung di handler (dicegah oleh compliance checker
program K).
