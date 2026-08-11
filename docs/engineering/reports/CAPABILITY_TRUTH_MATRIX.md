# CAPABILITY_TRUTH_MATRIX — SAM Operational Truth (P0)

> **Tujuan:** Mengganti seluruh klaim "capability berfungsi" dengan status berbasis bukti nyata (source line + real external effect).
> **Aturan:** `IMPLEMENTED ≠ OPERATIONAL`. Tanpa keenam bukti (Source + Test + Real External Effect + Real Verification + Audit Evidence + Repeatable Run) → **UNPROVEN**, bukan COMPLETE.
> **Tanggal:** 2026-08-12 · **Auditor:** Zara (Engineer)

---

## 0. Legenda Status

| Status | Arti | Syarat |
|---|---|---|
| **UNPROVEN** | Source+test ada, tapi tidak ada real external effect yang diverifikasi | Tidak lolos Definition of Done |
| **PARTIAL** | Sebagian jalur nyata ada (mis. jalur HTTP ter-wire tapi di-lock preview) | Butuh aktivasi + E2E real |
| **PROVEN** | Ada real external side effect + verification + audit + repeatable | Lolos DoD |
| **BLOCKED** | Ada hambatan arsitektural/ADL yang menahan eksekusi nyata | Perlu keputusan/ADR |

---

## 1. Capability Truth Ledger

| # | Capability | Folder Source | Source | Test | Real External | E2E | Status | Bukti Utama |
|---|---|---|---|---|---|---|---|---|
| 1 | AI Provider | `universal_ai/` + `providers/execution/` | ✅ | ✅ | ⚠️ transport ada, di-lock preview | ❌ | **PARTIAL** | Adapter mock + `httpx.post()` nyata ada, tapi activation di-lock preview |
| 2 | Tool | `universal_tool/` | ✅ | ✅ | ❌ | ❌ | **UNPROVEN** | `governed_tool_invocation.py:116` → hanya `GovernanceDecision`, tidak panggil apa pun |
| 3 | Agent | `universal_agent/` | ✅ | ✅ | ❌ | ❌ | **UNPROVEN** | Governance layer saja, tanpa real execution authority |
| 4 | Workflow (state-only) | `universal_workflow/` | ✅ | ✅ | ❌ | ❌ | **PARTIAL** | State/checkpoint/resume ada; tapi orchestration NYATA ditangani RealWorkflow (lihat #12) |
| 5 | Investigation | `operational_intelligence/` | ✅ | ✅ | ❌ | ❌ | **UNPROVEN** | Analisis berbasis data internal, bukan observasi sistem nyata |
| 6 | Learning | `operational_learning/` | ✅ | ✅ | ❌ (persist belum dibuktikan di deployment) | ❌ | **UNPROVEN** | Persistence append-only klaim, perlu bukti restart |
| 7 | Reasoning | `governed_reasoning/` | ✅ | ✅ | ⚠️ (ada llm_compliance HTTP import) | ❌ | **PARTIAL** | HTTP import ada tapi jalur execute belum diaktifkan |
| 8 | Recovery | `autonomous_operations/` | ✅ | ✅ | ❌ | ❌ | **UNPROVEN** | Recovery hanya `success=True` function, tanpa bukti state eksternal |
| 9 | Workspace | `operational_workspace/` | ✅ | ✅ | ❌ | ❌ | **UNPROVEN** | Workspace + end_to_end_flow ada, tanpa side effect nyata |
| 10 | Governance | `execution_runtime/` + stack | ✅ | ✅ | ⚠️ | ⚠️ | **PARTIAL** | Approval→Execution→Verification→Audit terdefinisi & di-lock preview |
| **11** | **Filesystem** | `execution_runtime/real_harness.py` + `real_harness_analyze.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **Real read/hash/meta/analyze + verify + audit + deterministic (P2-C + P3)** |
| **12** | **Workflow (RealExecutionHarness)** | `execution_runtime/real_harness_workflow.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **Orchestrasi 3 langkah nyata (meta→analyze→write) + produk tertulis + audit (P6)** |
| **13** | **Agent (RealAgent)** | `execution_runtime/real_harness_agent.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **discovery→request→governance→approve→real tool→verify→audit, bypass DENIED (P7)** |
| **14** | **Investigation (Real)** | `execution_runtime/real_harness_investigation.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **real observation→evidence→diagnosis→root cause→recommendation→lineage (P8)** |
| **15** | **Recovery (Real)** | `execution_runtime/real_harness_recovery.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **state eksternal berubah nyata + independent verification (P9)** |
| **16** | **Learning (Real)** | `execution_runtime/real_harness_learning.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **persisted ke disk + retrieved setelah restart (P10)** |
| **17** | **Full Mission** | `execution_runtime/real_harness_mission.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **request→reason→investigate→recommend→approve→recover→verify→artifact→audit→learn (P11)** |
| **18** | **Tool GitHub (RealAdapter)** | `execution_runtime/real_harness_tool.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **HTTP nyata get_repo ke GitHub, respon 200, data asli (P5, dengan token valid)** |
| **19** | **AI Provider NVIDIA (Real)** | `execution_runtime/real_harness_nvidia.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **HTTP nyata ke Nvidia NIM, model 'minimaxai/minimax-m3' (favorit Van) menjawab 'PROVEN', finish=stop (P4)** |
| **20** | **HTTP Connector (M6)** | `execution_runtime/canonical_http_connector.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **HTTP nyata GET ke 2 API eksternal berbeda (JSONPlaceholder + httpbin), 200+JSON valid, gate P2-B, verifikasi kontrak, audit; generic config-based endpoint (6f1ffed)** |
| **21** | **SQLite Database Connector (M6)** | `execution_runtime/canonical_db_connector.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **SQL genuine di SQLite: SELECT users/posts nyata (3 baris Aster/Zara/VanM), limit, audit; tanpa mock (a15e18e)** |
| **22** | **Process Connector (M6)** | `execution_runtime/canonical_process_connector.py` | ✅ | ✅ | ✅ E2E real | ✅ | **PROVEN** ✅ | **subprocess NYATA via allowlist read-only (hostname=VM, python --version), exit 0, output diverifikasi,audit (5d4d507)** |
| **23** | **Email Connector (M6)** | `execution_runtime/canonical_email_connector.py` | ✅ | ✅ | ⚠️ dry_run only (sent:false) | ❌ | **PARTIAL** | **Validas format real + gate SMTP + dry_run jujur; kirim SMTP NYATA belum terbukti (tanpa server/kredensial) -> sent:false (41a31dc)** |
| **24** | **Browser Connector (M6)** | `execution_runtime/canonical_browser_connector.py` | ✅ | ✅ | ⚠️ fetch HTTP only | ❌ | **PARTIAL** | **fetch_url HTTP nyata (httpbin 200); render headless Chromium (browser automation) belum terbukti (c61deb8)** |

**Kesimpulan ledger:** 6 UNPROVEN (legacy universal_*) · 2 PARTIAL (Email Connector, Browser Connector) · **12 PROVEN** (Filesystem, Workflow-harness, Agent, Investigation, Recovery, Learning, Mission, Tool-GitHub, AI-NVIDIA, **HTTP Connector, SQLite Database, Process Connector**).

---

## 2. Bukti Kunci per Capability (Source Line)

### 2.1 AI Provider → PARTIAL (bukan UNPROVEN)
`src/sam/universal_ai/openai_adapter.py` baris 35-38:
```python
if self._transport is not None:
    raw = self._transport(payload)   # HTTP nyata (hanya jika transport diisi)
else:
    raw = self._mock(payload)        # DEFAULT = mock
# _mock(payload) → "openai-mock-response"
```
- **Temuan:** Default adalah `_mock()`. Namun **jalur HTTP nyata ada** di `providers/execution/provider_executor.py:144-154` (`httpx.post(...)`) dan sudah ter-wire ke `api/llm_wiring.py:224` + `api/wiring.py:84`. Jalur ini **di-lock oleh mode preview** (lihat 2.3).
- Adaptor lain (Anthropic `anthropic_adapter.py`, Google `google_adapter.py`, local `local_model_adapter.py`) juga punya `_mock()` — pola sama (scan mock: 4 file).
- **Status: PARTIAL** — semua komponen ada (adapter, executor, wiring), activation diblok preview; real E2E belum terbukti.

### 2.2 Tool → tidak memanggil apa pun (UNPROVEN)
`src/sam/universal_tool/governed_tool_invocation.py` baris 97-125 (ringkas):
```python
decisions = [
  GovernanceDecision(ExecutionStage.REQUEST, ...),
  GovernanceDecision(ExecutionStage.CAPABILITY_RESOLUTION, ...),
  GovernanceDecision(ExecutionStage.POLICY_VALIDATION, ...),
  GovernanceDecision(ExecutionStage.APPROVAL, ...),
  GovernanceDecision(ExecutionStage.EXECUTION, True),  # cuma catat "lulus"
]
return ToolExecutionContext(..., params=params)  # params dimasukkan, TIDAK dieksekusi
```
- **Temuan:** Tidak ada import `requests`/`httpx`/connector. `params` hanya masuk ke context, tidak dipakai untuk memanggil GitHub/PostgreSQL/Docker/Gmail apapun.

### 2.3 Jalur HTTP nyata ADA tapi DILOCK (bagian penting)
`src/sam/providers/execution/provider_executor.py`:
- baris 144-154: `_call_http()` → `httpx.post(...)` — **panggilan HTTP nyata benar-benar ada**.
- baris 34-43: endpoint real OpenAI/Anthropic/Gemini/Deepseek/Ollama.

**Tapi jalur ini di-lock oleh mode preview:**
- `src/sam/runtime_service/api/execution_preview_wiring.py:11` → *"Provider TIDAK dieksekusi (mode preview bukan execute)"*
- `src/sam/web/server.py:119` → *"Provider TIDAK dieksekusi (preview, ADR-008 sec 12)"*
- `src/sam/mission_cognition/runtime.py:381` → `mode="preview"  # ADR-008 sec 12: provider tidak dieksekusi`

### 2.4 Analisis rujukan "ADR-008 sec 12" → misreading (lihat P2-A)
- Komen kode merujuk "ADR-008 sec 12: provider tidak dieksekusi".
- **Cek `docs/adr/ADR-008…md`:** Section 12 = "Architectural Boundaries" dan **menyertakan langkah Execution** dalam rantai resmi (Citizen→Capability→Registry→Contract→Approval→Execution→Audit). Section 12 **TIDAK menyebut preview / larangan eksekusi**.
- **Kesimpulan (detail di `P2A_Audit_Preview_Execute_References.md`):** komentar "sec 12: provider tidak dieksekusi" adalah **misreading** — Section 12 justru mendukung execution. Ini keputusan implementasi (default preview), bukan larangan arsitektur.

### 2.5 Sandbox = simulasi penuh
`src/sam/operations/sandbox.py` baris 119-151: semua operasi kembali string `"Simulated ..."`.
- `"Simulated read: {} ({} bytes)".format(target, len(parameters.get("content","")))` — **bahkan tidak membaca file asli**, hanya mengukur panjang string yang diberikan.
- `OperationsExecutor` (`operations/real_executor.py`) tidak pernah membaca/menulis file nyata; semua lewat sandbox.

---

## 3. Hasil Scan Otomatis (mock vs http per folder)

| Folder | File dgn mock | File dgn HTTP nyata |
|---|---|---|
| `universal_ai` | 4 (openai/anthropic/google/local adapter → `_mock`) | 0 |
| `universal_tool` | 0 | 0 |
| `universal_agent` | 0 | 0 |
| `universal_workflow` | 0 | 0 |
| `governed_reasoning` | 0 | 1 (`llm_compliance.py` — import lib saja) |
| `operational_intelligence` | 0 | 1 (`investigation_compliance.py` — import lib saja) |
| `providers` | 2 (preview_mode) | 1 (**`provider_executor.py` → httpx nyata**) |
| `execution_runtime` | 0 | 0 |
| `runtime_service` | 6 (preview_mode) | 0 |

> **Catatan penting:** Scan HTTP menangkap *import library* (mis. `import httpx`), bukan berarti jalur aktif. Satu-satunya jalur HTTP nyata yang terimplementasi adalah `provider_executor.py` — tapi di-lock preview (lihat 2.3).

---

## 4. Pelanggaran Definition of Done (dari laporan MISSION)

| Laporan | Klaim | Fakta |
|---|---|---|
| MISSION-5.1/5.2/5.4 | "implementation complete" | Benar bahwa *kode governance* ada; **salah** jika diartikan "capability operational" |
| MISSION-4.1 line 247 | "Provider Execution Readiness Level 6 (Certified)" | **Salah** — line 259-260 dokumen yang sama mengakui "HTTP nyata belum diverifikasi, uji pakai mock" |
| MISSION-4.2 line 223 | "Operational Intelligence Level 6 (Certified)" | **Salah** — tidak ada observasi sistem nyata |
| Daftar_Capability | daftar "potensi fungsi" | Daftar potensi ≠ capability terbukti |

Menurut model Readiness SAM sendiri (0 Defined → 6 Certified), kondisi nyata adalah:
- **Level 0-1 (Defined/Implemented):** hampir semua capability.
- **Tidak ada yang mencapai Level 4+ (External Verified / Operational)** karena tidak ada real external operation.

---

## 5. Temuan Prioritas (untuk eksekusi berikutnya)

| # | Temuan | Severity | Rekomendasi |
|---|---|---|---|
| 1 | Default AI adapter = mock | 🔴 Tinggi | Output dari Daftar_Capability harus ditandai UNPROVEN sampai jalur execute + real credential aktif |
| 2 | Jalur HTTP nyata ada tapi di-lock preview | 🔴 Tinggi | Klarifikasi Aster: kebijakan resmi mode execute + syarat minimalnya |
| 3 | Rujukan "ADR-008 sec 12" tidak ada di ADR | 🟠 Sedang | Tulis/klarifikasi aturan mode ke ADR resmi (jangan komentar implisit) |
| 4 | Sandbox 100% simulasi | 🟠 Sedang | Untuk Phase 3, gunakan `SAM_TEST_WORKSPACE/` nyata (bukan sandbox) |
| 5 | Recovery `success=True` tanpa bukti state eksternal | 🟠 Sedang | Phase 9: wajib bukti keadaan eksternal berubah |
| 6 | Laporan MISSION klaim Level 6 tanpa E2E nyata | 🔴 Tinggi | Fase 12: ganti metrik "76 tests → Certified" dengan L0-L7 berbasis evidence |

---

### 2.7 Filesystem → PROVEN (P2-C + P3) ⭐
`src/sam/execution_runtime/real_harness.py` + `real_harness_analyze.py`:
- `RealExecutionHarness` mengevaluasi **14 gate P2-B** sebelum EXECUTE; invariant `NO EXTERNAL SIDE EFFECT` bila ada gate gagal.
- `RealFilesystemAdapter` menyentuh disk nyata: `read` (konten 74 byte), `hash` (`sha256` 64 hex), `meta` (`size=75, mtime`).
- `AnalyzeAdapter` memakai `sam_analyzer._analyze_file` pada file NYATA:
  - `_demo/sample_data.xlsx` → `total_issues=5` (3 sel kosong, 1 duplikat, 1 sheet kosong) — **3 run → deterministik [5,5,5]**.
  - `_demo/sample_app.log` → `total_issues=16` (5 error, 5 warn, 1 critical, 3 fail, 2 timeout) — **2 run → deterministik [16,16]**.
- **Verified:** `_verify_external_effect` / `_verify_analyze` `passed=True`; **Audit:** 21 entries/run.
- **Bukti JSON:** `_demo/sample_data_p3_report.json`, `_demo/sample_app_p3_report.json`.
- **Status: PROVEN** — lolos DoD (real external effect + verification + audit + repeatable run).

### 2.8 Workflow (RealExecutionHarness) → PROVEN (P6) ⭐
`src/sam/execution_runtime/real_harness_workflow.py`:
- `RealWorkflow` mengorkestrasi **3 langkah nyata berurutan** pada `_demo/sample_data.xlsx`:
  1. `meta` → `size=5511` (stat disk nyata) ✅
  2. `analyze` → `total_issues=5` ✅
  3. `write_report` → **laporan 557 byte tertulis nyata** ke `_demo/workflow_out/sample_data_workflow_report.txt` ✅
- Tiap langkah dievaluasi **14 gate P2-B**; correlation ID tunggal `5579e688...` menautkan semua.
- **Produk nyata diverifikasi di disk** (file eksis + isi terbukti). Audit penuh.
- **Status: PROVEN** — real external effect (produk tertulis) + keamanan gate + audit + repeatable.

### 2.9 Agent/Investigation/Recovery/Learning/Mission → PROVEN (P7–P11) ⭐
`src/sam/execution_runtime/real_harness_{agent,investigation,recovery,learning,mission}.py`:
- **Agent (P7):** `RealAgent` tidak memegang adaptor — hanya `request_capability(...)` lewat harness.
  Rantai: discovery → request → governance → approval → real tool (filesystem) → real result → verify → audit.
  **Bypass attempt DENIED** (`agent.bypass.attempt`). Bukti: `_demo/p7_agent-007_*.json` (analyze=5 issue, hash=sha256, read=isi log nyata).
- **Investigation (P8):** input dari state eksternal nyata (file di disk). Rantai: real observation → evidence
  → diagnosis → root cause → recommendation → **evidence lineage** (`derived_from`, `addresses`).
  Env masalah nyata: `env_empty.log`(0 baris), `env_sparse.log`(8/5 kosong), `env_healthy.log`.
  Bukti: `_demo/p8_investigation.json`.
- **Recovery (P9):** **bukan flag `success=True`** — `svc-orders.state` berubah `stopped→running` di disk,
  independent health check baca ulang → `healthy=True`. Bukti: `_demo/recovery_sandbox/` + `_demo/p9_recovery.json`.
- **Learning (P10):** experience di-`store` ke `learning_store.json` (disk), **restart instance baru**,
  lalu `retrieve` sukses (data tidak hilang). Bukti: `_demo/p10_learning.json`.
- **Full Mission (P11):** rantai lengkap pada satu mission nyata "pulihkan svc-orders":
  request→reason→investigate→recommend→approve→recover(stopped→running)→verify(healthy)→artifact(tulisan disk)
  →audit(13) →learn(experience di-store). Bukti: `_demo/mission_out/M-DEMO01_report.txt` + `_evidence.json`.

### 2.10 HTTP / SQLite / Process Connector (M6) → PROVEN ⭐
Connector M6 dibangun di canonical path (`execution_runtime/canonical_*.py`), dieksekusi hanya via `RealExecutionHarness`, gate P2-B + verifikasi + audit.
- **HTTP (`canonical_http_connector.py`):** GET nyata ke **2 API eksternal berbeda** — JSONPlaceholder (`/posts/1`, 200, userId 1) + httpbin (`/json`, 200, json non-kosong). Response diverifikasi (kontrak), audit lengkap. Bukti: `docs/engineering/reports/M6-001_*`. Commit `6f1ffed` (9/9 test).
- **SQLite DB (`canonical_db_connector.py`):** SQL genuine—`SELECT` users/posts real (3 baris Aster/Zara/VanM), `LIMIT`. Tidak ada mock; db file nyata. Audit. Commit `a15e18e` (10/10 test).
- **Process (`canonical_process_connector.py`):** subprocess NYATA via allowlist read-only (`hostname`→VM, `python --version`→Python), exit 0, stdout diverifikasi, audit. Commit `5d4d507` (7/7 test).
- **Status: PROVEN** — real external effect + verification + audit + repeatable (masing-masing).

### 2.11 Email / Browser Connector (M6) → PARTIAL (bukan PROVEN)
Kedua connector mengikuti definisi kita: **tanpa real external effect penuh → PARTIAL, bukan PROVEN** (meski M6 ditandai complete).
- **Email (`canonical_email_connector.py`):** validasi format real (regex), gate SMTP, dry_run = validasi eksplisit (`sent:false`, mode DRY_RUN). **Kirim SMTP NYATA belum terbukti** — tanpa server SMTP lokal + kredensial → BLOCKED, `sent:false`. Commit `41a31dc` (10/10 test). **→ PARTIAL.**
- **Browser (`canonical_browser_connector.py`):** `fetch_url` HTTP nyata read-only (httpbin.org/html, 200, html_len 3739). **Render/browser automation (headless Chromium) belum terbukti** — playwright/selenium belum terinstall → BLOCKED (jujur, tidak diklaim). fetch HTTP ≠ browser automation. Commit `c61deb8` (9/9 test). **→ PARTIAL.**
- **Syarat naik ke PROVEN (pasca-M7):** Email→ real SMTP + real sent message + independent verification; Browser→ real Chromium + real navigation + real interaction + verification.

---

## 6. Mapping ke Rencana Eksekusi (P0 → P13)

| Phase | Target | Status Setelah P11 |
|---|---|---|
| P0 | Truth Ledger + audit | ✅ **Dokumen ini** |
| P1 | Audit source | ✅ Dilakukan |
| P2 | Real Execution Harness | ✅ **PROVEN** — harness + 14 gate (P2-C) |
| P3 | Filesystem real E2E | ✅ **PROVEN** — `real_harness_analyze.py` |
| P6 | Workflow real E2E | ✅ **PROVEN** — `real_harness_workflow.py` |
| P7 | Agent | ✅ **PROVEN** — `real_harness_agent.py` |
| P8 | Investigation | ✅ **PROVEN** — `real_harness_investigation.py` |
| P9 | Recovery | ✅ **PROVEN** — `real_harness_recovery.py` |
| P10 | Learning | ✅ **PROVEN** — `real_harness_learning.py` |
| P11 | Full Mission | ✅ **PROVEN** — `real_harness_mission.py` |
| P4 | Real AI provider (NVIDIA NIM) | ✅ **PROVEN** — HTTP nyata ke Nvidia, model 'minimaxai/minimax-m3' (favorit Van) menjawab 'PROVEN', finish=stop (key valid)
| P5 | Real GitHub tool | ✅ **PROVEN** — HTTP nyata get_repo, respon 200, data asli (token valid)
| P12-P13 | Cert / Production Workspace | 🔜 Setelah P4/P5 ditutup |

---

*Dokumen ini adalah artefak P0. Akan diperbarui setiap ada bukti baru. Berbasis source + scan otomatis, bukan asumsi.*
