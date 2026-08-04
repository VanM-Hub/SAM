# EC-003 — Dependency & Wiring Map

## Tujuan

Menggambarkan dependency aktual dan jalur wiring repository berdasarkan implementasi saat ini.

---

## Prinsip

Dependency bukan diukur dari jumlah import.

Dependency dianggap nyata apabila:

- dipanggil production,
- memiliki consumer,
- membentuk activation path,
- mempengaruhi lifecycle runtime.

Entry Point berbeda dari Activation Path dan Host Operational.

---

## Wiring Aktual — Beberapa Jalur Hidup Berdampingan

Repository tidak memiliki satu jalur tunggal.

Berikut jalur yang saat ini benar-benar ada.

Jalur 1 — Operations (Real flow, tanpa RuntimeCoordinator)

Conversation
↓
Operations
↓
Provider (Observation)

Fakta: operations TIDAK mengimport sam.runtime.
Jalur ini berjalan tanpa RuntimeService dan tanpa RuntimeCoordinator.

Jalur 2 — Direct Coordinator

CLI
↓
Launcher / perintah
↓
RuntimeCoordinator (per-request)

Web
↓
RuntimeCoordinator() (per-request)
↓
Telemetry
↓
Guardian
↓
Dashboard

REST
↓
RuntimeCoordinator() (per-request)
↓
Runtime Status (read-only)

Jalur ini adalah sumber berat direct wiring.

Jalur 3 — Automation / Approval

Automation
↓
ActionExecutor
↓
Approval
↓
Sandbox

---

## Jalur Target (belum aktif penuh)

Presentation
↓
RuntimeService
↓
Execution Runtime
↓
Provider

Jalur ini belum menjadi jalur operasional utama.  [Session 01: mulai terbentuk - Web->RuntimeService consumer=1, ExecutionRuntime preview producer=1, provider tidak dieksekusi]  | S03: jalur resmi preview kini terhubung ke Provider Resolution (filesystem/shell/sqlite di-resolve), execute tidak dipanggil (ADR-024).

---

## RuntimeCoordinator — Bukan Satu-Satunya Jalur

RuntimeCoordinator bukan satu-satunya jalur repository.

Sebagian flow masih menggunakannya (CLI, Web, REST).

Sebagian flow telah menggunakan jalur lain (Operations/Desktop lewat Provider).

Belum ada activation path tunggal yang digunakan seluruh entry point.

Diagnosis wiring tetap dipertahankan.

Yang dikoreksi hanyalah generalisasi bahwa RuntimeCoordinator adalah satu-satunya jalur.

---

## Dependency Gravity

Sangat Tinggi
runtime/
- RuntimeCoordinator
- launcher/
- guardian/

Tinggi
web/
cli/
execution/

Sedang
api/
presentation/
runtime_root/

Rendah
runtime_service/ (consumer_eff 3 - Web + Conversation + Presentation; + Knowledge S05 + Workflow S06 + Artifact S07 + Memory S08 + Policy S09 + Audit S09)
execution_runtime/ (producer 2 - Web + Conversation preview, S01/S02)

Dormant
knowledge_runtime/
workflow_runtime/
policy_runtime/
artifact_runtime/
audit_runtime/
memory_runtime/
mission_runtime/
cognitive_runtime/
model_runtime/
skills_runtime/

---

## Dependency Reality

RuntimeCoordinator
- Consumer banyak (CLI, Web, REST, Guardian, Service, Test).
- Merupakan kernel direct-wiring.

RuntimeService
- Consumer = 2 (WebRuntimeService + ConversationPreviewGateway, S01/S02).
- Producer = 0.

ExecutionRuntime
- Producer = 2 (Web + Conversation preview, S01/S02).
- Consumer internal saja.

Presentation
- Sudah tersedia tetapi belum menjadi jalur utama.
- Consumer sedikit.

Operations
- Mandiri: 0 import sam.runtime.
- Jalur nyata desktop/conversation.

---

## Wiring Bottleneck

RuntimeCoordinator masih menjadi titik berat untuk sebagian entry point (CLI, Web, REST).

Akibatnya pada jalur tersebut:
- RuntimeService tidak digunakan.
- ExecutionRuntime tidak menerima request.
- Provider jalur resmi aktif utk RESOLUTION (S03); execute tidak dipanggil (preview).

Catatan: tidak semua entry berhenti di Coordinator.
Operations/Desktop sudah berjalan lewat Provider.

---

## Engineering Insight

Repository tidak mengalami dependency problem secara keseluruhan.

Repository mengalami wiring problem.

Sebagian besar dependency sudah benar.

Yang belum benar adalah arah aliran dependency pada sebagian entry point.

---

## Jangan Dilakukan

- Menambah dependency baru ke RuntimeCoordinator.
- Membuat shortcut langsung ke Provider dari Presentation.
- Menghubungkan Runtime secara langsung.
- Membypass RuntimeService ketika activation mulai dilakukan.

---

## Fokus Engineering

Kurangi wiring langsung ke RuntimeCoordinator.

Tambahkan wiring menuju RuntimeService.

Pertahankan dependency tetap acyclic.

---

## Exit Criteria

Minimal satu entry point menggunakan:

Presentation
↓
RuntimeService
↓
Execution Runtime
↓
Provider

---

## Referensi

E0-001
O0-001
RSR-002
RSR-005
