# AD-S02-001 — Payload sebagai Execution Context

**Status:** Accepted · **Tanggal:** 2026-08-04 · **Tipe:** Engineering Decision (Session 02)

## Keputusan
- Gunakan `ExecutionRequest.payload` untuk membawa context lintas layer.
- payload **bukan** tempat menyimpan state Conversation; payload = **Execution Context**.

## Prinsip
- `ExecutionRequest` tetap DTO generik. JANGAN tambah field DTO baru.
- JANGAN ubah ExecutionRuntime. JANGAN ubah RuntimeService.
- Payload serializable, immutable selama execution, kontrak lintas layer.

## Payload (namespace 'conversation')
```
payload = {
    "conversation": { "conversation_id": "...", "turn_id": "...", "request": "..." }
}
```
- Istilah `request` (bukan `intent`) — menghindari ambiguitas dgn Intent Classification
  di fase Intelligence & Agent nanti.

## Context Identity
- Minimal: `conversation_id` + `turn_id` (identifier yang sudah ada; jangan buat sistem ID baru).

## Forward Compatibility (namespace)
```
payload ├── conversation (diisi) └── memory/knowledge/workflow/agent/telemetry (kosong sampai aktif)
```
- Session 02 HANYA mengisi `payload["conversation"]`. Namespace lain dibiarkan kosong.

## Jangan Masukkan ke payload
UI State · Window State · ViewModel · Runtime Object · Conversation Object · Service ·
Provider · Callback · Function · Session Object.
