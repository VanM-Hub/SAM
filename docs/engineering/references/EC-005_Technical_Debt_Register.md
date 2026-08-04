# EC-005 — Technical Debt Register

## Tujuan

Mencatat technical debt yang benar-benar mempengaruhi engineering.

---

## TD-001

Nama
RuntimeCoordinator Overload

Severity
HIGH

Blocker
Sebagian entry masih direct wiring ke Coordinator.

Recovery
Activation RuntimeService.

Exit
Consumer Coordinator berkurang.

---

## TD-002

Nama
RuntimeService 0 Consumer

Severity
HIGH

Recovery
Tambah consumer pertama.

Exit
Web menggunakan RuntimeService.

---

## TD-003

Nama
ExecutionRuntime 0 Producer

Severity
HIGH

Recovery
Hubungkan RuntimeService.

Exit
ExecutionRequest pertama masuk.

---

## TD-004

Nama
Legacy Execution World

Severity
HIGH

Recovery
Migrasi bertahap.

Exit
ExecutionRuntime menjadi jalur utama.

---

## TD-005

Nama
Direct Runtime Wiring

Severity
HIGH

Recovery
Gunakan Composition Root.

Exit
Entry tidak membuat Coordinator secara langsung.

---

## TD-006

Nama
Dormant Runtime

Severity
LOW

Recovery
Activation bila diperlukan.

Exit
Consumer tersedia.

Catatan
Dormant bukan dead code. Bukan prioritas untuk diaktifkan semua.

---

## TD-007

Nama
SQLite Direct Dependency

Severity
MEDIUM

Recovery
Migrasi Repository Pattern.

Exit
Runtime tidak mengakses SQLite langsung.

---

## TD-008

Nama
CLI Deep Coupling

Severity
MEDIUM

Recovery
Tahap akhir.

Exit
CLI menggunakan jalur resmi.

---

## Catatan Tambahan — Launcher Mismatch

Beberapa host launcher belum berhasil hidup (console, api_server, headless) karena kontrak fungsi run/start tidak cocok.

Ini bukan activation debt murni, tetapi perlu dicatat agar tidak dikira sebagai "Operational".

Kategori
Non-activation debt (kontrak launcher).

Recovery
Disesuaikan ketika migrasi entry yang bersangkutan.

---

## Engineering Insight

Mayoritas technical debt bukan bug.

Mayoritas merupakan activation debt.

---

## Jangan Dilakukan

Memperbaiki debt yang bukan blocker activation.

---

## Fokus Engineering

Debt yang menghambat wiring.

---

## Exit Criteria

Debt HIGH berkurang tanpa menambah Architecture Debt.

---

## Referensi

E0-001
O0-001
A0-001
RSR-005

---

## STATUS S10 (TDR, 2026-08-04)

- TD-001 (RuntimeCoordinator Overload): direct-wiring 10->8 (S10). Consumer mulai turun.
- TD-002 (RuntimeService 0 consumer): SELESAI -> consumer 3 (Web/Conv/Pres) + 6 capability aktif.
- TD-003 (ExecutionRuntime 0 producer): SELESAI -> producer 2 preview.
- TD-005 (Direct Runtime Wiring): berkurang (health/cli -> jalur resmi).
- Legacy execution/ & reasoning/: di-deprecate (jangan hapus; penyatuan = Architecture Backlog).
- Project SAM v1 SELESAI (S01-S10).