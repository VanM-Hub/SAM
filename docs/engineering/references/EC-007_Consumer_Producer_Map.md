# EC-007 — Consumer & Producer Map

## Tujuan

Mencatat consumer dan producer aktual agar engineering berfokus pada activation, bukan penambahan capability.

---

## RuntimeCoordinator

Consumer
Banyak (CLI, Web, REST, Guardian, Service, Test).

Source
- CLI (8 file)
- Web
- REST
- Guardian
- Service
- Test

Status
- Operational core (dipakai per-request).
- Direct wiring.
- God Object Score: HIGH.

Catatan
Bukan satu-satunya jalur. Operations/Desktop berjalan tanpa RuntimeCoordinator.

---

## RuntimeService

Consumer
2 (WebRuntimeService + ConversationPreviewGateway) - S01/S02

Producer
0

Status
Ready but not primary -> Mulai Aktif (consumer Web + Conversation).
Consumer S01: Web (/ dan /runtime). Consumer S02: Conversation preview.
Tetap gateway (bukan executor/coordinator).

---

## ExecutionRuntime

Producer
1 (RuntimeAPI action execution.preview - Session 01)

Consumer
Internal saja.

Status
Pipeline selesai.
Producer PREVIEW pertama (mode=preview), provider TIDAK dieksekusi.
Belum production execution (ADR-024).

---

## Presentation

Consumer
Sedikit.

Status
Ready but not primary.
Belum menjadi entry utama.

---

## Operations (jalur nyata)

Consumer
Desktop, Conversation.

Status
Operational (jalur Provider, tanpa RuntimeService).
0 import sam.runtime.

---

## Web

Consumer
Aktif per-request.
Masih direct ke Coordinator.

---

## REST

Consumer
Aktif per-request.
Masih direct ke Coordinator.

---

## CLI

Consumer
Sangat besar.
Deep coupling.
Direct ke Coordinator per-perintah.

---

## Provider

Consumer
Observation active (jalur Operations/Desktop).

Menunggu activation execution.

---

## Runtime Dormant

Consumer
0

Activation
0

---

## Consumer Priority

Paling Mendesak (S01+S02 target tercapai)
- RuntimeService: consumer 2 (Web + Conversation preview)
- ExecutionRuntime: producer 2 (Web preview + Conversation preview)
- Lanjut: Consumer runtime dormant sesuai kebutuhan operasional

Paling Banyak
RuntimeCoordinator

Paling Aman Ditambah
Presentation
RuntimeService
ExecutionRuntime

---

## Engineering Insight

Engineering berikutnya bukan membuat runtime.

Engineering berikutnya adalah memindahkan consumer.

Sebagian consumer memang sudah pindah ke jalur Operations (tanpa Coordinator).

Sebagian besar masih di RuntimeCoordinator.

---

## Jangan Dilakukan

- Menambah consumer ke RuntimeCoordinator.
- Menambah producer baru di luar ExecutionRuntime.
- Membuat activation path baru yang melewati RuntimeService.

---

## Fokus Engineering

[S01..S10 SELESAI] RuntimeService consumer_eff=3 (Web, Conversation, Presentation). 6 capability aktif (Knowledge/Workflow/Artifact/Memory/Policy/Audit) via Activation Pattern. RuntimeCoordinator direct-wiring 10->8 (S10 TDR).

Lanjut: Session 03 (Desktop) & migrasi endpoint sesuai scope.

Kurangi consumer RuntimeCoordinator.

---

## Exit Criteria

Consumer RuntimeService > 0.

Producer ExecutionRuntime > 0.

Consumer RuntimeCoordinator menurun.

---

## Referensi

RSR-001
RSR-002
RSR-005
E0-001
