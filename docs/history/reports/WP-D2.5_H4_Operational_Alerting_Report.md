# WP-D2.5 — H4 Operational Alerting — Engineering Evidence

**Program:** D (MISSION-2D — Production Readiness)
**Phase:** EA-002 — Production Readiness Implementation
**Priority:** P5 · **Gap:** H4 Operational Alerting
**Type:** Working Report (evidence) → `reports/`
**Date:** 2026-08-08
**Status:** ✅ COMPLETE (menunggu Verdict Lead Engineer)

---

## Objective (ruang lingkup implementasi)

Menutup Gap H4 sesuai EA-001-004 (D4-G1, **High**): **"Tidak ada alerting/notification aktif — platform mengobservasi kondisi kritis (Observation layer) tetapi TIDAK memberi tahu operator."**

1. **AlertPolicy** — kebijakan naik/turun alert berdasar severity threshold & kanal tujuan.
2. **AlertRecord** — satu alert operational immutable (payload, tanpa rahasia).
3. **AlertDispatcher** — orkestrasi record → policy → router → audit (jalur masuk tunggal).
4. **AlertRouter + AlertStore** — routing dengan **dedup fingerprint**, retensi ring buffer, & **status lifecycle** (open/acknowledged/resolved).
5. **AlertAuditLog** — jejak metadata (tanpa payload state).
6. Menjaga constraint EA-002: **tidak melakukan efek eksternal, tidak ubah runtime existing**.

---

## Gap yang Diperbaiki (H4)

Assessment EA-001-004 menemukan:
- Observability layer kuat (M3): telemetry, 273 observation tests, `platform_health` (C9), `operational_learning` (C10).
- Health & metrics endpoint tersedia (CLI/API/runtime_service).
- **Tetapi TIDAK ada alerting aktif** (D4-G1, **High**): platform tahu kondisi buruk tapi **tidak mengirim alert keluar** (read-only observe).
- Tambahan (Medium, di luar scope H4): D4-G2 aggregator health terpusat, D4-G3 metrics standard, D4-G4 log terpusat.

**Boundary (tumpang tindih dicegah):**
- `execution/runtime/alert_engine.py` + `alerts.py` = evaluasi rule pada **metric eksekusi** (threshold-based, execution domain).
- `operations/notification.py` + `core/notification.py` = notifikasi **mission/approval/execution** + model pydantic + store.
- Keduanya **TIDAK** menyediakan: agregasi kondisi kritis **lintas subsystem** menjadi alert stream terpusat dengan **kebijakan & kanal tujuan** + **dedup** + **lifecycle acknowledge/resolve**.

→ H4 = **Operational Alerting layer** (agregasi lintas-subsystem), komplementer & stand-alone terhadap keduanya, tidak menyentuh keduanya (constraint EA-002).

---

## Desain (konservatif terhadap constraint EA-002)

Modul **`src/sam/operational_alerting/`** dibangun sebagai **capability baru stand-alone** (pola konsisten H2/H3):

| File | Peran |
|---|---|
| `state.py` | DTO immutable (ADR-023): `AlertSeverity`, `AlertStatus`, `AlertChannel`, `AlertRecord`, `AlertPolicy` |
| `policy.py` | `AlertPolicyEvaluator` + `AlertRoutingDecision` — keputusan naik/drop & kanal tujuan |
| `router.py` | `AlertRouter` + `AlertStore` — dedup fingerprint, ring buffer, acknowledge/resolve |
| `dispatcher.py` | `AlertDispatcher` — orkestrasi record → policy → router → audit |
| `audit.py` | `AlertAuditLog` — jejak metadata alert events |

**Keputusan engineering:**
- **Tidak ada efek eksternal** — kanal adalah label (`console`/`log`/`operator`/`notification_center`); pengiriman nyata (email/SMS/webhook) adalah tanggung jawab sink eksternal di luar capability ini. Ini konsisten ADR-000 (deployment topology) dan menjaga production-readiness tanpa menambah ketergantungan eksternal.
- **Dedup fingerprint** — SHA-256 dari representasi kanonik title+severity+source; alert identik yang masih OPEN tidak di-dispatch ulang (anti spam).
- **Lifecycle** — OPEN → ACKNOWLEDGED → RESOLVED; audit mencatat setiap transisi.
- **Ring buffer** — memori terbatas (default 200 store, 500 audit).
- **DTO immutable** (ADR-023) untuk payload; status mutable dipisah di store.

---

## Evidence Suite (otomatis, bagian CI integration)

**`tests/integration/test_operational_alerting.py`** — 25 test (in-process, murni deterministik):

| Area | # Test | Cakupan |
|---|---|---|
| Record | 4 | fingerprint deterministik, normalisasi severity, severity rank, tanpa rahasia |
| Policy | 5 | default min-warning, route critical, drop below threshold, disabled drop, threshold override |
| Router | 6 | route dispatch, acknowledge, resolve, unknown false, ring buffer, open/critical count |
| Dispatcher | 7 | emit routes, drop below policy, dedup duplicate, new after resolve, trigger, audit events |
| Audit | 3 | tanpa payload, ring buffer, by-event/failures |
| Round-trip | 1 | health turun → alert critical → operator acknowledge → kondisi pulih → resolve → audit siklus penuh |

---

## Bukti Verifikasi Nyata

| Uji | Hasil |
|---|---|
| `import sam.operational_alerting` + API publik | ✅ OK (14 exports) |
| `tests/integration/test_operational_alerting.py` | ✅ 25 passed |
| Integration suite penuh `tests/integration/` | ✅ 158 passed |
| Baseline CI scope (unit + runtimes + observation) | ✅ 4290 passed, 1 skipped, 2 xfailed |

**Tidak ada regression.** `runtime_kernel`, `execution_runtime`, `operations/notification.py`, `core/notification.py`, `execution/runtime/alert_engine.py` — seluruhnya tidak diubah.

---

## Compliance

- Foundation: tidak diubah ✅
- Constitution: tidak diubah ✅
- Governance: tidak diubah ✅
- Accepted ADR: tetap berlaku ✅ (ADR-023 Immutable DTO; ADR-000 topology)
- Runtime konstitusional baru: tidak ditambah ✅
- Responsibility runtime: tidak diubah ✅ (Operational Alerting = capability baru stand-alone)
- Tidak melakukan efek eksternal (network/host) ✅
- Tanpa rahasia/credential di payload ✅ (audit metadata-only)

---

## Status

H4 **Operational Alerting** terimplementasi, ter-verifikasi, ter-test. **Dengan ini kelima High gap Program D (H1, H5, H2, H3, H4) tuntas (EA-002).** EA-002 Production Readiness Implementation kini **selesai** menunggu Verdict Lead Engineer.

*— Engineering evidence WP-D2.5 (H4). Menutup seluruh gap High Program D.*
