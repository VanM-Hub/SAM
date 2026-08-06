# ENG-J - Laporan Akhir Program J (REST API)

**Program:** J (REST API) - **Package:** AP-MISSION-005-001 - **Status:** SELESAI
**Tanggal:** 2026-08-06

---

## 1. Ringkasan

Program J menjadikan REST API (`sam.api`) sebagai **host operasional resmi
Project SAM** - Presentation Capability yang diakses seluruhnya melalui jalur
resmi `runtime_service.api`. Struktur host dibangun baru di `sam/api/
presentation_rest/` (`RESTApplication`, `RESTRouter`, `RESTEndpoint`,
`RESTSerializer`), seluruh endpoint capability di-wire ke `ConversationPreviewGateway`
via Dependency Injection di entry (`sam/api/wiring.py`). Host dibuat **independen**
dari `sam/web/server.py` (dashboard Program G/H/I) sesuai keputusan Lead Engineer.

Rewire dilakukan pada `/runtime` (sebelumnya import langsung `RuntimeCoordinator`)
dan `/health` (sebelumnya instansiasi `WebRuntimeService()` langsung) ke jalur
resmi `runtime_service.api`. Tidak ada akses langsung ke Runtime/Registry/
Provider/Connector/ExecutionRuntime di endpoint handler, dan tidak ada perubahan
RuntimeService.

## 2. File Berubah

| File | Peran |
|---|---|
| `src/sam/api/presentation_rest/rest_application.py` | `RESTApplication` - host (FastAPI app + registrasi router) |
| `src/sam/api/presentation_rest/rest_router.py` | `RESTRouter` + `RESTEndpoint` (DTO immutable, ADR-023) |
| `src/sam/api/presentation_rest/rest_serializer.py` | `RESTSerializer` (pemetaan hasil -> JSON) |
| `src/sam/api/presentation_rest/__init__.py` | export capability |
| `src/sam/api/wiring.py` | composition root - jalur resmi `runtime_service.api` (DI) + register endpoint |
| `src/sam/api/server.py` | composition root FastAPI (include router lama + capability) |
| `src/sam/api/routes/health.py` | rewire `/health` -> `gateway.api.health()` (hapus `WebRuntimeService()` langsung) |
| `src/sam/api/routes/runtime.py` | rewire `/runtime` -> `gateway.api.status()` (hapus import `RuntimeCoordinator`) |
| `tests/api/test_rest_capability.py` | unit + integration test Program J (19) |

> `src/sam/api/routes/events.py` & `metrics.py` dipertahankan apa adanya
> (Telemetry = **Deferred**, tidak disentuh per keputusan Lead).

## 3. Hasil Test

| Scope | Hasil |
|---|---|
| Unit/integration Program J (`test_rest_capability.py`) | **19 passed** |
| Test lama REST (`tests/api/test_api.py`) | **11 passed** |
| Regression `tests/api/` (termasuk web dashboard) | **51 passed** |
| Regression `tests/runtime_service/` | **283 passed** |
| Regression `tests/presentation/` (Program G/H/I) | **250 passed** |
| Sprint verification (`test_sprint31`, `test_sprint32` - import `sam.api.server`) | **76 passed** |

Total regression scope Program J: **584 passed** (api + runtime_service + presentation).

> Warning `datetime.utcnow()` deprecation di beberapa module = pre-existing,
> tidak terkait file Program J.

## 4. Endpoint (Activation Matrix)

Semua endpoint dengan activation path resmi tersedia via `runtime_service.api`:

| Endpoint | Jalur | Status |
|---|---|---|
| workflow | `preview_with_workflow` | Available |
| policy | `preview_with_policy` | Available |
| audit | `preview_with_audit` | Available |
| preview | `preview` (no execute) | Available |
| knowledge | `preview_with_knowledge` | Available |
| memory | `preview_with_memory` | Available |
| artifact | `preview_with_artifact` | Available |
| approval | pass-through (baca `approved` dari outcome) | Pass-through |
| runtime | `gateway.api.status()` (rewire) | Available |
| health | `gateway.api.health()` (rewire) | Available |
| status | `gateway.api.status()` | Available |
| mission | - (no activation path) | Deferred by Architecture |

## 5. Area Deferred / Escalation

| Area | Keputusan |
|---|---|
| mission | Deferred by Architecture (no activation path di `runtime_service.api`) - tanpa workaround |
| telemetry (`/events`, `/metrics`) | Deferred (belum ada activation path resmi) - dipertahankan, tidak di-rewire |

## 6. Acceptance Criteria

- [x] REST API tersedia sebagai host operasional resmi (`sam.api`).
- [x] Seluruh endpoint dengan activation path resmi tersedia (workflow, policy,
      audit, preview, knowledge, memory, artifact, status).
- [x] Approval bersifat pass-through (tidak membuat Approval baru).
- [x] Mission diklasifikasikan Deferred by Architecture (no activation path).
- [x] Seluruh akses melalui `runtime_service.api` (via `ConversationPreviewGateway`).
- [x] Tidak ada dependency langsung ke Runtime/Registry/Provider/Connector/ExecutionRuntime
      di endpoint handler & presentation host.
- [x] Regression PASS (584) + unit/integration PASS (30).
- [x] Tidak ada perubahan baseline Architecture, RuntimeService, activation path,
      Runtime, Registry, atau ADR.

---

*Ditandatangani oleh Executor: ZARA*
