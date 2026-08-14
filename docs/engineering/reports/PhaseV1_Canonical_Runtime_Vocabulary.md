# PHASE V1 — Canonical Runtime Vocabulary (RuntimeState + EvidenceType)

**Tanggal:** 2026-08-14
**Jenis:** Audit consumer + rencana canonical owner.
**Status:** ✅ **V1-EXEC-001 & V1-EXEC-002 DIEKSEKUSI** (commit `7d62a37`). Migration plan di bawah telah dijalankan.
**Cakupan:** `RuntimeState` dan `EvidenceType`.

---

## 1. RUNTIMESTATE

### 1.1 Definition (semua definisi di repo)

| # | Lokasi | Bentuk | Nilai | Klasifikasi |
|---|---|---|---|---|
| R1 | `contracts/runtime.py:8` | `str, Enum` | 12 nilai (INITIALIZING..SAFE_MODE) | 🔴 duplicate sejati |
| R2 | `runtime/state.py:8` | `str, Enum` | 12 nilai **IDENTIK** (INITIALIZING..SAFE_MODE) | 🔴 duplicate sejati |
| R3 | `runtime_root/lifecycle.py:21` | `str, Enum` | 5 nilai beda (CREATED/BUILT/STARTED/STOPPED/DISPOSED) | 🟢 bounded context (container lifecycle) |
| R4 | `runtime_kernel/runtime_state.py:8` | `dataclass` | state_id/state/previous_state/subsystem | 🟢 bounded context (kernel state record) |
| R5 | `autonomy_runtime/observation/models.py:37` | `dataclass` | state_id/observed_at/status/components... | 🟢 bounded context (observation snapshot) |
| R6 | `guardian/live/state.py:78` | `dataclass` | runtime_id/version/health/status/statistics... | 🟢 bounded context (ward guardian snapshot) |

> **Koreksi audit awal:** audit `850d5f0` menyebut RuntimeState "duplicate sejati 12 nilai identik". Yang benar: dari **6** definisi, hanya **R1 vs R2** yang duplicate sejati. R3–R6 = 4 bounded context berbeda (enum lifecycle vs 3 dataclass snapshot) — **jangan disatukan**.

### 1.2 Imports

| Definisi | Import oleh |
|---|---|
| R1 `contracts/runtime.py` | `contracts/__init__.py:5` (re-export `from .runtime import RuntimeState`) — **tidak ada consumer langsung** yang `from sam.contracts import RuntimeState` |
| R2 `runtime/state.py` | `runtime/__init__.py:3`, `runtime/bootstrap.py:10`, `runtime/coordinator.py:19`, `runtime/recovery.py:12`, `runtime/shutdown.py:11` |
| R3 `runtime_root/lifecycle.py` | `runtime_root/main.py:28`, `runtime_root/runtime_builder.py:171`, `runtime_root/runtime_root.py:38`, `runtime_root/__init__.py:44` |
| R4 `runtime_kernel/runtime_state.py` | `runtime_kernel/__init__.py` |
| R5 `autonomy_runtime/observation/models.py` | `autonomy_runtime/api/observation.py:12`, `autonomy_runtime/diagnostics/{engine,failure,health}.py`, `autonomy_runtime/observation/dependency.py`, `autonomy_runtime/readiness/analyzer.py` |
| R6 `guardian/live/state.py` | `guardian/live/{change_detector,conversation_sync,diff_engine,snapshot,validator,registry,synchronizer}.py` |

### 1.3 Consumers (pemakai nyata anggota enum 12 nilai)

Seluruh konsumen enum 12 nilai memakai **R2 (`runtime/state.py`)**:
- `runtime/bootstrap.py` → `BOOTSTRAPPING`, `READY`
- `runtime/coordinator.py` (19 ref) → `INITIALIZING`, `SAFE_MODE`, `READY`, `RUNNING`, `SHUTDOWN`, `CRASHED`, `DEGRADED`
- `runtime/recovery.py` (8 ref) → `RECOVERING`, `READY`, `SAFE_MODE`
- `runtime/shutdown.py` → `STOPPING`, `SHUTDOWN`
- Tests: `test_bootstrap.py`, `test_recovery.py`, `test_shutdown.py` — semua import `from sam.runtime.state import RuntimeState`

**R1 (`contracts/runtime.py`) punya 0 consumer langsung.** Hanya di-re-export `contracts/__init__.py`, tapi tidak ada kode/tests yang `from sam.contracts import RuntimeState`. `test_contracts.py` justru import `from sam.runtime.state import RuntimeState` (bukan dari contracts).

### 1.4 Serialization/storage impact

- R1/R2 = `str, Enum` murni, tidak ada method custom. Tidak ada yang memanggil `.value`/`.to_dict` pada enum ini secara langsung di jalur aktif (state dipakai sebagai perbandingan equality, bukan disimpan).
- R3 (lifecycle) dipakai `runtime_root` sebagai kontrol alur; tidak diserialize ke DB/JSON.
- R4/R5/R6 (dataclass) punya `to_dict`/`as_dict` masing-masing — independen, bounded context sendiri.

### 1.5 Runtime impact (jalur aktif)

- **R2 = enum yang benar-benar hidup** di runtime coordinator/bootstrap/recovery/shutdown.
- **R1 = mati** (dead duplicate) — hanya re-export tanpa consumer.

### 1.6 Tests

| Test | Memakai |
|---|---|
| `tests/unit/test_contracts.py` | `from sam.runtime.state import RuntimeState` (R2) — 27 ref |
| `tests/unit/test_bootstrap.py` | R2 — 15 ref |
| `tests/unit/test_recovery.py` | R2 — 7 ref |
| `tests/unit/test_shutdown.py` | R2 — 8 ref |
| `tests/runtime/runtime_root/test_composition.py`, `test_integration.py` | R3 (lifecycle) |
| `tests/sprint44/test_runtime_sync.py` | R6 (guardian) |

### 1.7 Canonical candidate

**`runtime/state.py` (R2)** = canonical owner. Alasan:
- satu-satunya enum 12 nilai yang **dipakai aktif** (4 modul + 4 file test).
- `contracts/runtime.py` (R1) = dead duplicate, 0 consumer langsung.

R3–R6 **bukan** bagian dari keputusan ini — mereka bounded context berbeda dan tetap hidup.

### 1.8 Migration plan — ✅ DIEKSEKUSI (commit `7d62a37`)

1. `contracts/runtime.py` diubah menjadi **compatibility shim** (re-export `from sam.runtime.state import RuntimeState`), bukan definisi kedua — `sam.contracts.RuntimeState` tetap valid.
2. `contracts/__init__.py` tetap `from .runtime import RuntimeState` (menunjuk ke shim).
3. Verifikasi 0 consumer `from sam.contracts import RuntimeState` (statis + dinamis) — terkonfirmasi. Tidak ada import dinamis (getattr/importlib) yang relevan.
4. Regression unit+runtime: **lulus.**

Hasil verifikasi:
- `RuntimeState is sam.contracts.RuntimeState` → **True** (satu definisi).
- `sam.runtime.state.RuntimeState` = satusatunya canonical.

> **Catatan arsitektural:** R1 hidup di `contracts/` (layer authority), R2 di `runtime/` (layer implementasi). Secara semantik, "RuntimeState 12 fase" adalah **kontrak runtime**, bukan kontrak antar-boundary seperti Mission/DOS. Maka home-nya adalah `runtime/state.py`. Ini selaras aturan baru "Folder ≠ Semantic Identity" — yang menentukan owner = semantic ownership, bukan nama folder `contracts`.

---

## 2. EVIDENCETYPE

### 2.1 Definition (semua definisi di repo)

| # | Lokasi | Bentuk | Anggota | Klasifikasi |
|---|---|---|---|---|
| E1 | `compliance/catalog/models.py:45` | `Enum` | 10 (FILE_EXISTS..TRACE_CHAIN) | 🔴 duplicate sejati |
| E2 | `compliance/models/evidence_type.py:6` | `Enum` + helper `from_str`/`__str__` | 10 **IDENTIK** | 🔴 duplicate sejati |
| E3 | `evidence/models.py:10` | `str, Enum` | 15 beda (HEALTH_CHECK..CUSTOM, lowercase) | 🟢 bounded context (operational evidence) |

> **Koreksi audit awal:** audit `850d5f0` menyebut EvidenceType "7 vs 10 anggota". Itu **keliru** — artefak truncation scan awal. Faktanya **E1 dan E2 keduanya 10 anggota identik** (FILE_EXISTS, FILE_ABSENT, SOURCE_CONTAINS, SOURCE_ABSENT, TEST_PASS, TEST_COUNT, IMPORT_LEGAL, IMPORT_ILLEGAL, LIFECYCLE_VALID, TRACE_CHAIN). E2 hanya menambah helper `from_str()` + `__str__()`.

### 2.2 Imports

| Definisi | Import oleh |
|---|---|
| E1 `compliance/catalog/models.py` | `compliance/manifest/loader.py:21` (`from ..catalog.models import CheckerClass, EvidenceType`) |
| E2 `compliance/models/evidence_type.py` | 12 file: `checks/_placeholders.py`, `checks/base/base_check.py`, `checks/concrete/baseline_backed_runner.py`, `checks/concrete/builder.py`, `checks/evidence/__init__.py`, `checks/factory/__init__.py`, `cli/session_runner.py`, `engine/runner.py`, `manifest/entry.py`, `models/check_model.py`, `models/evidence.py` |
| E3 `evidence/models.py` | `evidence/__init__.py`, `evidence/store.py` (jalur operational, bukan compliance) |

### 2.3 Consumers (pemakai anggota enum)

- **E1** dipakai 1 file (`manifest/loader.py`) untuk map `EvidenceType → CheckerClass`.
- **E2** dipakai 12 file (checks builder/runner/session/cli/engine/model).
- **3 anggota tambahan** (`IMPORT_ILLEGAL`, `LIFECYCLE_VALID`, `TRACE_CHAIN`) dipakai aktif di: `checks/_placeholders.py`, `checks/concrete/builder.py`, `cli/session_runner.py`, `manifest/loader.py`, + 5 file test compliance.

> **Kesimpulan soal "3 anggota tambahan":** ketiganya **canonical** — dipakai nyata oleh checks builder, session runner, manifest loader, dan tests (bukan konsep yang harus dipindah ke bounded context lain).

### 2.4 Serialization/storage impact

- E1/E2 diserialize via `.value` di: `catalog/models.py:159`, `base_check.py:150`, `builder.py:197`, `check_model.py:68`, `evidence.py:103`, `console_reporter.py:123`.
- Keduanya `Enum` dengan nilai string sama, jadi `.value` identik → **aman untuk disatukan tanpa perubahan format serialisasi**.
- E3 (`str, Enum` operational, 15 nilai) = domain berbeda, tidak bersentuhan.

### 2.5 Runtime impact (jalur aktif)

- **E2 = enum yang benar-benar hidup** (12 file consumer, seluruh jalur checks → builder → session runner → engine).
- **E1 = duplikat yang hanya dipakai `manifest/loader.py`** — 1 file, dan file itu juga butuh `CheckerClass` dari `catalog`.

### 2.6 Tests

| Test | Memakai |
|---|---|
| `tests/compliance/checks/test_determinism.py`, `test_execution.py`, `test_extensibility.py`, `test_inheritance.py` | E2 (via `from ...models.evidence_type import EvidenceType`) — memakai `LIFECYCLE_VALID`, `IMPORT_ILLEGAL`, `TRACE_CHAIN` |
| (E1) | tidak ada test langsung yang import dari catalog untuk EvidenceType |

### 2.7 Canonical candidate

**`compliance/models/evidence_type.py` (E2)** = canonical owner. Alasan:
- dipakai 12 file (vs E1 hanya 1).
- punya helper `from_str()`/`__str__()` yang E1 tidak punya.
- 3 anggota tambahan sudah canonical (dipakai aktif).

E3 (`evidence/models.py`) = bounded context berbeda (operational evidence, 15 nilai lowercase) — **jangan disatukan**.

### 2.8 Migration plan — ✅ DIEKSEKUSI (commit `7d62a37`)

1. `compliance/manifest/loader.py` diarahkan import `EvidenceType` dari `sam.compliance.models.evidence_type` (E2); `CheckerClass` tetap dari `..catalog.models`.
2. `catalog/models.py` tidak lagi mendefinisikan `EvidenceType` sendiri — import dari canonical (`from ..models.evidence_type import EvidenceType`) untuk field `CheckMetadata.evidence_type`. `CheckMetadata`/`CheckerClass`/`CheckAuthority` tetap di catalog (domain catalog yang sah).
3. Verifikasi `from_str()` helper tersedia (E2 sudah menyediakan).
4. Run suite compliance — **lulus** (masuk 4417 passed).

Verifikasi:
- `catalog.models.EvidenceType is models.evidence_type.EvidenceType` → **True**.
- Tidak ada consumer yang import `EvidenceType` dari `catalog.models` tersisa.

Catatan lint: `auto`/`Optional` yang sudah tidak terpakai di `catalog/models.py` ikut dibersihkan (pre-existing unused).

---

## Ringkasan keputusan PHASE V1

| Konsep | Canonical owner | Duplicate yang dihapus | Bounded context (tetap) |
|---|---|---|---|
| `RuntimeState` | `runtime/state.py` (R2) | `contracts/runtime.py` (R1, dead) | lifecycle/kernel/observation/guardian (R3–R6) |
| `EvidenceType` | `compliance/models/evidence_type.py` (E2) | `catalog/models.py` EvidenceType (E1) | `evidence/models.py` operational (E3) |

**Status:** ✅ **V1-EXEC-001 & V1-EXEC-002 selesai** (commit `7d62a37`).

**Acceptance criteria V1 — TERPENUHI:**
- `RuntimeState` → 1 canonical (`runtime/state.py`), 0 duplicate (contracts jadi shim; identity verified).
- Compliance `EvidenceType` → 1 canonical (`models/evidence_type.py`), semua consumer pakai canonical (identity verified).
- Operational `EvidenceType` (`evidence/models.py`, 15 nilai) → tetap terisolasi, tidak dipaksa.
- Bounded `RuntimeState` (lifecycle/kernel/observation/guardian) → tetap terisolasi, tidak dipaksa.
- Regression `unit`+`runtime`+`compliance`: **4417 passed, 1 skipped**. Ruff clean.

**Prinsip dipertahankan:** 5113 classes & 526 collisions tidak dipangkas semua — hanya menghilangkan semantic ambiguity yang terbukti nyata (2 duplicate sejati). Folder ≠ Semantic Identity = aturan tetap.
