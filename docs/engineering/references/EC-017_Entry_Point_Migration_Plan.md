# EC-017 — Entry Point Migration Plan

## Tujuan

Menjadi urutan migrasi entry point dengan risiko regression terendah.

Catatan: istilah "migrasi" di sini berarti memindahkan activation path entry menuju RuntimeService/ExecutionRuntime, bukan sekadar membuat entry tersedia.

---

## Batch 1

Web

Alasan
Coordinator direct wiring dapat dikonsolidasi.
Regression kecil.
ROI tinggi.

---

## Batch 2

REST

Alasan
Pola sama dengan Web.

---

## Batch 3

Conversation

Alasan
Sudah dekat dengan Presentation.
Flash Conversation saat ini lewat Operations/Provider.

---

## Batch 4

Dashboard

Alasan
Masih Preview.

---

## Batch 5

CLI

Alasan
Consumer terbesar.
Migrasi dilakukan terakhir.

---

## Batch 6

Desktop

Alasan
Masih transisi.
Sudah hidup via Operations.

---

## Batch 7

Automation

Setelah ExecutionRuntime stabil.

---

## Batch 8

Plugin

Hanya bila Plugin mulai menjadi execution entry.

---

## Prinsip

Satu batch.
→
Regression.
→
Commit.
→
Lanjut batch berikutnya.

---

## Exit Criteria

Tidak ada entry point baru yang membuat RuntimeCoordinator secara langsung.

---

## Referensi

RSR-002
E0-001
