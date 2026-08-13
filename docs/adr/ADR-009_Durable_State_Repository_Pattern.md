# ADR-009 — Durable State Repository Pattern (M12-001 Self-Preservation)

| Field | Value |
|---|---|
| **Decision ID** | ADR-009 |
| **Title** | Durable State Repository Pattern |
| **Status** | Accepted (M12-001) |
| **Date** | 2026-08-13 |
| **Architecture Domain** | Runtime — Persistence / Self-Preservation |
| **Decision Type** | Architectural decision (persistence foundation) |
| **Owner** | Project SAM |
| **Author** | ZARA |

---

## Purpose

Menetapkan fondasi persistence runtime SAM agar state operasional **tidak lagi bergantung pada in-memory singleton**. M12-001 menghilangkan ketergantungan runtime terhadap in-memory state dan menggantinya dengan **repository pattern** yang menyimpan entity per-id ke PostgreSQL, sehingga mission dapat hidup bersamaan tanpa saling overwrite dan selamat dari restart.

ADR ini menjawab satu pertanyaan:

> **Bagaimana state operasional SAM (mission, execution, approval, audit, evidence, idempotency) dipersist sehingga multiple mission dapat hidup bersamaan, tidak saling overwrite, dan survive restart — dengan domain yang tidak bergantung pada database?**

---

## Problem Statement

Rekognisi audit 2026-08-13 menunjukkan runtime `MissionUXService`:
- memegang state sebagai **instance singleton**: `self._state`, `self._request`, `self._plan`, `self._audit`, `self._last_result`, `self._idem`;
- source-of-truth adalah **variabel in-memory**, bukan penyimpanan per-entity;
- store yang ada (`MissionStore` JSON / `PostgresMissionStore`) menyimpan **satu blob** (`save(payload)`) — bukan per-entity;
- setelah `kill` + `restart`, state hilang (`/ux/state` → "belum ada mission").

Akibatnya: multi-mission tidak mungkin (satu global state); truth tidak survive restart; tidak ada isolasi per-entity. Ini bertentangan dengan ADR-008 §3 (Recovery: Session→Snapshot→Checkpoint→Replay, SAFE_MODE) dan kebutuhan M12-001.

---

## Decision

**DIPUTUSKAN:** SAM mengadopsi **Repository Pattern** untuk seluruh state operasional yang wajib durable, mengikuti alur Clean Architecture:

```text
Domain (entity, port interface)
   ↓
Repository Port (interface — domain-owned)
   ↓
Application Service (menggunakan port, tidak tahu backend)
   ↓
Repository Implementation (PostgreSQL)
   ↓
PostgreSQL
```

1. **Enam repository port**: `MissionRepository`, `ExecutionRepository`, `ApprovalRepository`, `AuditRepository`, `EvidenceRepository`, `IdempotencyRepository`. Domain mendefinisikan interface; implementasi (PostgreSQL) ada di lapisan infrastructure.

2. **Domain tidak bergantung pada PostgreSQL.** Service hanya melihat interface repository. Pilihan backend (PG/JSON/in-memory) adalah implementasi terpisah yang boleh di-swap.

3. **State keyed per entity + mission**: sumber state bukan satu global `mission_state`. Setiap mission/execution/approval/audit/evidence/idempotency disimpan dan dibaca per-id (mission_id / execution_id / key). Mission A, B, C hidup bersamaan tanpa overwrite.

4. **PostgreSQL sebagai implementation default untuk produksi**; tetap boleh implementasi in-memory/JSON untuk test/dev (backward compatible).

5. **Tidak membuat executor kedua**, tidak menambah capability, tidak mengubah ADR-000/001/002/003/004/005/006/007/008.

---

## Rationale

- **ADR-008 §3/§4** menuntut recovery yang bisa mensnapshot & replay; tanpa per-entity storage, recovery tidak bisa merekonstruksi per-mission.
- **Multi-mission** (M12-001 acceptance: Mission A/B/C tanpa overwrite) mustahil dengan satu global state; repository per-id menyelesaikannya.
- **Clean Architecture** (dipertahankan, aturan kerja M12 #7): domain definitions port, infrastructure implements — swap-able, testable.
- Tidak melanggar ADR-008; malah mewujudkan kemampuannya.

---

## Alternatives Considered

- **A. Satu blob JSON/PG (status quo)**: sederhana tapi single-mission, tidak survive multi, tidak isolates. Ditolak (audit bukti: state hilang setelah restart, `docs/engineering/state/` kosong).
- **B. Repository Pattern per-entity (dipilih)**: memenuhi multi-mission, recovery, isolation; biaya: struktur baru + test.
- **C. Event Sourcing**: lebih kuat untuk audit replay tetapi heavyweight; tidak diperlukan untuk acceptance M12-001; ditunda (bisa dipertimbangkan ADR lanjutan).

---

## Consequences

**Positive**: multi-mission dukungan; truth survive restart; isolasi per-entity; domain bebas backend; testability tinggi.
**Negative**: migrasi dari singleton ke repository membutuhkan perombakan service; perlu mempertahankan kompatibilitas test yang ada (regresi M10).
**Netral**: PG menjadi implementation produksi; JSON/in-memory tetap untuk dev/test.

---

## Non-Goals

- Bukan design database skema rinci (milik Engineering).
- Bukan event sourcing penuh (ditunda).
- Bukan mengganti jalur eksekusi canonical.

---

## Related Documents

ADR-008 (§3 Recovery, §4 Workspace, §9 Approval Boundary, §12 Boundary), dokumen M12 Self-Preservation Order, Self-Preservation Reconnaissance Audit 2026-08-13.

---

## Validation

- Audit 1 (Problem Coverage) — LULUS: menjawab satu pertanyaan persistence foundation.
- Audit 2 (Alternative Coverage) — LULUS: alternatif dicek.
- Audit 3 (Foundation Compliance) — LULUS: tidak mengubah Constitution/Philosophy/Governance.
- Audit 4 (Specification Compliance) — LULUS: tidak mengubah Specification.
- Audit 5–7 (ADR-000..002 dsb Consistency) — LULUS: tidak mengubah ADR prior.
- Audit 8 (Final) — LULUS.
- STOP Condition: tidak membutuhkan mengubah Foundation/Specification/ADR prior; bukan kandidat lain → **STOP tidak aktif**.

---

## Review History

| Tanggal | Revisi | Perubahan |
|---|---|---|
| 2026-08-13 | 1.0 | Penulisan awal ADR-009 (M12-001 Durable State Repository Pattern) |
