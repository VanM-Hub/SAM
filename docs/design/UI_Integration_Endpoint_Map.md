# UI Integration — Endpoint Map + Peta Implementasi Final (UI v18 → SAM)

Engineering verification oleh Zara · 2026-08-15
Prinsip: **STOP. INSPECT REPOSITORY & AUTHORITATIVE CONTRACTS. DO NOT INVENT ENDPOINT/SERVICE.**
Dokumen ini = hasil reconnaissance `src/sam` untuk Ward / Provider / Credential / Guardian / Control Panel, lalu peta implementasi final.

---

## 1. Kontrak yang dipegang (dari Arsitek UI)

### 1.1 Semantic identity
| Nama | Adalah | BUKAN |
|---|---|---|
| OpenClaw | named external service | ≠ automatically Ward |
| GitHub | named platform | ≠ Ward |
| VanM-Hub/SAM | specific external resource | → may be Ward setelah entrustment |
| Provider | capability supplier | ≠ Ward |
| Connector | transport/effect channel | ≠ Ward |
| Credential | secret pemegang akses | ≠ Provider |
| Mission Target | objek sasaran satu mission | ≠ Ward baru |

### 1.2 Menu → semantic role
`Home`=Situational awareness · `Mission Control`=Human↔Mission · `Wards`=Entrusted external entities · `Guardian`=Observation/guarding · `Control Panel`=Runtime·Governance·Records
→ Kelima menu BUKAN lima backend service.

### 1.3 Kategori tombol
Navigation / Query·Refresh / Configuration / Approval / Execution
- **Approve** → UI kirim *decision intent* → canonical ApprovalGate. UI TIDAK melakukan approval.
- Jalur efek: `UI → MissionUXService → Approval → Canonical Execution → Connector → Effect → Verify → Evidence/Audit → State → UI`

### 1.4 Credential (aturan terketat)
```
API Key → Secure Credential Boundary → Provider / Connector   ✓
API Key → Chat / Mission / Evidence / Activity / Audit / Browser state   ✗
```

### 1.5 Forbidden assumptions
Jangan relasikan berdasar nama. Hierarki: `Constitution → Architecture → Spec/ADR → Runtime/App Contracts → UI Integration Contract → UI Implementation`.

---

## 2. Hasil reconnaissance `src/sam` (bukti, bukan tebakan)

### 2.1 Composition root (`src/sam/api/wiring.py`) — APA YANG SEBENARNYA HIDUP DI RUNTIME
Hanya membangun **preview execution path** (ADR-008 sec 12, `external_calls=0`):
- `ExecutionRuntime` + `ExecutionEngine` (mode preview)
- `ConversationPreviewGateway` (terkonfigurasi: provider `filesystem`)
- 6 preview consumer: knowledge/workflow/artifact/memory/policy/audit — **masing-masing registry EMPTY in-memory**
- `RESTApplication` + endpoint capability J3–J10 (semua read-only preview)

> ⚠️ **Tidak ada** `WardRepository`, `AIProviderRegistry`, `CredentialBoundary`, Guardian, yang di-instantiate di sini.

### 2.2 Bukti ketersambungan (grep)
| Domain | Import `sam.*` dari luar domain | `XxxRepository()` di `src/` | Kesimpulan |
|---|---|---|---|
| **Ward** (`sam/ward`) | HANYA referensi internal paket + TES | **0** (hanya di `tests/ward/`) | Domain matang (M13) tapi **TIDAK di-wire ke runtime** — tanpa application boundary, tanpa REST |
| **Provider** (`AIProviderRegistry`, `ProviderExecutor`) | internal + wiring internal preview | hanya dipakai dalam preview | **TIDAK ada endpoint daftar provider**; registry instance (`environment/providers.py`) hanya aktif di skrip E2E |
| **Credential** (`CredentialBoundary`) | internal M8/M11 | dipakai di jalur execution | Boundary nyata, tapi **TIDAK ada endpoint** expose status/count (benar — secret tak pernah keluar) |
| **Guardian** (`m14_close_guardian.py`) | **fixture-only untuk proof E2E** (di docstring file) | 0 | Bukan permukaan runtime produksi → **tidak ada endpoint** |

---

## 3. Peta Implementasi FINAL
Legenda status: ✅ READY (ada endpoint + wiring) · ⚠️ SEBAGIAN (ada, tapi preview/empty) · ❌ TIDAK ADA (perlu keputusan arsitektur)

### Tahap 1 — READY untuk integrasi (Home + Mission Control via `/ux`, jalur efek nyata)
| UI element | Semantic entity | Owner | Existing class/service | Endpoint | Request → Response | State transition | Evidence/Audit | Status |
|---|---|---|---|---|---|---|---|---|
| Mission Control — chat | Human↔Mission (submit) | MissionUXService | `src/sam/application/ux/service.py` | `POST /ux/submit` | `{text, idempotency_key}` → `UxMissionState` | SUBMITTED → PLANNING/REASONING → WAITING_FOR_APPROVAL | tercatat dalam state | ✅ |
| Mission Control — Setujui | Approval decision intent | `decide(APPROVE)` | canonical `ApprovalGate` + `runner.run_mission` | `POST /ux/decide` | `{intent:'approve', approver}` → state | WAITING_FOR_APPROVAL → EXECUTING → VERIFYING → COMPLETED/BLOCKED/FAILED | `evidence`, `audit` tercatat | ✅ |
| Mission Control — Jangan lakukan | Approval reject | `decide(REJECT)` | canonical ApprovalGate | `POST /ux/decide` | `{intent:'reject'}` → state | WAITING_FOR_APPROVAL → REJECTED (0 mutation) | `audit` tercatat | ✅ |
| Mission Control — workspace stages | observe | `get_state()` | `service.py` | `GET /ux/state` | — → `UxMissionState` (request_id dari runtime, bukan UI) | timeline Observe→Investigate→Recommend→Decision→Execute→Verify | — | ✅ |
| Mission Control — evidence | observe | `get_evidence()` | `service.py` | `GET /ux/evidence` | — → `evidence[]` | — | evidence chain (sanitized) | ✅ |
| Mission Control — audit | observe | `get_audit()` | `service.py` | `GET /ux/audit` | — → `audit[]` | — | audit trail (no secret) | ✅ |
| Home — mission/keputusan | situational awareness | `get_state()` + TelemetryService | `service.py` + `telemetry/` | `GET /ux/state` + `GET /events` | — → state + events[] | — | event telemetry | ✅ (`/events` sempat 500, difix sesi ini) |
| Home — status SAM | situational awareness | gateway.api | runtime_service | `GET /runtime` + `GET /health/ready` | — → version/healthy/services | — | — | ✅ |
| Login overlay | human identity | `identity.py` UserStore/SessionStore | `src/sam/application/ux/identity.py` | `POST /ux/login`, `GET /ux/me`, `POST /ux/logout` | cred → cookie httpOnly; 401→showLogin | sesi aktif/revoked | — | ✅ |

### Control Panel — ⚠️ SEBAGIAN (Runtime nyata; Records/Governance preview/empty)
| UI element | Endpoint | Req→Res | Status | Catatan jujur |
|---|---|---|---|---|
| Runtime — health | `GET /health/ready`, `GET /runtime`, `GET /metrics` | → ready/healthy/telemetry | ✅ | jalur resmi, nyata (M12/M10) |
| Records — Activity | `GET /events` | → events[] (limit, severity) | ✅ | TelemetryService nyata |
| Records — Audit | `GET /ux/audit` + `GET /audit/` | → audit trail + audit_ids | ✅ / ⚠️ | `/ux/audit` = M9 nyata; `/audit/` = preview registry AUDIT → akan kosong |
| Records — Evidence | `GET /ux/evidence` | → evidence[] | ✅ | M9 nyata |
| Governance — Policy | `GET /policy/` + `GET /policy/{id}` | → policy_ids + resolve | ⚠️ | `PolicyPreviewConsumer` di atas **registry EMPTY** → UI tampil "belum ada data" (jujur) |
| Governance — Status | `GET /status/` | → status runtime (preview) | ⚠️ | status preview execution path |
| Governance — Verification | — | — | ❌ | tidak ada endpoint verifikasi khusus |

### ❌ TIDAK ADA backend — perebutan keputusan arsitektur (UI wajib empty state jujur)
| UI element | Semantic entity | Owner | Kelas yang ADA (tapi belum di-wire) | Endpoint | Status | Wajib putusan |
|---|---|---|---|---|---|---|
| Wards — daftar & detail | Entrusted external entities | WardRegistry | `sam/ward/registry/registry.py` (WardRepository: register/get/list/revoke) | **tidak ada** | ❌ domain ada, 0 wiring runtime | Expose ward sebagai endpoint read-only? |
| Wards — Add Ward (modal) | Configuration (entrustment) | WardRegistry + Ownership | `sam/ward/entrustment/models.py` (Entrustment) · `governance/boundary.py` (WardGovernanceBoundary) | **tidak ada** | ❌ | Entrustment = keputusan konsen Owner — design dulu |
| Guardian — state & activity | Observation/guarding | Guardian | `m14_close_guardian.py` (fixture-only) · `operations/brain/guardian/supervisor.py` | **tidak ada** | ❌ bukan produksi | Guardian produksi belum ada → UI jujur |
| Control Panel — Providers | Runtime (query) | Provider registry | `AIProviderRegistry` (`universal_ai/provider_registry.py`) · `ProviderExecutor` · `environment/providers.py` | **tidak ada** | ❌ | Provider list-resolve belum diverifikasi ter-wire |
| Control Panel — Credentials | Configuration (secret) | CredentialBoundary | `execution_runtime/credential_boundary.py` · `runtime_service/secrets/*` | **tidak ada (sengaja)** | ✅ benar | Secret TIDAK pernah diekspos. UI hanya boleh "n configured" bila ada sumber hitungan aman — belum ada |
| Provider modal (save) | Configuration (activation) | — | activation via canonical boundary | **tidak ada** | ❌ | aktivasi vs CRUD — beda |

---

## 4. Kesimpulan
1. **Jalur efek nyata hanya satu**: `/ux/*` (MissionUXService → ApprovalGate canonical → run_mission → connector). Persis jalur yang ditulis arsitek. ✓
2. **Tahap 1 aman diintegrasikan kini**: Home + Mission Control (6 endpoint `/ux` + `/runtime` + `/health/ready` + `/events`) - terbukti produksi (M9, M10).
    - **Status 2026-08-15 (commit `5c4e75b`, pushed)**: `mission_workspace_v18.html` (dari template v18) telah di-wire ke `/ux/*` nyata + `/events` + login, disajikan di `/ui/v18`. 0 data fiktif. `/ux/decide` memakai kontrak asli `{intent}`. Context schema `/ux/state`: status di `approval.status` & `execution.status` (bukan top-level).
3. **Control Panel**: Runtime nyata (✅) · Records sebagian (✅/⚠️) · Governance ⚠️ (registry preview kosong, tampil "belum ada" jujur).
4. **Wards / Guardian / Providers / Credentials**: **bukan soal "nyambung UI"** — ini **pekerjaan backend + keputusan arsitektur**. Domain Ward/Provider/Credential/Guardian ada sebagai kode + test, tapi **tidak di-wire ke composition root** (`wiring.py`) dan tidak punya REST. Sesuai STOP-rule, UI TIDAK boleh mengarang `/wards`, `/guardian`, `/providers`, `/credentials`.
5. **Untuk elemen tanpa backend → UI wajib empty state jujur** ("belum tersedia"), bukan data palsu, sampai ada keputusan arsitektur untuk men-wire domain tsb.
