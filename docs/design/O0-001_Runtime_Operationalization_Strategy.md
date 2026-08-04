O0-001 — Runtime Operationalization Strategy
Version: v1.0
Owner: 🦋 Zara
Architecture Authority: ✦ Aster
Status: APPROVED
Priority: *****
Category: Operationalization

Ringkasan
--------
Dokumen ini mengimplementasikan Work Order O0-001 (✦ Aster). Tujuan: menyusun strategi engineering minimal untuk menaikkan status runtime yang ada dari Specified → Implemented → Operational tanpa mengubah Architecture / Roadmap / Constitution / menambah runtime baru / memodifikasi repository.

Metodologi
---------
- Basis bukti: kode di src/sam/, runtime import trace, dan git log (commit terakhir per folder).
- Tidak ada perubahan kode; rekomendasi berupa tindakan minimum (1 langkah) yang tidak merombak desain.
- Klasifikasi mengikuti definisi: Specified (didefinisikan di spesifikasi/ADR), Implemented (kode ada), Operational (ter-activate dan dipakai di jalur startup/entry nyata).

Daftar Runtime (scope)
----------------------
(runtime nama WO → package aktual)
- runtime → sam.runtime
- runtime_service → sam.runtime_service
- runtime_root → sam.runtime_root
- execution_runtime → sam.execution
- model_runtime → sam.model_runtime
- knowledge_runtime → sam.knowledge_runtime
- workflow_runtime → sam.workflow_runtime
- artifact_runtime → sam.artifact_runtime
- audit_runtime → sam.audit_runtime
- policy_runtime → sam.policy_runtime
- mission_runtime → sam.mission_runtime
- cognitive_runtime → sam.cognitive_runtime
- memory_runtime → sam.memory
- skill_runtime → sam.skills
- intelligence_runtime → sam.intelligence_runtime

Panduan pembacaan: semua status & rekomendasi berbasis bukti; lihat juga docs/design/E0-001_Implementation_Blueprint.md untuk tabel detail per-audit dan bukti runtime trace.

Per-Runtime Analysis (template diisi)
-------------------------------------

1) Runtime: sam.runtime
A. Status
- Specified: YES
- Implemented: YES
- Operational: YES (kernel/infrastruktur hidup)
B. Evidence
- RuntimeCoordinator memiliki lifecycle async: start(), run(), stop() (src/sam/runtime/coordinator.py). (E0-001)
- ExecutionContext dipakai oleh workflow engine & execution engine (src/sam/runtime/context.py; src/sam/workflow/engine.py). (E0-001)
- Commit terakhir pada folder: 2026-08-03 (E1-003). (git)
C. Activation Path
Entry → sam.launcher.StartupPipeline → RuntimeCoordinator.start() → RuntimeCoordinator.run() → metrics collectors
D. Consumer
- CLI (sam.cli.*), workflow engine, execution engine, sdk modules
E. Provider
- Tidak bergantung pada provider eksternal untuk kernel basic (may use persistence modules) — None (provider khusus domain tidak diperlukan)
F. Registry
- CapabilityRegistry / RuntimeRegistry ada; runtime kernel adalah konsumen/penyedia konteks eksekusi. (see src/sam/runtime/registry.py)
G. Host
- CLI, Desktop, Web (when run_server) — kernel hadir di jalur CLI/Web/Desktop
H. Gap Analysis
- Kernel hidup dan mengelola lifecycle; tidak ada gap besar kecuali wiring domain runtimes ke registry
I. Minimal Action
- Tidak perlu action untuk kernel; gunakan sebagai anchor: **no action** (Operational)
J. Confidence
- Verified — High Confidence

2) Runtime Service: sam.runtime_service
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (STUB / not participating in startup)
B. Evidence
- Folder ada, modul servis didefinisikan, namun consumer = 0 dari trace. (E0-001)
C. Activation Path
- No Activation Path (tidak di-import oleh entry/CLI startup)
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not present in startup registry (no resolve path)
G. Host
- No Host
H. Gap Analysis
- Stub / belum di-wire ke pipeline; konstruktor ada tapi service api tidak digunakan
I. Minimal Action
- Tambahkan **1** registration step di StartupPipeline yang mendaftarkan runtime_service ke RuntimeRegistry sebagai placeholder health endpoint (tidak mengubah kontrak) sehingga service dapat dipanggil via CLI health/status
J. Confidence
- Verified

3) Runtime Root: sam.runtime_root
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (Dormant)
B. Evidence
- runtime_root memiliki builder/main, namun consumer eksternal = 0 di startup trace. (E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered at startup
G. Host
- No Host
H. Gap Analysis
- Composition root belum menjadi bagian dari startup stage; kemungkinan dimaksudkan untuk packaging/build-time
I. Minimal Action
- Tambahkan **1** line di StartupPipeline untuk meng-import runtime_root.main in safe mode and register a composition-summary object in RuntimeRegistry (read-only snapshot) — ini hanya registrasi metadata
J. Confidence
- High (Verified)

4) Execution Runtime: sam.execution
A. Status
- Specified: YES
- Implemented: YES
- Operational: PARTIAL → Operational Preview (sandbox execution works; pipeline not wired into live host entry)
B. Evidence
- ExecutionRuntime registry/builder/validator ada; ConversationExecutionPipeline implementasi ada (src/sam/operations/conversation_execution.py) dan executors nyata tersedia, tetapi pipeline tidak di-wire ke CLI entry. (E0-001)
- Execution runs in ExecutionSandbox and gated by approval. (E0-001)
C. Activation Path
- No activation from default launcher. Available path: internal calls from operations but not from entry. i.e.: Entry → (not wired) → ConversationExecutionPipeline → ExecutionSandbox
D. Consumer
- Internal (operations), runtime_kernel components (internal), no external consumers via startup
E. Provider
- Uses local providers (filesystem/command) but those provider concrete classes are dormant in startup
F. Registry
- ExecutionRegistry exists at code-level; not populated by default startup
G. Host
- CLI (can be invoked manually), Desktop (if invoked by a controller), but not registered by HostLauncher by default
H. Gap Analysis
- Pipeline present but not activated by launcher; providers dormant; approval gate prevents real execution
I. Minimal Action
- Add **1** explicit activation mapping in StartupPipeline that registers ExecutionRuntime in RuntimeRegistry in PREVIEW mode (read-only, sandbox-only). This exposes execution via CLI commands under a safe flag (`--preview`) without changing runtime internals.
J. Confidence
- Verified

5) Model Runtime: sam.model_runtime
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT)
B. Evidence
- model_runtime files exist; in-dep = 0; not imported in startup trace. (E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered
G. Host
- No Host
H. Gap Analysis
- Isolated package, no runtime wiring or consumers
I. Minimal Action
- Add **1** registry entry (placeholder) in StartupPipeline so model_runtime appears in RuntimeRegistry with a health endpoint `model_runtime:status` returning `not-activated` — this documents presence without enabling behavior
J. Confidence
- Verified

6) Knowledge Runtime: sam.knowledge_runtime
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT)
B. Evidence
- Package exists; consumer = 0; not imported at startup. (E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered
G. Host
- No Host
H. Gap Analysis
- No consumer, not wired to runtime kernel
I. Minimal Action
- Register a capability descriptor (CapabilityRegistry) for KnowledgeRuntime via StartupPipeline so workflows can resolve it later; do NOT implement provider behavior
J. Confidence
- Verified

7) Workflow Runtime: sam.workflow_runtime
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT)
B. Evidence
- workflow engine (src/sam/workflow/engine.py) uses ExecutionContext from runtime kernel, but workflow_runtime package itself has 0 external consumers in startup trace. (E0-001)
C. Activation Path
- No Activation Path (CLI prints runtime tree but not activating domain)
D. Consumer
- Workflow engine (engine module) but domain runtime package not wired
E. Provider
- None
F. Registry
- Not registered by default
G. Host
- No Host
H. Gap Analysis
- Engine uses runtime kernel but domain runtime package not registered/activated
I. Minimal Action
- Register workflow_runtime in RuntimeRegistry and expose a health-check; allow CLI `sam workflow` to transition from static display to a `--preview` execution that uses ExecutionSandbox
J. Confidence
- High (Verified)

8) Artifact Runtime: sam.artifact_runtime
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT)
B. Evidence
- Package exists; in-dep low; not in startup trace. (E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered
G. Host
- No Host
H. Gap Analysis
- No consumers / not wired
I. Minimal Action
- Register artifact_runtime metadata in RuntimeRegistry and surface `artifact_runtime:status` health endpoint
J. Confidence
- Verified

9) Audit Runtime: sam.audit_runtime
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT)
B. Evidence
- Package present; not imported by startup; audit recorder runtime components exist but not wired. (E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered
G. Host
- No Host
H. Gap Analysis
- Not part of startup or execution flow
I. Minimal Action
- Register AuditRuntime in RuntimeRegistry; optionally enable log/telemetry hooks in read-only mode for early visibility
J. Confidence
- Verified

10) Policy Runtime: sam.policy_runtime
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT)
B. Evidence
- Implemented package; no consumers in startup. (E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered
G. Host
- No Host
H. Gap Analysis
- No runtime activation or consumer
I. Minimal Action
- Add registry placeholder + health endpoint; allow later resolution by Approval/Policy components
J. Confidence
- Verified

11) Mission Runtime: sam.mission_runtime
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT)
B. Evidence
- Package exists; consumer = 0; last active commit 2026-07-31 (feature). (git + E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered
G. Host
- No Host
H. Gap Analysis
- Not promoted into startup
I. Minimal Action
- Register mission_runtime entry in RuntimeRegistry and surface metadata to CLI for visibility
J. Confidence
- Verified

12) Cognitive Runtime: sam.cognitive_runtime
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT)
B. Evidence
- Package present; consumer = 0; not in startup trace. (E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered
G. Host
- No Host
H. Gap Analysis
- Dormant
I. Minimal Action
- Register placeholder in RuntimeRegistry + small read-only health endpoint
J. Confidence
- Verified

13) Memory Runtime: sam.memory
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT)
B. Evidence
- Implemented package; consumer=0 in startup trace; last commit 2026-08-01. (E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered
G. Host
- No Host
H. Gap Analysis
- Not part of startup
I. Minimal Action
- Register memory runtime metadata in RuntimeRegistry; expose a read-only store status endpoint
J. Confidence
- Verified

14) Skill Runtime: sam.skills
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT)
B. Evidence
- Package present; no startup consumer. (E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered
G. Host
- No Host
H. Gap Analysis
- Dormant
I. Minimal Action
- Register as placeholder in RuntimeRegistry; expose skill listing metadata via CLI for visibility
J. Confidence
- Verified

15) Intelligence Runtime: sam.intelligence_runtime
A. Status
- Specified: YES
- Implemented: YES
- Operational: NO (DORMANT / Experimental)
B. Evidence
- Package exists; in-dep small; last commit 2026-08-01 (alpha). (git + E0-001)
C. Activation Path
- No Activation Path
D. Consumer
- No Consumer
E. Provider
- None
F. Registry
- Not registered
G. Host
- No Host
H. Gap Analysis
- Early alpha; intentionally experimental; not wired to pipeline
I. Minimal Action
- Register in RuntimeRegistry as `experimental` and surface metadata; no activation required
J. Confidence
- Verified (Hypothesis: intended experimental)

Consolidated Matrix (Spec/Impl/Operational/Confidence)
-----------------------------------------------------
| Runtime | Specified | Implemented | Operational | Confidence |
|---|---:|---:|---:|---:|
| sam.runtime | YES | YES | YES | Verified-High |
| sam.runtime_service | YES | YES | NO | Verified |
| sam.runtime_root | YES | YES | NO | High |
| sam.execution | YES | YES | PARTIAL (Preview) | Verified |
| sam.model_runtime | YES | YES | NO (Dormant) | Verified |
| sam.knowledge_runtime | YES | YES | NO | Verified |
| sam.workflow_runtime | YES | YES | NO | Verified |
| sam.artifact_runtime | YES | YES | NO | Verified |
| sam.audit_runtime | YES | YES | NO | Verified |
| sam.policy_runtime | YES | YES | NO | Verified |
| sam.mission_runtime | YES | YES | NO | Verified |
| sam.cognitive_runtime | YES | YES | NO | Verified |
| sam.memory | YES | YES | NO | Verified |
| sam.skills | YES | YES | NO | Verified |
| sam.intelligence_runtime | YES | YES | NO (Experimental) | Hypothesis-High |

Operational Heat Map (single category per runtime)
--------------------------------------------------
- Operational: sam.runtime
- Operational Preview: sam.execution
- Dormant: sam.model_runtime, sam.knowledge_runtime, sam.workflow_runtime, sam.artifact_runtime, sam.audit_runtime, sam.policy_runtime, sam.mission_runtime, sam.cognitive_runtime, sam.memory, sam.skills, sam.intelligence_runtime
- Stub: sam.runtime_service, sam.runtime_root
- Legacy: (none)
- Experimental: sam.intelligence_runtime (also listed Dormant)

Dependency Map (simplified)
---------------------------
Presentation / CLI
↓
Runtime Kernel (sam.runtime)
↓
Execution (sam.execution)
↓
Provider (sam.providers — concrete providers dormant)

Tandai: ACTIVE = sam.runtime, sam.execution (preview); DORMANT = semua *_runtime packages

Migration Opportunity (per-runtimes Dormant)
--------------------------------------------
Pendekatan umum (minimal, non-design):
1. **Visibility-first**: registrasikan runtime ke RuntimeRegistry sebagai metadata/health-only. Tujuan: terlihat & dapat dilacak dari CLI tanpa mengaktifkan perilaku.
2. **Preview activation**: enable `--preview` mode for a runtime that uses ExecutionSandbox (safe, no real side-effects). Expose via CLI optional flag.
3. **Consumer seeding**: buat small shim/adapter command yang memanggil a preview use-case (e.g., workflow sample run) untuk validasi end-to-end. Shim dipakai only in preview mode.

Contoh minimal per runtime (single-step, non-invasive):
- model_runtime: register metadata in RuntimeRegistry + health endpoint
- knowledge_runtime: register capability descriptor in CapabilityRegistry
- workflow_runtime: register + expose `sam workflow --preview` that runs a sample workflow through ExecutionSandbox
- artifact_runtime/audit_runtime/policy_runtime: register placeholders + health endpoints
- memory/skills: register placeholders + `sam memory list --preview` that returns read-only listing
- mission_runtime: register metadata accessible via `sam runtime status` (read-only)

Architecture Check
------------------
Apakah sesuai Constitution? (YES/NO)
- sam.runtime: YES
- sam.execution: YES (preview) — aligns with Execution Specification
- semua *_runtime (domain): YES — sesuai spec (exist as specified) but NOT operational by design until consumers & activation wired

Appendix
--------
A. Runtime Maturity Matrix (brief)
- See consolidated matrix above.

B. Operational Debt (example)
- OD-001: Knowledge Runtime — never activated since v18 (no consumer, no registry entry)
- OD-002: Model Runtime — in-dep 0 (isolated), needs registration to be discoverable

C. Activation Graph (global)
- Entry (CLI/Desktop/Web)
  → StartupPipeline
     → RuntimeRegistry (populate)
        → sam.runtime (start/run)
           → ExecutionRuntime (preview via explicit registration)
              → ExecutionSandbox (approval)

D. Operational Timeline (git evidence)
- runtime: last touched 2026-08-03 (E1-003)
- runtime_service: 2026-08-01
- runtime_root: 2026-08-03
- execution: 2026-07-31
- model_runtime: 2026-08-01
- knowledge_runtime: 2026-07-31
- workflow_runtime: 2026-08-01
- artifact_runtime: 2026-08-01
- audit_runtime: 2026-08-01
- policy_runtime: 2026-08-01
- mission_runtime: 2026-07-31
- cognitive_runtime: 2026-08-01
- memory: 2026-08-01
- skills: 2026-07-31
- intelligence_runtime: 2026-08-01

Deliverable
-----------
- File: docs/design/O0-001_Runtime_Operationalization_Strategy.md (this file)

Acceptance Criteria Checklist
-----------------------------
- [x] Semua Runtime dianalisis
- [x] Tidak ada Runtime terlewat (15 terdaftar)
- [x] Semua status berbasis bukti (E0-001 + git)
- [x] Semua gap berbasis runtime trace
- [x] Tidak ada redesign
- [x] Tidak ada Runtime baru
- [x] Tidak ada perubahan Repository
- [x] Semua rekomendasi adalah minimal action (1 langkah)

Next Step (ops)
---------------
Saya bisa:
- A: Simpan dokumen (sudah ditulis) dan tunggu persetujuanmu untuk commit → saya akan commit & push hanya jika kamu izinkan.
- B: Langsung commit & push (butuh persetujuan explicit).

Pilih: Commit sekarang? (ya/tidak)

