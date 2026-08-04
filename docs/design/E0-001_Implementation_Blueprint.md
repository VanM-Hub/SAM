# E0-001 — Implementation Blueprint

**Judul:** E0-001 — Implementation Blueprint *(Observed Reality)*
**Jenis:** Laporan Audit Implementasi — READ-ONLY (tidak mengubah repo)
**STATUS OTORITAS: Implementation Blueprint (Observed Reality)** — dokumen observasional, BUKAN Architecture Authority
**Sumber Otoritas:** Kode + runtime nyata di `src/sam/`, `pyproject.toml`
**Konteks:** Misi E0-001 (✦ Aster) — dokumentasikan implementasi LANGSUNG yang hidup, bukan dokumentasi
**Tanggal:** 2026-08-04
**Status:** Selesai — 15/15 audit

---

## 1. Ringkasan Eksekutif

Repository SAM berisi **~2532 modul Python** di `src/sam/`. Namun **implementasi yang benar-benar AKTIF saat runtime jauh lebih kecil** — hanya `sam.launcher.*`, `sam.runtime.*`, `sam.cli.*`, dan sebagian `sam.operations.*` yang ter-import saat startup resmi.

**Empat temuan arsitektural terpenting:**

| # | Temuan | Severity | Bukti |
|---|--------|----------|-------|
| 1 | **Sebagian besar "runtime" adalah kerangka replikasi, bukan runtime aktif.** ~13 package `*_runtime` (intelligence, artifact, audit, cognitive, knowledge, memory, mission, policy, skills, workflow, model_runtime) punya skeleton identik (builder/catalog/certification/dashboard/foundation/integration/model/monitoring/runtime) + Bridge, tapi **tidak pernah ter-import saat startup** | **HIGH** | Runtime trace: pipeline=18 modul, cli=16, headless=8 — tak satupun `*_runtime` |
| 2 | **HostLauncher punya kontrak yang tidak cocok dengan implementasi host.** Dari 4 host (console/api/headless/desktop), hanya DESKTOP yang bisa hidup lewat launcher. Console & API tak punya `run()` module-level yang dicari launcher; Headless error karena `TelemetryService` tidak punya `start()` | **HIGH** | Reproduksi error langsung: `'TelemetryService' object has no attribute 'start'` |
| 3 | **Konteks "runtime" tertukar dua makna.** `sam.runtime` (Runtime Kernel: coordinator/session/bootstrap/shutdown — HIDUP) vs `sam.execution.runtime` (Execution Runtime: registry/builder/validator — layer execution) vs ~11 package `*_runtime` (DORMANT) | **MEDIUM** | 3 jalur berbeda dengan nama serupa |
| 4 | **Model_runtime sepenuhnya terisolasi** (in-dep=0) — 89 file yang tidak pernah di-referensikan modul lain | **HIGH** | Complexity scan: model_runtime in-dep 0 |

**Yang HIDUP hari ini (runtime trace real):**

```
Entry (sam / sam-console / sam-desktop / sam-headless / sam-diagnostic)
  → sam.launcher.cli_entry.*_main
     → sam.launcher.StartupPipeline (18 modul launcher di-import)
        → sam.runtime.* (RuntimeCoordinator, SessionManager, BootstrapManager, ...)   [HIDUP]
        → HostLauncher.launch(HostType)
           ├─ CONSOLE  → sam.operations.presentation.console.app  → GAGAL (tak ada run())
           ├─ DESKTOP  → sam.desktop.main.run                      → HIDUP ✅
           ├─ HEADLESS → sam.telemetry.service + operations.health → GAGAL (tak ada start())
           └─ API      → sam.api.server                            → GAGAL (tak ada run())
  → sam.cli.main (Typer)  → 20 subcommand (status/health/session/runtime/...)  → HIDUP ✅
     → sam.web.server.run_server ('sam web')                                     → HIDUP ✅
```

---

## 2. Posisi dalam Hirarki Otoritas (klarifikasi status)

E0-001 adalah dokumen **observasional** — mencatat *apa yang benar-benar hidup* pada implementasi hari ini, **bukan** *bagaimana SAM seharusnya dirancang*.

> **STATUS: Implementation Blueprint (Observed Reality)** — BUKAN Architecture Authority.
> Tidak membuat aturan baru, tidak menjadi sumber kebenaran desain, dan tidak mengganggu hierarki L0/L1/L2.

Posisi E0-001 dalam hierarki:

```
MISSION
  ↓
CONSTITUTION
  ↓
SPECIFICATION
  ↓
ADR
  ↓
SAM_ARCHITECTURE
  ↓
Reference Runtime
  ↓
▶ E0-001 Implementation Blueprint (Observed Reality)   ← DI SINI
  ↓
SOURCE CODE
```

E0-001 menjembatani arsitektur dengan implementasi aktual. Pembaca boleh menggunakannya untuk **memahami keadaan aktual** (mana yang hidup/dormant/stub, apa kontrak yang cocok/tidak cocok), tetapi **tidak boleh** mengangkat isinya menjadi aturan arsitektur baru. Jika ada konflik antara E0-001 dan hierarki otoritas di atasnya, maka hierarki di atasnya yang menang.

---

## 3. Kelayakan & Metodologi

- **Sumber kebenaran:** `src/sam/` (kode), `pyproject.toml` (entry), runtime import trace.
- **Metode:** (a) static AST/import scan utk struktur & ukuran, (b) **runtime import trace** (patch `builtins.__import__`) utk bukti hidup hari ini, (c) reproduksi eksekusi HostLauncher utk status host.
- **Batasan:** import trace menangkap modul yang di-import; subclass/objek lifecycle yang dibuat via string/dynamic registry bisa terlewat. Verifikasi manual dilakukan untuk temuan kritis (host, telemetry, provider).
- **Naming** mengikuti MISSION/Constitution/Governance; tidak mengusulkan perubahan (READ-ONLY).

---

## 4. AUDIT 1 — Runtime Dependency Graph (flow implementasi)

Graf dependensi runtime (dari bukti import trace + struktur launcher):

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRY POINTS (pyproject) — semua → launcher.cli_entry       │
│  sam, sam-console, sam-desktop, sam-headless, sam-diagnostic │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
                 sam.launcher.cli_entry (5 × *_main)
                               ▼
                sam.launcher.StartupPipeline
                ├───────────────────────────────┐
                ▼                               ▼
   sam.runtime (KERNEL)              sam.launcher.HostLauncher
   RuntimeCoordinator                ├── Console→console.app  (✗)
   SessionManager                    ├── Desktop→desktop.main (✓)
   BootstrapManager                  ├── Headless→telemetry  (✗)
   ShutdownManager                   └── API→api.server      (✗)
   RecoveryManager
                │
                ▼
   sam.cli.main (20 subcommand) ───► sam.web.server.run_server
                │
                ▼
   sam.operations (brain, execution pipeline)
                │
                ▼
   sam.execution.runtime (ExecutionRuntime → ConversationExecution)
                │
                ▼
   Operations sandbox executors
   (Filesystem/Command/Process/Workspace, via ExecutionSandbox)
```

**Graf ini DIVERIFIKASI saat runtime:** pipeline meng-import `sam.launcher.*` (13) + `sam.operations.brain` (6); CLI meng-import `sam.runtime.coordinator/session`, `sam.mission.loader`, `sam.contracts`, `sam.dos.loader`, `sam.guardian.pipeline/decision`, `sam.service.manager`, `sam.operations.brain`.

---

## 5. AUDIT 2 — Capability Matrix (status implementasi per runtime)

| Runtime / Package | File | Class | Status Implementasi (bukti runtime) |
|---|---|---|---|
| **sam.runtime** (Kernel) | 169 | 178 | **HIDUP** — coordinator/session/bootstrap/shutdown di-import CLI |
| **sam.execution** | 104 | 323 | **HIDUP** — ConversationExecution reachable via runtime |
| **sam.launcher** | ~14 | — | **HIDUP** — semua entry point |
| **sam.cli** | ~7 | — | **HIDUP** — 20 subcommand |
| **sam.operations** | 350 | 1036 | **SEBAGIAN HIDUP** — brain & execution pipeline aktif; sisanya besar dormant |
| **sam.guardian** | 77 | 189 | **SEBAGIAN** — pipeline/decision dipakai CLI; in-dep rendah |
| **sam.providers** | 125 | 169 | **DORMANT** — tak ada provider nyata (docker/filesystem/llm) ter-import di startup |
| **sam.connectors** | 77 | 116 | **DORMANT** — in-dep 22 tapi tak ter-import di startup |
| **sam.model_runtime** | 89 | 145 | **DORMANT TOTAL** — in-dep 0 |
| **sam.artifact_runtime** | 66 | 90 | **DORMANT** — in-dep 9, tak ter-import |
| **sam.intelligence_runtime** | 41 | 45 | **DORMANT** — in-dep 1 |
| **sam.cognitive_runtime** | 65 | 87 | **DORMANT** — in-dep 9 |
| **sam.knowledge_runtime** | 67 | 90 | **DORMANT** — in-dep 10 |
| **sam.memory** | 67 | 92 | **DORMANT** — in-dep 10 |
| **sam.mission_runtime** | 70 | 93 | **DORMANT** — in-dep 1 |
| **sam.policy_runtime** | 66 | 89 | **DORMANT** — in-dep 9 |
| **sam.skills** | 67 | 92 | **DORMANT** — in-dep 10 |
| **sam.workflow_runtime** | 66 | 89 | **DORMANT** — in-dep 9 |
| **sam.runtime_root** | 10 | 14 | **MINIMAL** — in-dep 1, kerangka composition |
| **sam.runtime_kernel** | 69 | 124 | **PARALEL** — anggota ketiga keluarga "runtime", in-dep 57 |
| **sam.runtime_service** | 61 | 64 | **STUB** — ConversationRuntimeService & co. hanya konstruktor |
| **sam.presentation** | 51 | 41 | **TIPIS** — koordinator + certifier |
| **sam.compliance** | 86 | 117 | **MANDIRI** — enginedan check framework, in-dep 19 |

---

## 6. AUDIT 3 — Public API Surface (kelas publik per package)

**Hotspot public API (class + dataclass):**

| Package | Class | Dataclass | Total |
|---|---|---|---|
| sam.operations | 1036 | 642 | 1678 |
| sam.execution | 323 | 207 | 530 |
| sam.runtime | 178 | 24 | 202 |
| sam.guardian | 189 | 102 | 291 |
| sam.providers | 169 | 99 | 268 |
| sam.model_runtime | 145 | 92 | 237 |
| sam.compliance | 117 | 18 | 135 |
| sam.connectors | 116 | 58 | 174 |
| sam.runtime_kernel | 124 | 55 | 179 |
| sam.agent | 86 | 48 | 134 |

**Pola dominan di API:** hampir semua package expos kelas `*Builder`, `*Registry`, `*Manager`, `*Service`, `*Runtime`, `*Bridge`, `*HealthService`, `*Lifecycle`, `*State`, `*Validator`. Ini menunjukkan **template/foundation yang direplikasi hampir identik di berpuluh package** (lihat Audit 9).

**Contoh kelas publik nyata (dari `sam.runtime` — yang HIDUP):**
`RuntimeState, RuntimeCoordinator, BootstrapManager, SessionManager, ShutdownManager, RecoveryManager` (dari `__init__.py`).

**Contoh isi kernel `sam.runtime_root`:** `RuntimeBuilder, RuntimeContainer, RuntimeRoot, RuntimeLifecycle, RuntimeHealth, RuntimeState, HealthProvider, HealthStatus, UnitFactory, UnitRegistry`.

---

## 7. AUDIT 4 — Runtime Lifecycle (siapa membuat / meng-init / menghentikan)

| Lifecycle | Pemilik | Bukti |
|---|---|---|
| Bootstrap | `sam.runtime.BootstrapManager` | Live; dipakai CLI |
| Session | `sam.runtime.SessionManager` | Live; dipakai CLI (`sam.runtime.session`) |
| Coordinator | `sam.runtime.RuntimeCoordinator` | Live; `sam.runtime.coordinator` ter-import di CLI |
| Shutdown | `sam.runtime.ShutdownManager` | Live |
| Recovery | `sam.runtime.RecoveryManager` | Live |
| Host launch | `sam.launcher.HostLauncher` + `HostManager` | Live (impor); tapi 3/4 host gagal eksekusi |
| Host start/stop | `HostLauncher` panggil `host.start()/stop()` | **MISMATCH** — TelemetryService tak punya `start()` |
| Execution init | `sam.execution.runtime.ExecutionRuntime.__init__` | Live; bangun registry/builder/validator/rules/constraints/readiness |
| Execution run | `ExecutionRuntime.run(ctx, req)` → `ExecutionDraft` | Live; via ConversationExecution |
| Provider/service lifecycle | `sam.provider` `SamProviderManager`? — via `sam.service.manager` | Service manager live di CLI |

**Temuan lifecycle (READ-ONLY):** tidak ada lifecycle owner tunggal yang meng-aktifkan package `*_runtime` yang dormant; masing-masing punya `*_lifecycle.py` sendiri yang tidak ter-panggil dari flow hidup.

---

## 8. AUDIT 5 — Singleton Map

Singleton/registry bernama (dari scan seluruh src/sam/):

| Nama | Kemunculan | Package tersebar | Status |
|---|---|---|---|
| `RuntimeRegistry` | 5 | launcher, runtime | **PENTING** — daftar 7 runtime, tapi kosong by default |
| `HealthService` | 7 | multi-runtime | DORMANT (di `*_runtime`) |
| `RuntimeCoordinator` | 4 | runtime | HIDUP |
| `ProviderRegistry` | 3 | providers, runtime | DORMANT |
| `PluginRegistry` | 3 | runtime_kernel, plugin | DORMANT |
| `RuntimeManifest` | 3 | — | DORMANT |
| `ServiceManager` | 2 | core/service, cli `sam.service.manager` | **HIDUP** (CLI) |
| `ConnectorRegistry` / `ConnectorRuntime` | 2+2 | connectors | DORMANT |
| `MissionRegistry` / `MissionBuilder` | 2+2 | mission_runtime | DORMANT |
| `SessionRegistry` | 2 | — | HIDUP (via session) |
| `ExecutionRegistry` / `ExecutionBuilder` | 2+2 | execution | **HIDUP** |
| `AgentRegistry` | 2 | agent | DORMANT |

**Kunci:** `RuntimeRegistry` yang diisi saat pipeline stage berisi 7 runtime (Guardian, Reasoning, Decision, Conversation, Console, Desktop, Headless), namun di runtime nyata registry ini `empty` by default — hanya terisi selama stage pipeline, dan hanya beberapa yang benar-benar mendapat implementasi hidup.

---

## 9. AUDIT 6 — Service Locator

| Pola | Total kemunculan | Severity |
|---|---|---|
| `registry.get(...)` | 51× | **HIGH** |
| `runtime.current(...)` | 6× | Medium |
| `manager.get(...)` | 2× | Low |

**Paket dengan locator terbanyak:** `dependency` (7), `live` (6), `connector_locator` (5), `runtime` (3), `routing` (3), `container` (3), `monitor` (2), `protocol` (2), `conversation_state` (2).

**Makna:** SAM bergantung berat pada **service-locator / dynamic registry lookup** — ini menjelaskan kenapa static-import analysis (Audit 8) menunjukkan banyak modul "orphaned": mereka di-lookup via string/nama saat runtime, bukan di-import statis. **Peringatan metodologi:** hasil dormant harus digabung dengan bukti runtime trace dan verifikasi manual, bukan hanya dari import statis.

---

## 10. AUDIT 7 — Circular Dependency

**HASIL: 0 (ZERO) module-level circular import terdeteksi.**

- Menggunakan algoritma Tarjan SCC pada directed graph import seluruh `src/sam/` (~2532 node).
- Tidak ada SCC berukuran >1 → **tidak ada cycle antar module** (pada level import).
- Catatan: audit ini import-level; cycle di level object/instance (lewat service locator) tidak ter-capture dan perlu pemeriksaan lanjutan bila relevan.

**Verdict: POSITIF** — struktur import acyclic.

---

## 11. AUDIT 8 — Dead Runtime (Dormant)

**Definisi:** package yang (a) tidak ter-import saat startup resmi, DAN (b) in-dep sangat rendah (jarang/tidak pernah di-referensikan modul luar).

**Matrix dead/dormant runtime:**

| Package | File | in-dep | Ter-import saat startup? | Verdict |
|---|---|---|---|---|
| sam.model_runtime | 89 | **0** | Tidak | **DORMANT TOTAL** |
| sam.intelligence_runtime | 41 | 1 | Tidak | DORMANT |
| sam.mission_runtime | 70 | 1 | Tidak | DORMANT |
| sam.guardian | 77 | 2 | Tidak (pipeline/decision saja via CLI) | SEBAGIAN |
| sam.orchestrator | 78 | 1 | Tidak | DORMANT |
| sam.runtime_root | 10 | 1 | Tidak | DORMANT/MINIMAL |
| sam.runtime_service | 61 | 5 | Tidak | **STUB** |
| sam.artifact_runtime | 66 | 9 | Tidak | DORMANT |
| sam.audit_runtime | 66 | 9 | Tidak | DORMANT |
| sam.cognitive_runtime | 65 | 9 | Tidak | DORMANT |
| sam.policy_runtime | 66 | 9 | Tidak | DORMANT |
| sam.workflow_runtime | 66 | 9 | Tidak | DORMANT |
| sam.knowledge_runtime | 67 | 10 | Tidak | DORMANT |
| sam.memory | 67 | 10 | Tidak | DORMANT |
| sam.skills | 67 | 10 | Tidak | DORMANT |
| sam.providers (nyata) | 125 | 27 | Tidak (semua provider konkret orphaned) | DORMANT |
| sam.connectors | 77 | 22 | Tidak | DORMANT |
| sam.agent | 67 | 10 | Tidak | DORMANT |
| sam.execution | 104 | 65 | Ya (via runtime) | **HIDUP** |
| sam.runtime | 169 | 50 | Ya (via CLI) | **HIDUP** |

**Angka "orphaned module" (tidak di-import modul sam lain, per top folder):**
brain 161/172, runtime 81/128, certification 79/79, foundation 78/78, presentation 71/71, integration 68/68, live 68/68, builder 65/65, catalog 57/60, model 50/50, monitor 41/41, monitoring 40/40, docker 10/10, llm 10/10, filesystem 8/8, shell 8/8, sqlite 8/8.

---

## 12. AUDIT 9 — Duplicate Responsibility

**Temuan utama: pola "Bridge" & skeleton runtime direplikasi massif.**

Hampir setiap package `*_runtime` (dan `model_runtime`/`*_sdk`) berisi struktur folder yang **identik**:

```
builder/  catalog/  certification/  dashboard/  foundation/  integration/
model/    monitoring/  runtime/
```

serta kelas `*Bridge` (ConversationRuntimeBridge, DashboardRuntimeBridge, dll) yang hampir sama di tiap package.

**Daftar besar Bridge/ds replicated (dari scan):**
- Providers: `ConversationProviderBridge`, `DashboardProviderBridge`, `ConnectorProviderLink`, `ConnectorProviderBridge`
- Bridge routers: `BridgeRouter`, `BridgeRoute` (operations)
- Kelas `*Bridge` di mayoritas package

**Dampak (READ-ONLY):** ~13 package mengulang skeleton + Bridge yang sama → **duplicate responsibility** antara package `*_runtime` yang satu dan lainnya (semua mengaku "runtime" untuk domain berbeda tapi struktur identik), serta duplikasi `*Builder`/`*Registry`/`*HealthService` di banyak tempat. Ini konsisten dengan temuan bahwa sebagian besar tidak terhubung ke entry (Audit 8).

---

## 13. AUDIT 10 — Runtime Complexity

Tabel lengkap (file / class / dataclass / out-dep / in-dep):

| Package | File | Class | Dataclass | Out-dep | In-dep |
|---|---|---|---|---|---|
| operations | 350 | 1036 | 642 | 624 | 33 |
| runtime | 169 | 178 | 24 | 107 | 50 |
| execution | 104 | 323 | 207 | 175 | 65 |
| providers | 125 | 169 | 99 | 240 | 27 |
| model_runtime | 89 | 145 | 92 | 126 | 0 |
| compliance | 86 | 117 | 18 | 198 | 19 |
| orchestrator | 78 | 101 | 56 | 162 | 1 |
| guardian | 77 | 189 | 102 | 250 | 2 |
| connectors | 77 | 116 | 58 | 192 | 22 |
| mission_runtime | 70 | 93 | 52 | 157 | 1 |
| runtime_kernel | 69 | 124 | 55 | 69 | 57 |
| knowledge_runtime | 67 | 90 | 45 | 126 | 10 |
| memory | 67 | 92 | 47 | 124 | 10 |
| agent | 67 | 86 | 48 | 130 | 10 |
| skills | 67 | 92 | 47 | 128 | 10 |
| artifact_runtime | 66 | 90 | 47 | 128 | 9 |
| audit_runtime | 66 | 88 | 46 | 128 | 9 |
| policy_runtime | 66 | 89 | 44 | 137 | 9 |
| workflow_runtime | 66 | 89 | 44 | 137 | 9 |
| cognitive_runtime | 65 | 87 | 43 | 138 | 9 |
| runtime_service | 61 | 64 | 33 | 64 | 5 |
| presentation | 51 | 41 | 31 | 89 | 14 |
| activation | 45 | 72 | 34 | 44 | 32 |
| intelligence_runtime | 41 | 45 | 43 | 43 | 1 |
| runtime_root | 10 | 14 | 0 | 40 | 1 |

**Peringkat kompleksitas:** operations (raksasa) → execution → providers → guardian/model_runtime. **Ketidakseimbangan ekstrim:** `operations` 350 file vs `runtime_root` 10 file; sementara runtime *domain) masing-masing ~66 file dengan in-dep <10.

---

## 14. AUDIT 11 — Runtime Boundary

- **Boundary launcher→host:** `HostLauncher` mengharapkan tiap host punya `run()` module-level (atau `start()`/`stop()` utk service). **Tidak konsisten:** desktop punya `run()`, console/api tidak; telemetry harus `start()` tapi tidak ada.
- **Boundary CLI→subcommand:** `sam.cli.main` mendefinisikan 20 subcommand (status, health, session, runtime, plugins, knowledge, memory, workflow, events, guardian, service, logs, metrics, openclaw, intelligence, autonomous, history, task, settings, explain) — semua route ke fungsi Typer.
- **Boundary execution:** semua executor nyata **di sandbox** (`ExecutionSandbox`, `SandboxOperationType`) dengan approval gate (`_require_execution_approval`). Execution = **preview/simulation**, tidak menyentuh sistem nyata.
- **Boundary service locator:** `sam.service.manager.ServiceManager.get_service()` adalah titik lookup layanan (High service-locator, lihat Audit 6).

---

## 15. AUDIT 12 — Runtime Activation per Entry Mode

Bukti runtime trace (import modul `sam.*` unik saat launch):

| Entry / Mode | Modul sam.* di-import | Package aktif | Status host |
|---|---|---|---|
| **StartupPipeline** | 18 | launcher.* (13) + operations.brain (6) | Berjalan (pipeline) |
| **CLI (`sam` status)** | 16 | cli.main, cli, runtime.coordinator, runtime.session, mission.loader, contracts, dos.loader, guardian.pipeline, guardian.decision, service.manager, operations.brain | **HIDUP** ✅ |
| **Console** | 8 (launcher saja) | host_launcher, host_manager | **GAGAL** — console.app tak ada `run()` |
| **API_SERVER** | 8 (launcher saja) | host_launcher, host_manager | **GAGAL** — api.server tak ada `run()` |
| **Headless** | 8 (launcher saja) | host_launcher, host_manager | **GAGAL** — `TelemetryService.start()` tidak ada |
| **Web** | (via CLI `sam web`) | web.server.run_server | **HIDUP** ✅ |
| **Desktop** | (via launcher) | desktop.main.run | **HIDUP** ✅ (satu-satunya host launcher) |

**Kesimpulan:** Jalur CLI + Web + Desktop berfungsi. **Console, API, Headless HOST tidak berfungsi via launcher** karena mismatch kontrak (Audit 4/13).

---

## 16. AUDIT 13 — Provider Activation

Providers konkret (subclass/nyata) + status aktivasi:

| Provider | File | Ter-import startup? | Status |
|---|---|---|---|
| DockerProvider | docker/docker_provider.py | Tidak | DORMANT |
| FilesystemProvider | filesystem/filesystem_provider.py | Tidak | DORMANT |
| AnthropicProviderConfig | anthropic/ | Tidak | DORMANT (config only) |
| DeepSeekProviderConfig | deepseek/ | Tidak | DORMANT (config only) |
| GeminiProviderConfig | gemini/ | Tidak | DORMANT (config only) |
| OpenAI (config) | openai/ | Tidak | DORMANT (config only) |
| Ollama (config) | ollama/ | Tidak | DORMANT (config only) |
| ProviderExecutor / real_provider_activation | execution/ | Tidak | DORMANT |
| ProviderRegistry / ProviderFactory | interfaces/ | Tidak | DORMANT (kerangka) |
| ConversationProviderBridge / DashboardProviderBridge | conversation/ dashboard/ | Tidak | DORMANT (bridge replikasi) |

**Temuan:** Seluruh provider konkret di `sam.providers` (docker, filesystem, llm, shell, sqlite) **orphaned** di static-import (10/10, 8/8, 10/10, 8/8, 8/8) dan tidak ter-import saat startup → **DORMANT**. Tersedia kerangka (`BaseProvider`, `ProviderRegistry`, `ProviderFactory`) tapi tak teraktivasi di flow hidup.

---

## 17. AUDIT 14 — Connector Activation

Connectors (`sam.connectors`, 77 file, in-dep 22):

- `connector_locator` punya 5 hits service-locator (`registry.get`) — ini jalur lookup.
- Namun **tidak ada connector yang ter-import saat startup** (runtime trace: 0 modul `sam.connectors`).
- `ConnectorRegistry` / `ConnectorRuntime` / `ConnectorManifest` ada sebagai kerangka (2× masing-masing).
- `ConnectorProviderLink` / `ConnectorProviderBridge` (providers/connector_bridge) = jembatan provider-connector, DORMANT.

**Verdict:** **Connectors = DORMANT pada flow startup saat ini.** Tersedia kerangka + locator, tapi tidak diaktifkan oleh entry.

---

## 18. AUDIT 15 — Execution Readiness

| Area | Status | Bukti |
|---|---|---|
| **ConversationExecutionPipeline** (Plan→Policy→Approval→Execute→Verify→Audit) | **SIAP (ready)** | Real di `operations/conversation_execution.py` + wired ke `execution.runtime` |
| **Executors nyata** (Filesystem/Command/Process/Workspace) | **SIAP** | `operations/real_executor.py`, semua via `ExecutionSandbox` |
| **Sandbox** (`ExecutionSandbox`, `SandboxOperationType`) | **SIAP** | Execution ter-isolasi, tidak sentuh sistem nyata |
| **Approval gate** (`ApprovalV2Workflow`, `_require_execution_approval`) | **SIAP** | Blokir eksekusi tanpa approval |
| **VerificationEngine / SimulationEngine / AuditTrail** | **SIAP** | Ada di pipeline |
| **ConversationRuntimeService** (`runtime_service`) | **STUB** | Hanya konstruktor; tidak ada execute/preview |
| **TelemetryService.start()** | **MISSING** | Launcher harap `start()`; class punya `close/emit/query/...` tapi TIDAK `start` → Headless broken |
| **Host run() contract** | **TIDAK KONSISTEN** | Desktop punya, Console/API tidak |

**Execution readiness keseluruhan:** **Execution engine (conversation → sandbox) SIAP dan berfungsi**, tapi **host-level readiness (headless/console/api via launcher) BELUM** karena mismatch kontrak `start()`/`run()`.

---

## 19. Issue Register (E0 — rangkuman)

| ID | Deskripsi | Severity |
|---|---|---|
| E0-01 | ~13 package `*_runtime` + model_runtime adalah kerangka replikasi yang tidak teraktifkan saat startup (DORMANT) | HIGH |
| E0-02 | HostLauncher kontrak tidak cocok: Console & API tak punya `run()`, Headless error `TelemetryService.start()` tidak ada | HIGH |
| E0-03 | `runtime_service` stub (ConversationRuntimeService dll) — belum ada implementasi execute/preview | HIGH |
| E0-04 | `model_runtime` sepenuhnya terisolasi (in-dep 0) | HIGH |
| E0-05 | Semua provider konkret (docker/filesystem/llm/shell/sqlite) DORMANT | MEDIUM |
| E0-06 | Connectors DORMANT pada flow startup | MEDIUM |
| E0-07 | Dua/tiga makna "runtime" (Kernel vs Execution vs pool) tertukar | MEDIUM |
| E0-08 | Duplicate skeleton/Bridge di ~13 package `*_runtime` | MEDIUM |
| E0-09 | `sam --version` → "vunknown" (version detection rusak) | LOW |
| E0-10 | RuntimeRegistry kosong by default (hanya terisi saat pipeline stage) | LOW |

---

## 20. Rekomendasi (READ-ONLY — diserahkan ke Chief Architect)

> Sesuai protokol, Zara menyajikan temuan + severity; keputusan arsitektur di tingkat Aster.

1. **Klassifikasi runtime** (tingkat kematangan implementasi) per package — pisahkan HIDUP (runtime/execution/cli/operations-brain) vs DORMANT vs STUB, agar authority jelas.
2. **Selaraskan kontrak host** dengan implementasi (atau sebaliknya): konsistenkan `run()`/`start()`/`stop()` di launcher vs host/telemetry — ini bug runtime nyata yang membuat 3 dari 4 host tidak bisa hidup.
3. **Audit provider/connector activation** — tentukan apakah wallet provider + connector harus diaktifkan di flow hidup atau ditandai eksplisit sebagai "belum aktif".
4. **Telaah duplikasi skeleton `*_runtime`** — apakah replikasi ini disengaja (foundation) atau perlu dikonsolidasi.
5. **Isi/angkat `runtime_service` stub** bila Conversation runtime service diharapkan jadi API hidup.

---

## 21. Kriteria Penerimaan

- [x] Blueprint didasarkan pada kode `src/sam/` + runtime trace (bukan dokumen)
- [x] Keluaran berbentuk tabel/matrix/graph (minimal narasi)
- [x] 15/15 audit tercakup
- [x] READ-ONLY — tidak ada modifikasi repo
- [x] Disimpan di `docs/design/E0-001_Implementation_Blueprint.md`
- [ ] Menunggu persetujuan Van untuk commit (sesuai aturan audit READ-ONLY)
