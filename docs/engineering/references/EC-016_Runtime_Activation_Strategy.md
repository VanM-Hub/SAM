# EC-016 — Runtime Activation Strategy

## Tujuan

Menentukan urutan aktivasi runtime berdasarkan nilai operasional, bukan urutan pembuatan.

---

## Tahap 1

RuntimeService

Status
Ready but not primary.

Consumer
0

Prioritas
Sangat Tinggi

Target
Consumer pertama.

---

## Tahap 2

ExecutionRuntime

Status
Ready but not primary.

Producer
0

Prioritas
Sangat Tinggi

Target
Request pertama.

---

## Tahap 3

Provider

Status
Observation active (jalur Operations/Desktop).
Execution belum operational.

Target
ExecutionRuntime dapat memanggil Provider resmi.

---

## Tahap 4

WorkflowRuntime

Aktifkan hanya jika workflow production membutuhkan runtime khusus.

---

## Tahap 5

KnowledgeRuntime

Aktifkan ketika Knowledge benar-benar menjadi capability operasional.

---

## Tahap 6

ModelRuntime

Aktifkan setelah jalur execution stabil.

---

## Runtime Lain

Mission
Policy
Memory
Artifact
Audit
Cognitive
Skills
Intelligence

Aktivasi berdasarkan kebutuhan operasional.

Bukan berdasarkan urutan roadmap.

---

## Prinsip

Activation mengikuti kebutuhan aplikasi.

Bukan mengikuti jumlah runtime.

---

## Exit Criteria

Runtime baru dianggap hidup apabila memiliki:

- activation path
- consumer
- regression
- monitoring

---

## Referensi

O0-001
C0-001
RSR-001
