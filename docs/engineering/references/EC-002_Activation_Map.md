# EC-002 — Activation Map

## Tujuan

Menggambarkan capability dan runtime yang benar-benar aktif berdasarkan implementasi saat ini, sehingga engineer mengetahui area yang sudah operasional dan area yang masih dormant.

---

## Prinsip

Activation ≠ Folder.

Activation ≠ Runtime tersedia.

Activation hanya dianggap ada apabila:

- memiliki activation path,
- memiliki consumer,
- dipanggil saat startup,
- atau benar-benar digunakan pada runtime trace.

Entry Point dibedakan dari Activation Path dan Host Operational.

Keberadaan entry point tidak berarti jalur production aktif.

---

## Activation Reality

Berikut adalah status aktivasi sesuai implementasi aktual.

## Operational Core

runtime/

Peran
- bootstrap
- lifecycle
- session
- hosting
- recovery
- runtime state

Catatan
- Dipakai per-request oleh CLI / Web / API.
- TIDAK diinstansiasi saat startup normal (desktop/console/headless).
- Termasuk RuntimeCoordinator (kernel direct-wiring).

execution/

Peran
- approval
- planning
- sandbox
- execution flow

Status
- Preview / Available but not fully activated.
- Eksekusi nyata provider belum menjadi jalur utama.

guardian/

Peran
- monitoring
- validation
- runtime observation

Status
- Available.
- Digunakan pada jalur tertentu.

launcher/

Peran
- startup
- host selection
- bootstrap pipeline

Status
- Operational core untuk pemilihan host.
- Masing-masing host memiliki status launcher sendiri (tidak semua berhasil hidup).

cli/

Peran
- operational entry
- runtime command
- diagnostic

Status
- Entry point tersedia.
- Consumer RuntimeCoordinator terbesar.
- Activation path per-perintah.
- Masih menggunakan sebagian jalur lama (direct wiring).

## Entry Point Tersedia (Activation per-request)

web/

- Dashboard, monitoring, runtime status.
- Masih membuat RuntimeCoordinator secara langsung (direct wiring).
- Activation path per-request.

api/

- Runtime status, health, metrics.
- Masih membuat RuntimeCoordinator secara langsung (direct wiring).
- Activation path per-request (read-only).
- Belum menjadi jalur execution.

## Operational (Host Launcher Berhasil)

desktop/

- Jalur Operations/Provider.
- Launcher berhasil menjalankan host (def run tersedia).

Catatan: status "Operational" di sini merujuk pada host launcher yang berhasil hidup, bukan berarti seluruh stack modern sudah teraktivasi.

## Transition Layer (Ready but not primary)

presentation/

Status
READY

Business Logic
Tidak ada.

Peran
- Presentation Layer resmi.
- Belum menjadi entry utama seluruh aplikasi.
- Consumer masih sedikit.

runtime_root/

Status
READY

Peran
- Composition Root.

runtime_service/

Status
READY

Consumer
1 (WebRuntimeService - Web Runtime/Lifecycle/Status endpoint)

Peran
- Gateway kontrak & lifecycle.
- Consumer produksi pertama: Web (/ dan /runtime) - Session 01.
- Tetap gateway, bukan executor/coordinator.

execution_runtime/

Status
READY (preview)

Producer
1 (RuntimeAPI action execution.preview - Session 01)

Peran
- Execution Pipeline resmi.
- Producer PREVIEW pertama (mode=preview), provider TIDAK dieksekusi.
- Belum production execution (ADR-024 preview-only).

## Dormant Runtime (Ready but not primary)

Seluruh runtime berikut tersedia dan memiliki fondasi, tetapi belum memiliki activation path dan tidak memiliki consumer produksi.

workflow_runtime - MULAI AKTIF (consumer 1 - WorkflowPreviewConsumer via jalur resmi, S06). Scheduler/planner/automation masih belum.
knowledge_runtime - MULAI AKTIF (consumer 1 - KnowledgePreviewConsumer via jalur resmi, S05). Indexing/embedding/search masih dormant.
policy_runtime - MULAI AKTIF (consumer 1 - PolicyPreviewConsumer, S09).
mission_runtime — Dormant, consumer 0.
artifact_runtime - MULAI AKTIF (consumer 1 - ArtifactPreviewConsumer via Activation Pattern Std, S07).
audit_runtime - MULAI AKTIF (consumer 1 - AuditPreviewConsumer, S09).
memory - MULAI AKTIF (consumer 1 - MemoryPreviewConsumer via Activation Pattern Std, S08; capability mandiri).
cognitive_runtime — Dormant, consumer 0.
model_runtime — Dormant, consumer 0.
intelligence_runtime — Dormant, consumer 0.
skills_runtime — Dormant, consumer 0.

Walaupun memiliki banyak implementasi, belum menjadi jalur operasional utama.

---

## Ringkasan Activasi

Operational Core
runtime (per-request)
execution (preview)

Entry Point Tersedia (Activation per-request)
cli
web
api

Host Operational (launcher hidup)
desktop (jalur Operations)

Mulai Aktif (Session 01 + S05)
- runtime_service: consumer 1 (WebRuntimeService)
- execution_runtime: producer 1 (preview)

Ready but Unused
- runtime_root (0 consumer produksi di luar package)
- presentation (consumer sedikit)

Dormant
workflow_runtime
# knowledge_runtime -> aktif (S05); tersisa:
policy_runtime -> aktif (S09)
mission_runtime
artifact_runtime
audit_runtime -> aktif (S09)
memory_runtime
cognitive_runtime
model_runtime
intelligence_runtime
skills_runtime

---

## Engineering Insight

Sebagian besar runtime bukan gagal.

Sebagian besar runtime memang belum memiliki consumer.

Masalah repository saat ini bukan kurangnya runtime.

Masalahnya adalah activation.

---

## Jangan Dilakukan

- Menghapus runtime dormant karena terlihat tidak dipakai.
- Mengaktifkan seluruh runtime sekaligus.
- Membuat runtime baru untuk menggantikan runtime dormant.
- Menganggap dormant sebagai technical debt.

---

## Fokus Engineering

Tambahkan activation path.

Tambahkan consumer.

Integrasikan runtime yang sudah ada.

Jangan menambah runtime baru.

---

## Exit Criteria

Minimal RuntimeService dan ExecutionRuntime menjadi jalur operasional nyata.

Minimal satu runtime dormant memiliki activation path resmi.

---

## Referensi

E0-001
O0-001
C0-001
RSR-001
RSR-002
