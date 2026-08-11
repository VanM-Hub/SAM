# Canonical Execution Consolidation Audit

- **Tanggal:** 2026-08-12
- **Otoritas:** Van (keputusan arsitektural)
- **Status:** Baseline audit awal (M1) — perlu per-fail verifikasi lanjutan
- **Ruang lingkup:** 77 file `src/sam/universal_{ai,tool,agent,workflow}/` + canonical `execution_runtime/real_harness*.py`

---

## 1. Keputusan arsitektural

| Area | Keputusan |
|---|---|
| Execution path | **Real Execution Path = CANONICAL** |
| `universal_*` | **LEGACY / MIGRATION SOURCE** (bukan execution authority, belum dihapus) |
| Connector baru | Hanya di canonical path |
| Duplicate executor | Dilarang |
| Migrasi | Bertahap, per contract (bukan big-bang rewrite) |
| Target akhir | **Satu execution path** |

Prinsip: *satu capability boleh punya banyak adapter, tapi satu canonical execution boundary.*

---

## 2. Bukti audit (verifikasi langsung source code, 2026-08-12)

### 2.1 `universal_*` tidak memiliki executor nyata
- Heuristik atas 77 file: **0 referensi** ke `ProviderExecutor`, `_call_http`, `httpx`, `requests`, `subprocess`, `docker`, `psycopg`, `sqlite3`, `boto3`.
- `universal_ai` (37), `universal_tool` (26), `universal_agent` (8), `universal_workflow` (6) semuanya `[contract/model]`.

### 2.2 Hidden mock di adapter universal_ai
- `src/sam/universal_ai/openai_adapter.py:44` — `OpenAIAdapter.invoke()` memakai **transport mock default**:
  ```python
  def _mock(payload): return {"choices":[{"message":{"content":"openai-mock-response"}}]}
  if transport is None: transport = _mock
  ```
- Artinya adapter universal_ai **tidak operational secara default** — hanya mock. Ini penyebab `universal_*` bukan execution authority.

### 2.3 Logika orchestrasi bernilai tinggi di universal_* (CALON MIGRATING)
| File | Logika | Nilai |
|---|---|---|
| `universal_ai/provider_invocation.py` | `ProviderInvoker.invoke()` via abstraction (`ProviderAdapter`) | TINGGI — pola invocation boundary sudah benar |
| `universal_tool/governed_tool_invocation.py` | `GovernedToolInvoker.execute()` — chain Request→Capability→Policy→Approval→Execution | TINGGI — **governed execution** sudah benar |
| `universal_tool/capability_resolution.py` | `ToolCapabilityResolver.resolve()` — deterministic | TINGGI |
| `universal_workflow/workflow_execution.py` | `WorkflowExecutionEngine.execute()` — plan→gov→approval→dispatch→verify | TINGGI — orchestrator lengkap |

### 2.4 Abstraction yang layak dipertahankan sebagai contract (ACTIVE-as-contract)
- `universal_ai/adapter_framework.py` — `ProviderAdapter` abstraction murni (transport di-inject, `invoke()` via callable).
- `provider_registry`, `provider_selection`, `provider_identity`, `provider_descriptor` — kontrak provider yang valid.

### 2.5 SEMUA adapter universal_ai = MOCK DEFAULT (bukan operational)
| Adapter | Default invoke | Bukti |
|---|---|---|
| `openai_adapter.py` | `_mock` | `:44` `if transport is None: transport = _mock` |
| `anthropic_adapter.py` | `_mock` | `:35` `_transport if ... else _mock` |
| `google_adapter.py` | `_mock` | `:34` `_transport if ... else _mock` |
| `local_model_adapter.py` | `_mock` | `:34` `_transport if ... else _mock` |

- Pola transport-injection bagus (lihat 2.4), tetapi **tanpa transport eksternal, semua kembali ke mock** -> tidak operational.
- Sebaliknya canonical `real_harness_ai.py` memakai `ProviderExecutor` nyata (httpx) -> **terbukti E2E** (Minimax M3).
- Ini pendorong "hidden mock" yang membuat universal_* bukan execution authority.

---

## 3. Klasifikasi baseline (77 file)

> Klasifikasi ini **baseline** — tiap file wajib diverifikasi per-file sebelum migrasi/dibuang.
> Kelas: **ACTIVE** (kanonik) / **MIGRATING** (diserap canonical dgn E2E proof) / **LEGACY** (dipertahankan utk referensi) / **INVENTORY-ONLY** (contract pasif, dibuang setelah window) / **DEPRECATED** (retire) / **RETIRE** (hapus).

### 3.1 MIGRATING (logika orchestrasi/contract bernilai → diserap canonical)
| Paket | File |
|---|---|
| universal_ai | `provider_invocation.py` |
| universal_tool | `governed_tool_invocation.py`, `capability_resolution.py`, `capability_binding.py`, `tool_contract.py`, `tool_descriptor.py`, `tool_request.py`, `tool_response.py` |
| universal_workflow | `workflow_execution.py`, `workflow_composition.py`, `workflow_foundation.py`, `workflow_state_recovery.py` |
| universal_agent | `agent_contract_framework.py`, `agent_identity.py` |

### 3.2 INVENTORY-ONLY (dataclass/model/compliance pasif — dibuang setelah window)
- `universal_ai`: `conversation_*.py`, `reasoning_*.py`, `response_normalization.py`, `message_model.py`, `context_*.py`, `evidence_context.py`, `experience_context.py`, `operational_context.py`, `failover_assessment.py`, `capability_model.py`, `ai_certification.py`, `ai_provider_compliance.py`, `provider_health.py`, `provider_integration_compliance.py`, `reasoning_compliance.py`, `reasoning_explainability.py`
- `universal_tool`: `connector_*.py`, `tool_*.py` (selain yang di MIGRATING), `connection_management.py`, `tool_execution_compliance.py`, `tool_audit.py`, `tool_certification.py`, `tool_compliance.py`, `tool_discovery.py`, `tool_explorer.py`, `tool_health.py`, `tool_workspace.py`
- `universal_workflow`: `workflow_certification.py`
- `universal_agent`: `agent_collaboration.py`, `agent_foundation.py`, `agent_lifecycle_api.py`, `agent_registry.py`, `agent_workspace_cert.py`

### 3.3 Adapter universal_ai: MOCK DEFAULT -> ganti transport ke canonical `ProviderExecutor`
- `openai_adapter.py`, `anthropic_adapter.py`, `google_adapter.py`, `local_model_adapter.py` — pola adapter bagus, tapi default MOCK.
- Solusi: saat migrasi, `transport` adapter diarahkan ke canonical `ProviderExecutor` (real HTTP), bukan buat executor paralel.
- `adapter_framework.py` — abstraction dipertahankan sebagai contract (MIGRATING/ACTIVE).

---

## 4. Hasil audit M1 — Execution Core SUDAH stabil (single execution authority)

Verifikasi 2026-08-12: `RealExecutionHarness` di `real_harness.py` sudah menjadi **single execution authority**:

- Jalur lengkap: Request -> Capability -> Registry -> Contract -> Policy -> Approval -> Executor -> REAL External -> Verification -> Audit.
- 14 gate P2-B, `ExecutionMode` PREVIEW/EXECUTE, `AuditTrail`, `ControlledApprover`, invariant NO EXTERNAL SIDE EFFECT.
- Terbukti operational (P2C-P11).

Pola pemakaian oleh harness lain (TIDAK ada executor paralel):
| Harness | Boundary | Executor nyata | Status |
|---|---|---|---|
| real_harness_ai | RealExecutionHarness | ProviderExecutor (HTTP) | OK canonical |
| real_harness_nvidia | RealExecutionHarness | ProviderExecutor (NIM HTTP) | OK canonical |
| real_harness_tool | RealExecutionHarness | RealGitHubAdapter | OK canonical |
| real_harness_analyze | RealExecutionHarness | AnalyzeAdapter (filesystem) | OK canonical |
| real_harness_learning | (bukan execution) | ExperienceRepository | OK - learning store, di luar boundary |
| real_harness_agent/investigation/recovery/mission/workflow | RealExecutionHarness | adapter domain | OK canonical |

Kesimpulan: **satu capability banyak adapter, SATU canonical boundary** — prinsip terpenuhi. Tidak perlu bangun Execution Core baru; tugas M1 = memastikan tidak ada jalur paralel (TERPENUHI).

## 6. HASIL MIGRASI M2-M5 (2026-08-12) — selesai

Seluruh migrasi bertahap (M2-M5) dieksekusi non-destruktif. Setiap bridge
menyerap contract bernilai dari universal_* ke canonical boundary TANPA
menghapus/merusak file legacy.

| Phase | Bridge canonical | Serapan | Bukti (test) |
|---|---|---|---|
| M2 | `canonical_tool_contract.py` | ToolContract/ToolCapabilityKind universal_tool | `test_m2_canonical_tool_contract.py` 7/7 |
| M3 | `canonical_ai_bridge.py` | adapter AI universal_ai (mock -> ProviderExecutor HTTP) | `test_m3_canonical_ai_bridge.py` 4/4+1 skip |
| M4 | `canonical_workflow_bridge.py` | WorkflowExecutionEngine orchestrator universal_workflow | `test_m4_canonical_workflow_bridge.py` 5/5 |
| M5 | `canonical_agent_governance.py` | AgentInteractionContract universal_agent | `test_m5_canonical_agent_governance.py` 5/5 |

Garansi yang dibuktikan semua bridge (bukan mock):
- Tanpa approval / tanpa kredensial -> BLOCKED / ProviderUnavailableError (NO EXTERNAL SIDE EFFECT).
- Fail-fast workflow -> no partial commit.
- Agent TIDAK megang adapter langsung; semua lewat canonical request_capability.
- Verification + audit tercatat untuk tiap eksekusi nyata.

Regression (seluruh execution_runtime + universal_*): **429 passed, 1 skipped, 2 xfailed** — tidak ada regresi.

## 8. M6-001 — Universal HTTP Connector (2026-08-12) — PROVEN

Primitive connector pertama Operational Expansion. `src/sam/execution_runtime/canonical_http_connector.py`:
- SATU jalur eksekusi = `RealExecutionHarness` / capability `http` (no second executor).
- Endpoint = konfigurasi (`HttpEndpoint`: name/method/url_template/auth_env/required_params) — generik, bukan hardcoded per API.
- Tanpa mock default: endpoint tak dikenal / param wajib kosong / kredensial ber-auth kosong -> RAISE/BLOCKED (NO SIDE EFFECT).
- Verification nyata: HTTP 200 + JSON valid + payload sesuai kontrak wajib; selain itu dianggap gagal.
- PREVIEW explicit simulated, TIDAK menyamar sebagai execution.

**Bukti E2E nyata (minimal 2 API berbeda):**

| External API | Result | Verified |
|---|---|---|
| JSONPlaceholder GET /posts/1 | 200, id=1, title real | ya |
| httpbin GET /get | 200, echo url=https://httpbin.org/get | ya |
| JSONPlaceholder GET /users/1 | 200, id=1, email real | ya |

Test `tests/execution_runtime/test_m6_http_connector.py` **9/9 passed** (5 structural + 4 E2E).
Executed E2E proof JSON: `docs/engineering/reports/M6-001_HTTP_Connector_E2E_Proof.json` (ok=True, http_status=200, 22 audit entries).
Regression execution_runtime: **301 passed, 1 skipped, 2 xfailed** — tidak ada regresi.

Syarat "HTTP connector terbukti dengan minimal dua external API berbeda" TERPENUHI -> berhak lanjut Database Connector (M6-002).

## 7. Status akhir canonical execution consolidation

- Execution Core canonical (RealExecutionHarness) = single execution authority (M1, proven P0-P11).
- Contract universal_* bernilai -> diserap ke canonical (M2-M5), legacy dipertahankan.
- Tidak ada executor paralel baru; bridge hanya pengarah, bukan executor.
- "Capability Truth ≠ Architecture Inventory" tetap: 9 capability PROVEN, universal_* inventory tidak operational sendirian tapi kini bisa dipakai via canonical.

Next (bila Van setuju): buka area operasional baru (HTTP Universal Connector, Database/PostgreSQL, Docker/Process, Email, Browser) -- SEMUA hanya di canonical path.

---

## 5. Catatan penting

- **Capability Truth ≠ Architecture Inventory.** 9 capability PROVEN ≠ 77 file universal_* operational.
- Real Execution Path terbukti operational (P0–P11); universal_* hanya inventory.
- Tidak ada penghapusan massal sebelum setiap contract dimigrasikan atau dinyatakan obsolete secara eksplisit.
