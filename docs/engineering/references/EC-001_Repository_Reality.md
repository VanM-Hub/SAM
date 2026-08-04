# EC-001 — Repository Reality

## Tujuan

Memberikan gambaran kondisi implementasi SAM yang sebenarnya berdasarkan hasil audit engineering, bukan berdasarkan roadmap atau desain.

---

## Kondisi Aktual

Repository telah menyelesaikan fase Foundation.

Seluruh Canonical Document telah selesai.

Architecture telah dibekukan.

CI hijau.

Regression test lulus.

Namun implementasi operasional belum sepenuhnya tersambung.

Repository saat ini berada pada fase transisi dari Foundation menuju Operational Product.

---

## Kondisi Nyata Repository

Architecture
████████████████████ 100%

Documentation
████████████████████ 100%

Governance
███████████████████░ 95%

Execution Design
███████████████████░ 95%

Operational Wiring
████░░░░░░░░░░░░░░░░ 20%

Product Integration
██░░░░░░░░░░░░░░░░░░ 10%

---

## Realitas Implementasi

Repository tidak kekurangan capability.

Repository kekurangan activation.

Sebagian besar pekerjaan engineering berikutnya adalah:

- menghubungkan capability
- mengaktifkan consumer
- menyelesaikan wiring
- mengurangi technical debt operasional

bukan membuat capability baru.

---

## Dua Dunia Repository

Saat ini terdapat dua dunia implementasi.

Legacy Operational

- runtime
- execution
- operations
- coordinator
- launcher

Masih menjadi jalur operasional utama yang benar-benar dipakai.

Modern Architecture

- runtime_service
- execution_runtime
- presentation
- runtime_root

Sudah sesuai desain tetapi sebagian besar belum menjadi jalur utama aplikasi.

---

## Status Entry Point vs Activation vs Host

Tiga kondisi dibedakan secara eksplisit:

Entry Point

Aplikasi memiliki entry point.

CLI, Desktop, REST, Web tersedia.

Keberadaan entry point tidak otomatis berarti jalur production aktif.

Activation Path

Jalur wiring yang benar-benar dilewati request.

Activation berarti: memiliki consumer, dipanggil runtime, ikut lifecycle, terlihat pada execution trace.

Host / Launcher Operational

Launcher berhasil menjalankan aplikasi secara penuh sampai process hidup.

Kondisi ini berbeda dari activation.

Ketiganya tidak boleh disamakan.

---

## Status Per Entry Point

CLI

Entry point tersedia.

Direct wiring ke RuntimeCoordinator.

Activation path tersedia per-perintah (bukan saat startup).

Web

Entry point tersedia.

Direct wiring ke RuntimeCoordinator.

Activation path tersedia per-request.

REST

Entry point tersedia.

Direct wiring ke RuntimeCoordinator.

Activation path tersedia per-request (read-only).

Desktop

Entry point tersedia.

Activation path tersedia (jalur Operations/Provider).

Merupakan host yang launcher-nya berhasil hidup.

Automation

Entry point tersedia.

Approval berjalan.

Eksekusi masih simulasi (belum activation penuh).

Plugin

Meta management.

Tidak melakukan execution.

---

## Status Launcher / Host

Launcher dipisahkan dari status entry point.

sam (console)

Entry point tersedia.

Launcher belum berhasil menjalankan host.

Kondisi: Not Fully Operational.

Penyebab: module host tidak memiliki fungsi run module-level.

sam-desktop

Entry point tersedia.

Launcher berhasil menjalankan host.

Kondisi: Operational.

sam-headless

Entry point tersedia.

Launcher belum berhasil menjalankan host.

Kondisi: Not Fully Operational.

Penyebab: kontrak TelemetryService tidak memiliki method start.

sam-diagnostic

Entry point tersedia.

Berjalan sebagai snapshot lalu exit (bukan aplikasi persistent).

Kondisi: Transition / Partial.

api_server

Entry point tersedia.

Launcher belum berhasil menjalankan host.

Kondisi: Not Fully Operational.

Penyebab: module host tidak memiliki fungsi run module-level.

---

## Status Runtime

Operational Core

- runtime (dipakai per-request CLI/Web/API, bukan saat startup)
- execution (preview)

Dormant (Ready but not primary)

- workflow_runtime
- knowledge_runtime
- policy_runtime
- mission_runtime
- audit_runtime
- artifact_runtime
- cognitive_runtime
- model_runtime
- intelligence_runtime
- memory_runtime
- skills_runtime

Sebagian besar runtime merupakan capability framework yang belum memiliki activation path.

---

## Jalur Wiring Aktual

Repository tidak memiliki satu jalur tunggal.

Beberapa activation path hidup berdampingan.

Jalur 1 — Operations (Real flow, hidup tanpa RuntimeService)

Conversation
↓
Operations
↓
Provider (Observation)

Ops: jalur ini TIDAK menyentuh RuntimeCoordinator dan berjalan.

Jalur 2 — Direct Coordinator (sebagian flow)

CLI / Web / REST
↓
RuntimeCoordinator (per-request)

Jalur inilah yang masih menjadi berat direct wiring.

Jalur Target (belum aktif penuh)

Presentation
↓
RuntimeService
↓
Execution Runtime
↓
Provider

Belum ada satu activation path yang dipakai seluruh entry point.

---

## Engineering Insight

Masalah terbesar repository bukan lagi struktur.

Masalah terbesar adalah belum adanya jalur operasional yang menyatukan seluruh entry point.

Sebagian besar entry point masih melakukan direct wiring ke RuntimeCoordinator.

Sebagian lain (Operations/Desktop) sudah berjalan lewat Provider tanpa RuntimeService.

Diagnosis wiring tetap dipertahankan.

Yang dikoreksi hanyalah generalisasi bahwa ada satu jalur tunggal.

---

## Jangan Dilakukan

- Membuat Runtime baru.
- Mendesain ulang Architecture.
- Mengubah Canonical Document untuk mempermudah implementasi.
- Memindahkan business logic ke Presentation.
- Menambah capability baru sebelum capability lama memiliki consumer.

---

## Fokus Engineering

Activation.

Integration.

Operational Wiring.

Technical Debt Reduction.

---

## Exit Criteria

Repository mulai menggunakan jalur operasional resmi:

Presentation
↓
RuntimeService
↓
Execution Runtime
↓
Provider

Minimal satu entry point telah menggunakan jalur tersebut.

---

## Referensi

MISSION
CONSTITUTION
SPECIFICATION_FREEZE
E0-001
O0-001
A0-001
D0-001
D1-001
RSR-001
RSR-002
RSR-005
