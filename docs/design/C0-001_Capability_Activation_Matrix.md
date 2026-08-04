C0-001 — Capability Activation Matrix
Version: v1.0
Owner: 🦋 Zara
Architecture Authority: ✦ Aster
Status: APPROVED
Priority: ⭐⭐⭐⭐⭐
Category: Capability / Product Engineering

Memetakan Capability nyata SAM — yang benar-benar bisa digunakan hari ini dari entry point — bukan Capability yang direncanakan atau tertulis di dokumen.

Konteks Transisi
----------------
Ini adalah dokumen transisi antara Architecture Complete dan Product Engineering.
Prinsip yang ditetapkan ✦ Aster:
- Runtime bukan tujuan; Runtime adalah sarana.
- Engineering berpusat pada Capability.
- Runtime aktif hanya jika dibutuhkan oleh Capability.
- Dormant yang sesuai constitution/roadmap = status valid ("Dormant by Design").
- Jangan membuat consumer buatan.

Authority
---------
MISSION → CONSTITUTION → CITIZEN SPECIFICATION → SPECIFICATION FREEZE → ROADMAP → ADR-000..ADR-007 → E0-001 → O0-001 → Repository

Metodologi
----------
- Capability diderivasi dari implementasi nyata (entry point), bukan roadmap.
- Status berbasis bukti: runtime trace, call graph, startup, registry, execution.
- Tidak ada capability baru; tidak ada runtime baru; tidak ada redesign.
- Merujuk E0-001 (Implementation Blueprint) & O0-001 (Runtime Operationalization) sebagai basis fakta.

Entry Point yang Diperiksa
--------------------------
- Conversation
- CLI
- Desktop
- Web
- REST
- Automation
- Plugin

Kunci pembacaan entry point nyata (dari E0-001 + O0-001):
- CLI: hidup (16 modul cli.*)
- Web (sam web → FastAPI Operations Console): HIDUP
- Desktop (sam.desktop.main.run): hadir
- REST API (sam.api.server): kode ada, launcher BLOCKED (contract mismatch)
- Headless/Console/API host via launcher: BLOCKED

CATATAN TEMUAN PENTING (CLI)
----------------------------
Banyak subcommand CLI yang tampak sebagai "capability" ternyata HANYA mencetak status statis / hardcoded (tidak memanggil capability nyata):
- sam knowledge, sam intelligence, sam metrics, sam explain, sam history, sam task list/show : hanya echo/print (0 import sam.* capability, 0 runtime_call)
- sam runtime : mencetak "Workflow Runtime: RUNNING / Knowledge: READY" HARDCODED (bukan registry live) — MENYESATKAN
- Subcommand yang benar-benar memanggil capability: autonomous (execute/approve), guardian (decision/cycle), events (follow/show), health/status (coordinator), service (Windows service), session (runtime.session)

=====================================================================
PER-RUNTIME... PER-CAPABILITY ANALYSIS
=====================================================================

---------------------------------------------------------------------
CAPABILITY 1 — CLI System Health & Status
---------------------------------------------------------------------
1. Nama Capability: CLI System Status
2. Status: Operational
3. Evidence:
   - sam.cli.status / sam.cli.health meng-import sam.runtime.coordinator (RuntimeCoordinator), sam.dos.loader, sam.mission.loader.
   - Dipanggil via `sam status`, `sam health` di shell.
4. Entry Point: CLI
5. Activation Path:
   CLI (sam status)
   ↓
   RuntimeCoordinator
   ↓
   (state: INITIALIZING/READY/RUNNING dari lifecycle kernel)
6. Runtime Dependency: sam.runtime (kernel) — saja
7. Execution: Read-only
8. Approval: None
9. Audit: NO
10. Provider: None
11. Consumer: User (operator), CLI
12. Minimal Missing Piece: Tidak ada — sudah fungsional. Anchor untuk capability lain.

---------------------------------------------------------------------
CAPABILITY 2 — CLI Autonomous Execution
---------------------------------------------------------------------
1. Nama Capability: Autonomous Action Execution
2. Status: Operational Preview
3. Evidence:
   - sam.cli.autonomous: status/approve/deny/history/execute.
   - sam.autonomous.executor.ActionExecutor.execute(): SafetyPolicy.requires_approval → ApprovalManager.request → _do_execute.
   - Action types: RESTART/RECOVER/RESUME/ISOLATE/ESCALATE.
   - Catatan: beberapa action (mis. _restart) memakai asyncio.sleep simulasi → bukan eksekusi penuh.
4. Entry Point: CLI (sam autonomous)
5. Activation Path:
   CLI (sam autonomous execute)
   ↓
   ActionExecutor.execute
   ↓
   SafetyPolicy.requires_approval
   ↓
   ApprovalManager.request (gate)
   ↓
   _execute_action (RESTART/RECOVER/RESUME/ISOLATE/ESCALATE)
6. Runtime Dependency: sam.runtime (coordinator), sam.autonomous (policies/isolation/recovery)
7. Execution: Execute (dengan approval gate; sebagian action simulasi)
8. Approval: Required
9. Audit: NO (belum menghasilkan audit record terpisah; hanya log)
10. Provider: None (action execution internal/simulasi)
11. Consumer: User, Automation (via approve/deny flow)
12. Minimal Missing Piece: Ganti action yang masih simulasi (restart/recover/resume) dengan eksekusi nyata, ATAU tandai eksplisit sebagai preview di status.

---------------------------------------------------------------------
CAPABILITY 3 — Guardian Decision & Cycle
---------------------------------------------------------------------
1. Nama Capability: Guardian Decision
2. Status: Operational Preview
3. Evidence:
   - sam.cli.guardian: decision/cycle.
   - Import sam.guardian.decision, sam.guardian.pipeline, sam.contracts, sam.runtime.coordinator.
   - Pipeline decision nyata (bukan print).
4. Entry Point: CLI (sam guardian)
5. Activation Path:
   CLI (sam guardian decision)
   ↓
   sam.guardian.pipeline
   ↓
   sam.contracts (decision model)
   ↓
   sam.runtime.coordinator
6. Runtime Dependency: sam.runtime (coordinator), sam.guardian (decision contract)
7. Execution: Read-only / Evaluate
8. Approval: Optional (guardian = pengaman, bukan eksekutor)
9. Audit: NO
10. Provider: None
11. Consumer: User, Automation (guardian gate sebelum eksekusi)
12. Minimal Missing Piece: Wire guardian decision sebagai prasyarat (pre-check) di ActionExecutor.execute sehingga eksekusi autonomous lewat guardian terlebih dahulu.

---------------------------------------------------------------------
CAPABILITY 4 — Web Operations Console
---------------------------------------------------------------------
1. Nama Capability: Web Operations Console (SAM Dashboard)
2. Status: Operational
3. Evidence:
   - sam.web.server: FastAPI app dengan routes /, /runtime, /workflow, /incidents, /autonomous, /openclaw, /knowledge.
   - IncidentDetector ter-instansiasi di startup web.
   - Di-launch via `sam web` (run_server ada, host/port default 127.0.0.1:8080).
4. Entry Point: Web
5. Activation Path:
   CLI (sam web)
   ↓
   sam.web.server.run_server
   ↓
   FastAPI app (SAM Operations Console)
   ↓
   routes (runtime/workflow/incidents/autonomous/openclaw/knowledge)
   ↓
   RuntimeCoordinator
6. Runtime Dependency: sam.runtime (coordinator/workspace), sam.operations (IncidentDetector)
7. Execution: Read-only (dashboard/observability)
8. Approval: None
9. Audit: NO
10. Provider: None
11. Consumer: User (operator/console), Dashboard
12. Minimal Missing Piece: Tidak ada untuk dashboard inti. Opsional: expose endpoint yang memanggil capability eksekusi (preview) — tapi itu capability terpisah, di luar inti konsole.

---------------------------------------------------------------------
CAPABILITY 5 — REST API
---------------------------------------------------------------------
1. Nama Capability: REST API (Health/Runtime/Events/Metrics)
2. Status: Stub / Operational Preview (kode siap, launch BLOCKED)
3. Evidence:
   - sam.api.server: FastAPI app, routers health/runtime/events/metrics.
   - DARI E0-001: host API via launcher BLOCKED oleh contract mismatch ("'TelemetryService' object has no attribute 'start'"); def run() tidak ada di sam/api/server.py.
4. Entry Point: REST
5. Activation Path:
   REST (FastAPI)
   ↓
   sam.api.server app
   ↓
   routers: /health, /runtime, /events, /metrics
   - TAPI: No Activation Path dari HostLauncher (blocked)
6. Runtime Dependency: sam.runtime (health/events/metrics collector)
7. Execution: Read-only (jika di-launch)
8. Approval: None
9. Audit: NO
10. Provider: None
11. Consumer: External client, Automation (jika di-launch)
12. Minimal Missing Piece: Tambahkan def run() pada sam.api.server ATAU perbaiki contract TelemetryService.start() sehingga HostLauncher dapat men-launch API (lihat E0-01 Issue Register). TANPA ini, capability tidak bisa diaktifkan.

---------------------------------------------------------------------
CAPABILITY 6 — Desktop Runtime
---------------------------------------------------------------------
1. Nama Capability: Desktop Application
2. Status: Operational Preview
3. Evidence:
   - sam.desktop.main.run tersedia; Desktop adalah salah satu host aktif (E0-001).
4. Entry Point: Desktop
5. Activation Path:
   Desktop launch
   ↓
   sam.desktop.main.run
   ↓
   (UI shell; RuntimeCoordinator)
6. Runtime Dependency: sam.runtime (coordinator)
7. Execution: Read-only / UI preview
8. Approval: None
9. Audit: NO
10. Provider: None
11. Consumer: User (desktop operator)
12. Minimal Missing Piece: Verifikasi scope UI Desktop (dashboard/console) dan wire capability apa yang diekspos dari shell; tanpa verifikasi, klasifikasi Preview.

---------------------------------------------------------------------
CAPABILITY 7 — Conversation Execution & Dispatcher
---------------------------------------------------------------------
1. Nama Capability: Conversation/Dispatcher Execution
2. Status: Dormant (stack lengkap, belum di-wire ke entry)
3. Evidence:
   - sam.execution.dispatch.* lengkap: ConversationDispatchBridge (queue/detail/preview/audit/validation/readiness/history/statistics/connector/approval), DashboardDispatchBuilder, IntegrationDispatch, DispatchAudit, DispatchQueue, DispatchValidator.
   - Konsumen: execution/adapters (conversation_adapter, execution_envelope, integration_adapter), execution/providers (conversation_provider).
   - DARI O0-001: ConversationExecutionPipeline TIDAK di-wire ke HostLauncher/entry (tidak ter-import di startup trace).
4. Entry Point: Conversation (belum ada entry live)
5. Activation Path:
   No Activation Path (pipeline belum ter-wire ke entry/launcher)
   - Potensi (saat di-wire): Conversation API → RuntimeService → ConversationExecutionPipeline → ExecutionSandbox
6. Runtime Dependency: sam.execution (dispatch/adapters/providers), sam.runtime (context)
7. Execution: Preview (potensial; sandbox) — saat ini None
8. Approval: Required (approval gate pada sandbox; _require_execution_approval)
9. Audit: YES (potensial) — DispatchAudit/DispatchAuditEntry tersedia
10. Provider: sam.execution.providers (conversation_provider) — tersedia
11. Consumer: User (conversation), Automation (jadwal) — belum terhubung
12. Minimal Missing Piece: Wire ConversationDispatchBridge ke salah satu entry live (mis. route /conversation di sam.web ATAU subcommand sam conversation) dalam mode preview/sandbox; gunakan DispatchAudit untuk aktivasi audit.

---------------------------------------------------------------------
CAPABILITY 8 — CLI Presentation (Knowledge/Memory/Workflow/Task/Intelligence)
---------------------------------------------------------------------
1. Nama Capability: CLI Domain Display (Knowledge/Memory/Workflow/Task/Intelligence/Metrics)
2. Status: Dormant (hardcoded display, tidak memanggil capability nyata)
3. Evidence:
   - sam.cli.knowledge (31 echo, 0 runtime_call), sam.cli.intelligence (34 echo), sam.cli.metrics (8 echo), sam.cli.explain (21 echo), sam.cli.history (12 echo), sam.cli.task (17 echo), sam.cli.memory stats, sam.cli.plugins list/status, sam.cli.workflow list/status.
   - sam.cli.runtime mencetak status HARDCODED (RUNNING/READY) tanpa query registry live.
4. Entry Point: CLI
5. Activation Path:
   - CLI → print statis (tidak menuju runtime capability apa pun)
   - No real activation; hanya menampilkan teks.
6. Runtime Dependency: NONE (hanya runtime.coordinator untuk wrapper; isi hardcoded)
7. Execution: None (hanya display)
8. Approval: None
9. Audit: NO
10. Provider: None
11. Consumer: User (informasi), tapi data tidak real
12. Minimal Missing Piece: Hentikan klaim tidak nyata — perbaiki display agar query registry live ATAU tandai sebagai "preview/placeholder". (Ini perbaikan kecil interface, bukan redesign.)

---------------------------------------------------------------------
CAPABILITY 9 — Events & Telemetry Stream
---------------------------------------------------------------------
1. Nama Capability: Events Follow (telemetry/event stream)
2. Status: Operational Preview
3. Evidence:
   - sam.cli.events: follow/show; import sam.runtime.coordinator.
   - Runtime kernel memancarkan event (startup.initiating, startup.complete, runtime.started, dsb — dari RuntimeCoordinator).
4. Entry Point: CLI
5. Activation Path:
   CLI (sam events follow)
   ↓
   sam.runtime.coordinator (lifecycle events)
   ↓
   (event payload stream)
6. Runtime Dependency: sam.runtime (coordinator)
7. Execution: Read-only (streaming)
8. Approval: None
9. Audit: NO
10. Provider: None
11. Consumer: User, Monitor/Dashboard
12. Minimal Missing Piece: Tidak ada untuk stream dasar. (Opsional: hubungkan ke DispatchAudit bila perlu tap audit.)

---------------------------------------------------------------------
CAPABILITY 10 — Service Management (Windows)
---------------------------------------------------------------------
1. Nama Capability: SAM Runtime Service (Windows daemon)
2. Status: Operational
3. Evidence:
   - sam.service.manager: install/start/stop/status via win32serviceutil (SAMRuntime service).
   - sam.cli.service: 4 subcommand (install/start/stop/status).
4. Entry Point: CLI (sam service)
5. Activation Path:
   CLI (sam service start)
   ↓
   sam.service.manager (win32serviceutil)
   ↓
   SAMRuntime Windows service
6. Runtime Dependency: sam.service.manager (wrapper Windows); sam.runtime sebagai payload saat service berjalan
7. Execution: Execute (service kontrol)
8. Approval: None (OS-level service)
9. Audit: NO
10. Provider: None
11. Consumer: OS/Administrator, Automation (daemon)
12. Minimal Missing Piece: Verifikasi payload yang dijalankan service benar-benar menjalankan RuntimeCoordinator penuh (bukan shell kosong).

=====================================================================
CONSOLIDATED MATRIX
=====================================================================
| # | Capability | Entry | Runtime Dep | Execution | Approval | Audit | Provider | Status |
|---|------------|-------|-------------|-----------|----------|-------|----------|--------|
| 1 | CLI System Status | CLI | sam.runtime | Read-only | None | NO | None | Operational |
| 2 | Autonomous Execution | CLI | sam.runtime, sam.autonomous | Execute (part-simulasi) | Required | NO | None | Operational Preview |
| 3 | Guardian Decision | CLI | sam.runtime, sam.guardian | Evaluate | Optional | NO | None | Operational Preview |
| 4 | Web Operations Console | Web | sam.runtime, sam.operations | Read-only | None | NO | None | Operational |
| 5 | REST API | REST | sam.runtime | Read-only | None | NO | None | Stub (launch blocked) |
| 6 | Desktop Application | Desktop | sam.runtime | Read-only | None | NO | None | Operational Preview |
| 7 | Conversation/Dispatcher | Conversation | sam.execution, sam.runtime | None (preview potensial) | Required | YES (tersedia) | exec.providers | Dormant |
| 8 | CLI Domain Display (K/M/W/T/I) | CLI | NONE | None | None | NO | None | Dormant (hardcoded) |
| 9 | Events Follow | CLI | sam.runtime | Read-only | None | NO | None | Operational Preview |
| 10 | Service Management (Win) | CLI | sam.service.manager | Execute (service) | None | NO | None | Operational |

=====================================================================
CAPABILITY HEAT MAP
=====================================================================
Production (siap dipakai hari ini):
- CLI System Status (#1)
- Web Operations Console (#4)
- Service Management (#10)

Preview (fungsional tapi belum penuh / masih simulasi / belum di-launch):
- Autonomous Execution (#2) — approval live, action sebagian simulasi
- Guardian Decision (#3)
- Desktop Application (#6)
- Events Follow (#9)

Dormant (stack ada, tapi belum di-wire ke entry / hanya display hardcoded):
- Conversation/Dispatcher (#7)
- CLI Domain Display (#8)

Legacy: (tidak ada)

=====================================================================
DEPENDENCY GRAPH (dibalik — jalur yang dipakai, Capability → Runtime)
=====================================================================
Sesuai arah yang diinginkan Aster (Capability → RuntimeService → Runtime → Execution → Provider),

Capability
  ↓ (entries)
1. CLI System Status ─────────► sam.runtime ──► (state kernel)
2. Autonomous Execution ─────► sam.runtime → sam.autonomous (executor/approval) → [Execution action] → (simulasi)
3. Guardian Decision ────────► sam.runtime → sam.guardian (pipeline/contracts) → Evaluate
4. Web Operations Console ───► sam.runtime → sam.operations (IncidentDetector) → Read
5. REST API ────────────────► sam.runtime → (health/events/metrics) — BLOCKED launch
6. Desktop ─────────────────► sam.runtime → (UI shell) → Read
7. Conversation/Dispatcher ─► sam.runtime → sam.execution (dispatch/adapters/providers) → ExecutionSandbox → exec.providers — DORMANT
8. CLI Domain Display ──────► (none) — hanya teks
9. Events Follow ───────────► sam.runtime (coordinator events) → Read
10. Service Management ─────► sam.service.manager → SAMRuntime service → (runtime payload)

Graph terbalik (yang ingin dipakai Program F):
Capability
  ↓
RuntimeService
  ↓
Runtime (sam.runtime kernel / sam.execution)
  ↓
Execution
  ↓
Provider
Khusus C0-001: hanya rute dengan Capability yang benar-benar hidup relevan. Mayoritas capability masih berhenti di "Runtime kernel / Read" — belum sampai Execution dan Provider, karena belum ada consumer nyata yang menuntut eksekusi.

=====================================================================
PRODUCT VALUE RANKING
=====================================================================
Urutan Capability berdasar nilai produk (bukan runtime):
1. Conversation/Dispatcher (#7) — terbesar (inti interaksi/otomasi), tapi DORMANT → perlu wiring
2. Web Operations Console (#4) — Operational, nilai observability tinggi
3. Autonomous Execution (#2) — nilai otomasi, operational preview
4. Knowledge (#8 bagian) — nilai domain, tapi hanya display (dormant) 
5. Workflow (#8 bagian) — nilai proses, hanya display
6. Memory (#8 bagian) — nilai konteks, hanya display
7. Guardian Decision (#3) — nilai keamanan gate
8. CLI System Status (#1) — dasar
9. Events Follow (#9) — telemetri
10. REST API (#5) — akses eksternal, blocked
11. Desktop (#6) — UX, preview
12. Service Management (#10) — infra

=====================================================================
ACCEPTANCE CRITERIA
=====================================================================
- [x] Semua Capability berasal dari implementasi nyata.
- [x] Tidak ada Capability fiktif (semua berbasis kode/entry yang diverifikasi).
- [x] Tidak ada Runtime baru.
- [x] Tidak ada redesign.
- [x] Semua Capability memiliki activation path yang dapat diverifikasi (yang dormant dicatat "No Activation Path" atau "hanya display").

=====================================================================
CATATAN UNTUK ENGINEERING (transisi)
=====================================================================
1. Jangan operasionalkan runtime satu per satu. Operasionalkan Capability.
2. Kandidat pertama yang paling masuk akal untuk "dihidupkan" (wiring, bukan redesign):
   a. Conversation/Dispatcher (#7): wire ConversationDispatchBridge ke route /conversation (web) ATAU subcommand sam conversation, mode preview/sandbox, gunakan DispatchAudit. — MENGHIDUPKAN runtime sam.execution SECARA CAPABILITY-DRIVEN.
   b. REST API (#5): tambah def run() / fix TelemetryService contract → huruf "activate capability" REST.
   c. Perbaiki CLI Domain Display (#8): ganti hardcoded jadi query registry live (kecil, bukan redesign), agar klaim status jujur.
3. Capability yang tetap dormant (tanpa consumer nyata) = Dormant by Design — valid.
4. Setiap keputusan "runtime ikut aktif" harus berasal dari kebutuhan Capability, bukan inisiatif runtime.

=====================================================================
OUTPUT
=====================================================================
- File: docs/design/C0-001_Capability_Activation_Matrix.md (ini)

=====================================================================
REFERENSI
=====================================================================
- E0-001 Implementation Blueprint (docs/design/E0-001_Implementation_Blueprint.md)
- O0-001 Runtime Operationalization Strategy (docs/design/O0-001_Runtime_Operationalization_Strategy.md)
- MISSION / CONSTITUTION / CITIZEN SPECIFICATION / ADR / ROADMAP
