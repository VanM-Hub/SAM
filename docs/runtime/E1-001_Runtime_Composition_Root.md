# E1-001 — Runtime Composition Root

**Document ID:** E1-001
**Title:** Runtime Composition Root
**Status:** Completed
**Date:** 2026-08-03
**Author:** Zara (Product Engineering, atas arahan Van)
**Audience:** Engineering
**Source of Authority (trace chain):** Constitution → Governance → Specification → ADR-000..ADR-007 → R4-001 → R4-002 → R5-001 → I0-001 → I1-001 → I2-001..I2-007 → P0-001 → P1-001..P1-008 → **E1-001**

---

# Executive Summary

E1-001 merakit **7 Reference Runtime Unit** menjadi **satu Runtime hidup** melalui sebuah **Composition Root** (`RuntimeBuilder` → `RuntimeRoot`). Ini **produk perakitan (assembly layer)** — **tidak menambah fitur**, **tidak mengubah arsitektur**, **tidak mengubah ADR**, **tidak mengubah compliance/baseline**, dan **tidak mengubah 7 unit runtime**.

Struktur ditulis ulang mengikuti skema package yang ditetapkan (bukan lagi struktur eksplorasi). Lokasi paket perakitan: **`src/sam/runtime_root/`** — di luar paket Reference Runtime (`sam/runtime/`), mengikuti Clean Architecture (Composition Root di luar domain Runtime) dan keputusan E1-000 yang disetujui Van.

---

## 1. Lokasi & Package

**Package:** `src/sam/runtime_root/` (lapisan perakitan, di luar `sam/runtime/`).

Tidak dibuat: `runtime/composition`, `runtime/bootstrap`, `runtime/application`, `runtime/runtime_root`.

Struktur (skema TASK + E1-002):

```
src/sam/runtime_root/
├── __init__.py              # Public API E1-001 + E1-002
├── __main__.py              # CLI: python -m sam.runtime_root (E1-002)
├── runtime_builder.py       # RuntimeBuilder — composition root
├── runtime_container.py     # RuntimeContainer — immutable, tepat 7 dependency
├── runtime_root.py          # RuntimeRoot — public API
├── lifecycle.py             # RuntimeLifecycle + RuntimeState
├── health.py                # RuntimeHealth + HealthStatus
├── exceptions.py            # RuntimeCompositionError + subclass
├── interfaces.py            # UnitFactory, HealthProvider, UnitRegistry
└── main.py                  # create_runtime/run_runtime/shutdown_runtime (E1-002)
```

---

## 2. Komponen

### 2.1 RuntimeBuilder (Composition Root)

- **instantiate** — membuat tepat satu instance per unit, dalam urutan kanonik.
- **wire** — menyusun pipeline (tidak ada shortcut).
- **validate** — memvalidasi 7 unit tersedia, 0 duplicate/missing, 0 cycle, pipeline valid, authority valid, health valid.
- **build** — menghasilkan `RuntimeContainer` immutable + `RuntimeRoot` (BUILT).
- **TIDAK menjalankan Runtime.**

Behavior singleton-builder: objek `RuntimeBuilder` dapat dipakai ulang; tiap `build()` menghasilkan instance baru yang identik strukturnya (`build_count` bertambah).

### 2.2 RuntimeContainer (Immutable, tepat 7 dependency)

Memegang **tepat tujuh** dependency:
`CitizenHost, CapabilityManager, DiscoveryResolver, ContractEnforcer, ApprovalCoordinator, ExecutionScheduler, AuditRecorder`.

- Dibatasi `__slots__` ke 7 atribut + `_frozen`; `__setattr__` menolak mutasi setelah konstruksi.
- **Tidak boleh ada dependency kedelapan** — konstruktor membuang `RuntimeCompositionError` jika ada unit missing/extra.

### 2.3 RuntimeRoot (Public API)

```
RuntimeRoot.build()         # buat/rebuild runtime fresh (aliases RuntimeBuilder)
RuntimeRoot.start()         # deterministic startup
RuntimeRoot.stop()          # deterministic shutdown
RuntimeRoot.restart()       # stop (bila perlu) + build fresh + start
RuntimeRoot.health()        # aggregate health (Healthy/Degraded/Failed)
RuntimeRoot.container()     # immutable seven-unit container
RuntimeRoot.is_running()    # True iff STARTED
```

### 2.4 Lifecycle (deterministik)

```
CREATED -> BUILT -> STARTED -> STOPPED -> DISPOSED
```

Transisi dijaga tabel deterministik; path invalid memicu `LifecycleCompositionError` (subclass `RuntimeCompositionError`).

### 2.5 Wiring (pipeline, no shortcut)

```
CitizenHost
  ↓
CapabilityManager
  ↓
DiscoveryResolver
  ↓
ContractEnforcer
  ↓
ApprovalCoordinator
  ↓
ExecutionScheduler
  ↓
AuditRecorder
```

`PIPELINE` (7 id) dan `CANONICAL_EDGES` (6 edge hilir berurutan) adalah encode persis rantai R5-001 S2 / I1-001 §3.

### 2.6 Dependency Rule

- Import hanya `shared`, `contracts`, `runtime.*`.
- Unit **tidak saling instantiate**.
- **No global singleton**, **no service locator** — builder yang membuat semuanya (lazy factory).
- Unit tidak pernah mengimpor `runtime_root` (arah: builder → unit).

### 2.7 Validation (saat build)

`RuntimeBuilder._validate_structure` + `_assert_acyclic` memeriksa:
1. 7 unit tersedia
2. 0 duplicate
3. 0 missing
4. 0 cycle (DFS)
5. authority chain valid (hanya 6 edge kanonik — no skip/lateral)
6. pipeline valid (linear DAG, root = citizen_host)
7. health valid (tiap unit punya `get_health` callable)

Jika gagal: **`RuntimeCompositionError`**.

### 2.8 Health (aggregate 7 unit)

```
7 unit → RuntimeHealth → status: Healthy | Degraded | Failed
```

Aturan deterministik:
- semua unit Healthy → **Healthy**
- ada unit Failed/unavailable → **Failed**
- selain itu (ada Degraded) → **Degraded**

Format health unit heterogen (string/dict) dinormalkan; aggregator tidak memaksa nilai yang tidak dilaporkan unit.

> Catatan aktual: setelah `start()`, 5 unit (citizen_host, capability_manager, approval_coordinator, execution_scheduler, audit_recorder) Healthy; **discovery_resolver & contract_enforcer** tidak punya `initialize()` dan secara internal tetap melaporkan `unavailable` → aggregate **Failed**. Ini agregasi jujur; E1-001 tidak mengubah unit tersebut (STOP condition: 7 unit tak boleh disentuh).

### 2.9 Exceptions

```
RuntimeCompositionError         # base (TASK)
  ├── CompositionValidationError
  ├── DependencyGraphError
  └── LifecycleCompositionError
```

Alias backward-compatible: `CompositionException == RuntimeCompositionError`, `CompositionDefinitionError == RuntimeCompositionError`.

---

## 3. Test

| File | Scope |
|---|---|
| `tests/runtime/runtime_root/test_composition.py` | E1-001: builds, starts, stops, health aggregate, dependency graph, pipeline, determinism, multiple build, restart, singleton-builder |
| `tests/runtime/runtime_root/test_integration.py` | E1-002 executable: create/run/shutdown_runtime + CLI smoke |

**Total: 40 test hijau.**

Cakupan yang diminta TASK diverifikasi:
- runtime builds / starts / stops ✅
- health aggregate ✅
- dependency graph ✅
- pipeline (no shortcut) ✅
- determinism (build 100x identik) ✅
- multiple build (fresh instances) ✅
- restart ✅
- singleton builder behavior (build_count) ✅

---

# Audit 1 — Architecture Audit

**Bukti:** Composition Root berada di `src/sam/runtime_root/` (assembly layer, di luar domain Runtime). Tidak ada change pada R4-001 (arsitektur), R4-002 (desain), R5-001 (engineering), I0-001 (blueprint), I1-001 (skeleton), ADR-000..007, atau foundation/spec. 7 unit tidak diubah; wiring hanya di lapisan composition (I1-001 IR4 no lateral). Import hanya `shared`/`contracts`/`runtime.*`.

**Hasil:** ✅ LULUS

---

# Audit 2 — Implementation Audit

**Bukti:** `RuntimeBuilder` instantiate+wire+validate+build, tidak run. `RuntimeContainer` immutable, tepat 7 dependency (__slots__ + guard extra/missing). `RuntimeRoot` public API lengkap (build/start/stop/restart/health/container/is_running). Lifecycle `CREATED→BUILT→STARTED→STOPPED→DISPOSED` deterministik. Exception base `RuntimeCompositionError`. Semua file `runtime_root/*.py` ada sesuai skema. Import relatif valid; build 100x identik.

**Hasil:** ✅ LULUS

---

# Audit 3 — Compliance Audit

**Bukti (empiris):** `BaselineBackedSessionRunner` → **total evidence 99, deviating 0, verdict A**. Paket di luar `src/sam/runtime/` (yang dipindai checker) → L0-11 dan seluruh checker lain tetap hijau. Tidak ada perubahan compliance/baseline (P1-001..P1-008).

**Hasil:** ✅ LULUS — 99/99 HIJAU, verdict A, 0 deviation.

---

# Audit 4 — Integration Audit

**Bukti:** Full runtime suite `tests/runtime/` = **917 passed**. Full project suite (excl legacy) = **15,641 passed**. 3 failure (`test_sprint25.py` x2, `test_legacy_failure_injection.py`) terkonfirmasi **pre-existing** — gagal juga di HEAD bersih `fe2442c` (verifikasi via git stash), tidak menyentuh `runtime_root`/`sam.runtime`, tidak diubah oleh pekerjaan ini → **0 regression**.

**Hasil:** ✅ LULUS

---

# Audit 5 — Determinism Audit

**Bukti:** `test_build_100_times_identical_structure` — build 100x → structur identik (dependency_ids sama, jumlah unit sama, state BUILT). `test_multiple_build_produces_fresh_instances` — tiap build instance baru. Lifecycle deterministik (urutan tetap). CLI output deterministic tanpa timestamp/random. Tanpa network.

**Hasil:** ✅ LULUS

---

# Audit 6 — Dependency Audit

**Bukti:** Tidak ada modul unit yang mengimpor `runtime_root` (arah satu arah). Factory lazy import (import unit hanya di dalam closure factory) → tidak ada import cycle pada import awal. `RuntimeRoot.build/restart` memakai lazy import `RuntimeBuilder` untuk memutus siklus antar modul paket. Tidak ada import lateral unit. No global singleton, no service locator.

**Hasil:** ✅ LULUS

---

# Audit 7 — Health Audit

**Bukti:** `RuntimeHealth` mengagregasi 7 unit; status `Healthy/Degraded/Failed`; normalisasi format heterogen (string/dict); aturan aggregate deterministik; `health_summary()` menyediakan per-unit map. Konteks aktual: 5/7 Healthy, DR+CE unavailable → Failed (agregasi jujur, unit tak diubah). Driver `_drive_initialize` memanggil `initialize()` unit yang punya, urut pipeline.

**Hasil:** ✅ LULUS (perilaku agregasi jujur terverifikasi oleh test `test_health_aggregate_*`)

---

# Audit 8 — Final Certification

**Bukti:** Semua Audit 1–7 LULUS. 99 compliance hijau verdict A. 40 test baru hijau. `python -m sam.runtime_root` exit 0 dengan urutan build→start→health→stop→dispose. 0 regression. STOP condition terpenuhi (7 unit, arsitektur, ADR, compliance, baseline, skeleton tak diubah).

**Hasil:** ✅ **LULUS — VERDICT A-CERTIFIED**

---

# STATUS

**SELESAI — E1-001 Runtime Composition Root terimplementasi di `src/sam/runtime_root/` sebagai assembly layer (Composition Root), tanpa mengubah 7 unit, arsitektur, ADR, compliance, atau baseline. 99/99 compliance HIJAU, 40 test hijau, 0 regression.**

---
