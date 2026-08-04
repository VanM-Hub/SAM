# EC-004 — Integration Status

## Tujuan

Mencatat status integrasi nyata seluruh entry point.

---

## Format Status

Status dibedakan menjadi Entry Point, Activation Path, dan Host Operational.

Istilah "Operational" hanya dipakai bila launcher benar-benar berhasil menjalankan host atau jalur benar-benar aktif.

---

## Web

Status
Entry point tersedia.

Runtime
Direct wiring ke RuntimeCoordinator (per-request).

Execution
Tidak.

RuntimeService
Tidak.

Host Launcher
Not Fully Operational (modul host tidak memiliki fungsi run module-level).

Prioritas
TINGGI

---

## REST

Status
Entry point tersedia.

Runtime
Direct wiring ke RuntimeCoordinator (per-request).

Execution
Tidak.

RuntimeService
Tidak.

Prioritas
TINGGI

---

## Conversation

Status
Entry point tersedia.

Alur
Operations → Provider (observation).

Execution
Preview (melalui jalur resmi) - Session 02. Provider tidak dieksekusi.

RuntimeService
Ya (preview via ConversationPreviewGateway -> RuntimeAPI execution.preview).

Catatan
Jalur Operations legacy tetap ada; Conversation kini punya jalur resmi preview (S02).
Preview: Conversation -> RuntimeService -> ExecutionRuntime (preview, ADR-024).
Prioritas
TINGGI

---

## Dashboard

Status
Preview.

Bridge tersedia.

Masih preview_only.

Prioritas
SEDANG

---

## CLI

Status
Entry point tersedia.

Deep coupling.

Direct wiring ke RuntimeCoordinator (per-perintah).

Activation path tersedia per-perintah (bukan saat startup).

Prioritas
RENDAH

Alasan
Regression besar.

---

## Desktop

Status
Entry point tersedia.

Host launcher berhasil hidup (Operational).

Jalur Operations/Provider.

Masih masa transisi untuk Presentation Layer baru.

Prioritas
RENDAH

---

## Automation

Status
Entry point tersedia.

Approval berjalan.

Eksekusi masih simulasi (belum activation penuh).

Prioritas
RENDAH

---

## Plugin

Status
Meta Layer.

Tidak melakukan execution.

Prioritas
RENDAH

---

## RuntimeService

Status
Ready but not primary -> Consumer pertama aktif (Session 01).

Consumer
1 (WebRuntimeService - Web / dan /runtime, lifecycle/status)

---

## ExecutionRuntime

Status
Ready but not primary -> Producer preview pertama aktif (Session 01).

Producer
1 (RuntimeAPI action execution.preview; mode=preview, provider tidak dieksekusi)

---

## Provider

Status
Tersedia (Observation Provider aktif di jalur Operations).

Belum jadi execution (ADR-024). Jalur resmi preview kini resolve provider (S03), execute tidak dipanggil.

---

## Integration Score (berdasarkan aktivasi aktual)

Runtime
██████████ (Operational core, per-request direct)

Presentation
█████░░░░░ (Ready, consumer sedikit)

RuntimeService
░░░░░░░░░░ (0 consumer)

ExecutionRuntime
██████░░░░ (pipeline selesai, 0 producer)

Provider
█████░░░░░ (observation aktif, execution belum)

---

## Engineering Insight

Sebagian besar komponen telah selesai.

Yang belum selesai adalah hubungan antar komponen.

Sebagian entry masih direct wiring ke Coordinator.

Sebagian entry (Operations/Desktop) sudah berjalan lewat Provider.

---

## Jangan Dilakukan

Mengaktifkan seluruh entry sekaligus.

Lakukan integrasi bertahap.

---

## Fokus Engineering (urutan)

Web
→
REST
→
Conversation
→
Dashboard
→
CLI
→
Desktop

---

## Exit Criteria

Minimal Web dan REST menggunakan jalur RuntimeService.

---

## Referensi

E0-001
O0-001
D0-001
D1-001
RSR-002

---

## Presentation (Session 04)

Status
Presentation Layer menerima RuntimeService via DI (AD-S04).

RuntimeService
Consumer: Presentation membaca kontrak RuntimeService (lifecycle/status/descriptor/metadata/contract) sbg snapshot immutable. Tanpa akses RuntimeCoordinator/ExecutionRuntime.

Activation
Presentation -> RuntimeService -> ExecutionRuntime -> Provider Resolution -> STOP.
---

## Knowledge (Session 05)

Status
Mulai aktif - consumer pertama (KnowledgePreviewConsumer via jalur resmi).

Alur
Conversation -> RuntimeService -> ExecutionRuntime (preview) -> Knowledge (bridge yg sudah ada).

Pembatasan
Hanya resolve/summary/descriptor/metadata/capability + pipeline preview. Indexing/embedding/search/RAG = belum (bukan scope).
---

## Workflow (Session 06)

Status
Mulai aktif - consumer pertama (WorkflowPreviewConsumer via jalur resmi).

Alur
Conversation -> RuntimeService -> ExecutionRuntime (preview) -> Workflow (+ knowledge input).

Pembatasan
Hanya resolve/status/pipeline preview. Scheduler/planner/automation penuh belum (bukan scope).
---

## Artifact (Session 07)

Status
Mulai aktif - consumer pertama (ArtifactPreviewConsumer via Activation Pattern Standard).

Alur
Conversation -> RuntimeService -> ExecutionRuntime (preview) -> ArtifactRegistry -> ConversationArtifactBridge -> STOP.

Pembatasan
Tanpa generate/engine/storage; tanpa integrasi Mission/Contract/Dashboard/Intelligence.
---

## Memory (Session 08)

Status
Mulai aktif - consumer pertama (MemoryPreviewConsumer via Activation Pattern Standard). Capability mandiri (bukan namespace payload).

Alur
Conversation -> RuntimeService -> ExecutionRuntime (preview) -> MemoryRegistry -> ConversationMemoryBridge -> STOP.

Pembatasan
Tanpa storage/DB/embedding/retrieval; tanpa integrasi knowledge/workflow/mission.
---

## Audit (Session 09)

Status
Mulai aktif - consumer pertama (AuditPreviewConsumer via Activation Pattern Standard).

Alur
Conversation -> RuntimeService -> ExecutionRuntime (preview) -> AuditRegistry -> ConversationAuditBridge -> STOP.

Pembatasan
Immutable, no-execute; tanpa AuditEngine/Compliance/Storage; tanpa integrasi terlarang.
---

## Policy (Session 09)

Status
Mulai aktif - consumer pertama (PolicyPreviewConsumer via Activation Pattern Standard).

Alur
Conversation -> RuntimeService -> ExecutionRuntime (preview) -> PolicyRegistry -> ConversationPolicyBridge -> STOP.

Pembatasan
No evaluate/decision; tanpa GovernanceEngine; tanpa integrasi terlarang.