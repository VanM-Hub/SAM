# EC-011 — Engineering Priorities

## Tujuan

Menetapkan urutan implementasi berdasarkan kondisi repository saat ini.

---

## Prioritas 1

Activation RuntimeService

Target
Consumer pertama.

---

## Prioritas 2

Activation ExecutionRuntime

Target
Producer pertama.

---

## Prioritas 3

Migrasi Web

Target
Tidak lagi membuat RuntimeCoordinator langsung (menggunakan jalur RuntimeService).

---

## Prioritas 4

Migrasi REST

Target
Menggunakan jalur RuntimeService.

---

## Prioritas 5

Conversation Integration

Target
Masuk ke jalur resmi RuntimeService.

---

## Prioritas 6

Dashboard Integration

Target
Keluar dari preview-only.

---

## Prioritas 7

Provider Activation

Target
ExecutionRuntime mampu memanggil provider resmi.

---

## Prioritas 8

CLI Migration

Target
Mengurangi deep coupling.

---

## Prioritas 9

Desktop Migration --[S04] Presentation Layer memakai RuntimeService via DI (Presentation jadi consumer jalur resmi)

Target
Menggunakan Presentation Layer baru -- SELESAI konfigurasi DI (PresentationLayer(runtime_service=...)).

---

## Prioritas 10

Activation Runtime Domain --[Knowledge S05 aktif; Workflow S06 aktif]

Target
Workflow --[S06] MULAI AKTIF (consumer 1)
Knowledge --[S05] MULAI AKTIF (consumer 1)
Model
Mission
Policy

sesuai kebutuhan operasional (bukan semua sekaligus).

---

## Yang Tidak Menjadi Prioritas

- Runtime baru.
- Refactor besar RuntimeCoordinator.
- Mengaktifkan seluruh runtime dormant.
- Penyempurnaan dokumentasi.
- Optimasi yang tidak mengurangi technical debt.

---

## Engineering Insight

Urutan ini disusun berdasarkan ROI engineering.

Perubahan dengan regression kecil dan dampak besar dikerjakan lebih dahulu.

---

## Exit Criteria

RuntimeService menjadi jalur operasional nyata.

ExecutionRuntime menerima request production.

Web dan REST tidak lagi direct wiring ke Coordinator.

---

## Referensi

O0-001
RSR-002
RSR-005
