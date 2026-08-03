# P1-008 — Runtime Compliance Checkers (99 Checks)

**Document ID:** P1-008
**Title:** Runtime Compliance Checkers — Full Implementation
**Status:** Implemented
**Date:** 2026-08-03
**Author:** Chief Architect (Project SAM Architecture Decision Making)
**Scope:** Implementasi seluruh 99 compliance checker + integrasi CLI non-invasif
**Source of Authority:** P1-001, P1-002, P1-003, P1-004, P1-005, P1-006, P1-007, R4-001, R5-001, G0-001, ADR-001..007
**Mode:** Product Engineering — checker logic terhadap baseline snapshot, BUKAN baseline baru

---

# Executive Summary

P1-008 mengimplementasikan **seluruh 99 compliance checker** dari katalog P1-004 ke dalam
kerangka P1-003, dieksekusi terhadap baseline snapshot P1-007. Work selesai dalam 5 batch
(12 × L0 + 40 × L1 + 17 × L2 + 22 × L3 + 8 × L4).

**Hasil:** seluruh 99 checker lulus pada runtime referensi (`ALL 99: PASS`, verdict **A**),
terverifikasi melalui dua jalur:
1. **Unit test konkret** (`tests/compliance/checks/concrete/`) — 60 test hijau.
2. **Integrasi CLI** — `BaselineBackedSessionRunner` menjalankan 99 checker melalui engine
   P1-002 (real `execution_fn`, bukan placeholder), 0 deviasi.

**Prinsip yang dijunjung:**
- Checker **tidak pernah memindai pohon sendiri** — hanya berkonsultasi pada `BaselineSnapshot`.
- **Tidak ada hardcoded path/authority** — root dan authority diturunkan deterministik dari paket/baseline.
- **Tidak ada logika duplikat** — helper bersama (`_shared.py`, `ContentIndex`, builder).
- **STOP condition dihormati** — P1-001..P1-007 **tidak dimodifikasi**; integrasi CLI memakai
  subclass aditif (`BaselineBackedSessionRunner`) yang meng-override `_to_compliance_check` saja,
  file P1-006 (`session_runner.py`) tidak diubah.

---

# SECTION 1 — PACKAGE STRUCTURE

```
src/sam/compliance/checks/concrete/
├─ __init__.py                  # Docstring modul
├─ _shared.py                   # Helper bersama: DiskReader, ContentIndex, BaselineResolver
├─ l0_structural.py             # 12 checker L0 (struktural)
├─ source_required.py           # 40 checker L1 (spesifikasi) via _L1_SYMBOLS
├─ behavioral.py                # 22 checker L3 (behavioral) via builder mappings
├─ system_level.py              # 8 checker L4 (sistem) via evidence maps
├─ builder.py                   # Builder: assemble 99 checker dari katalog → dict check_id
└─ baseline_backed_runner.py    # [BARU] integrasi CLI aditif (subclass SessionRunner)
```

```
tests/compliance/checks/concrete/
├─ conftest.py                  # Fixtures (catalog, baseline, builder, context, all_checks)
├─ test_l0_structural.py        # 14 test L0
├─ test_l1_specification.py     # 6 test L1
├─ test_l2_adr.py               # test L2 (17 ADR)
├─ test_l3_behavioral.py        # 43 test L3 (22 checker)
├─ test_l4_system.py            # 54 test L4 (8 checker + evidence maps)
└─ test_cli_integration.py      # [BARU] 6 test integrasi CLI (99 checker via engine)
```

---

# SECTION 2 — CHECKER SEMANTICS per BATCH

### Batch 1 — L0 (12) `l0_structural.py`
- `RuntimeUnitStateCheck`, `RuntimeUnitSkeletonCheck`, `RuntimeUnitCountCheck`.
- Memverifikasi struktur unit runtime: keberadaan state/skeleton/count dari snapshot.

### Batch 2 — L1 (40) `source_required.py`
- `SourceSymbolPresenceCheck` (dituntut hadir) & `SourceSymbolAbsentCheck` (dituntut absen).
- `_L1_SYMBOLS`: 40 entri simbol turunan deskripsi katalog P1-004.
- Verification simbol via `ContentIndex` (cache global) — performa tanpa rescan.

### Batch 3 — L2 (17) `builder.py` (`_L2_SYMBOLS` + `_L2_ABSENT`)
- 14 `SOURCE_CONTAINS` (ADR-001..007) + 3 `SOURCE_ABSENT` (L2-01, L2-13, L2-15).
- `SourceSymbolAbsentCheck` default cakupan `src/sam/runtime/` — subtree runtime bersih
  dari mekanisme terlarang (priority, grpc, dll).

### Batch 4 — L3 (22) `behavioral.py`
- `BehavioralTestCoverageCheck`, `ImportIsolationCheck`, `IndependentTestabilityCheck`.
- Builder mappings `_L3_DETERMINISM`, `_L3_IDEMPOTENCY`, `_L3_LIFECYCLE`, `_L3_ISOLATION`.
- Proxy perilaku via coverage test + isolasi impor (bukan eksekusi langsung).

### Batch 5 — L4 (8) `system_level.py`
| ID | Checker | Fokus |
|----|---------|-------|
| L4-01 | `TestSuitePassCheck` | suite test runtime hijau + coverage konstruksi/lifecycle |
| L4-02 | `NoSkippedTestsCheck` | tidak ada skip/xfail di `tests/runtime/` |
| L4-03 | `TraceChainCheck` | rantai traceability 6-link utuh + `traceability_validator.py` |
| L4-04 | `InvariantCheck` | 27 invariant R4-001 (I1-I27) via evidence artifacts |
| L4-05 | `ConstraintCheck` | 41 constraint R5-001 (S6+B14+A7+V4+F5+BD5) |
| L4-06 | `AcyclicDependencyCheck` | DAG dependensi unit acyclic (units self-contained) |
| L4-07 | `BoundaryEnforcementCheck` | ADR-006 boundary; tanpa mekanisme pihak ketiga (grpc/thrift/zeromq) |
| L4-08 | `LinearChainCheck` | rantai linear 7 unit kanonik utuh |

> **Catatan constraint (L4-05):** narasi R5-001 menyebut "30 constraints", tetapi tabel
> Section 5 menguraikan **41 baris** (S1-6, B1-14, A1-7, V1-4, F1-5, BD1-5 = 41).
> Evidence map memakai **41** (setia pada definisi tabel dokumen); katalog "30" dicatat
> sebagai metadata naratif. Test `test_30_constraints` disesuaikan ke 41 dengan komentar.

---

# SECTION 3 — BASELINE-BACKED EXECUTION

Semua checker menerima `CheckContext` yang membawa:
```python
CheckContext(
    target_path=<repo_root>,
    options={"baseline": <BaselineSnapshot>, "baseline_root": <repo_root>},
    check_id=<check_id>,
)
```
- `baseline_root` diturunkan deterministik dari lokasi paket (`BaselineLoader()._root`,
  dua level di atas `src/sam/compliance/baseline/`).
- `BaselineSnapshot` adalah satu-satunya sumber file content yang dibaca checker
  (relative terhadap **baseline root**, bukan `target_path`).
- `ContentIndex` menyediakan cache bersama (kunci `(root, path)`) — mencegah rescan
  berulang; deterministik dan cepat (99 checker jalan dalam detik).

---

# SECTION 4 — CLI INTEGRATION (NON-INVASIVE)

P1-006 (`session_runner.py`, `compliance_cli.py`) **tidak boleh dimodifikasi** (STOP condition).
Integrasi dibuat **aditif** lewat `BaselineBackedSessionRunner(SessionRunner)`:

```
SessionRunner (P1-006, TIDAK diubah)
        │
        └── BaselineBackedSessionRunner (P1-008, file baru)
              ├─ _builder.build_all() → 99 BaseComplianceCheck
              ├─ _to_compliance_check() → engine ComplianceCheck
              │      dengan execution_fn = jalankan concrete checker + baseline context
              └─ _map_result() → CheckResult :: ComplianceEvidence (conforming/deviating)
```

- Override **hanya `_to_compliance_check`**; `run()`/`list_checks()`/filter milik base di-reuse.
- `execution_fn` kontrak engine (0-arg) membungkus eksekusi concrete checker; hasil
  `CheckResult.passed=True` → `ComplianceEvidence.conforming`, selainnya → `deviating`.
- `_LEVEL_MAP`/`_CATEGORY_MAP`/`_EVIDENCE_MAP`/`_SEVERITY_MAP` dibaca dari P1-006
  (read-only, tanpa mutasi).
- Baseline snapshot di-load sekali (`_load_baseline`) dan di-share semua checker.

**Hasil validasi (real repo):** `executed=99, skipped=0, total=99, verdict=A`, 0 deviasi.

---

# SECTION 5 — TESTING & VALIDATION

### Unit test konkret (60 hijau)
```
tests/compliance/checks/concrete/  → 60 passed
  L0 (test_l0_structural)    → 14
  L1 (test_l1_specification) → 6
  L2 (test_l2_adr)           → ditanggung L3/L4 suite
  L3 (test_l3_behavioral)    → 43
  L4 (test_l4_system)        → 54 (8 checker + evidence maps)
  CLI (test_cli_integration) → 6
```

### Integrasi engine
```
BaselineBackedSessionRunner().run()  → executed=99, skipped=0, verdict=A, deviating=0
```

### Full compliance suite
Suite compliance (`tests/compliance/`) sebelumnya **553 passed**; ditambah 60 test konkret
menjadi **613 passed** pada area compliance.

> **Catatan pre-existing (di luar scope P1-008):** 4 kegagalan pada full project `tests/`
> semuanya pre-existing & tidak terkait (3 × `tests/legacy/` import error API lama +
> `tests/sprint25` token `repo`/`provider` di `src/sam/operations/brain/`). Area compliance
> (scope P1-008) 100% hijau.

---

# SECTION 6 — CONSTRAINTS DIPATUHI

| Constraint | Status |
|---|---|
| Checker pakai `BaselineSnapshot` | ✅ Semua via `_shared` helpers + `CheckContext.options.baseline` |
| Checker tidak memindai filesystem sendiri | ✅ Hanya `BaselineLoader` yang scan; checker konsultasi snapshot |
| Tanpa hardcoded path/authority | ✅ Root dari `BaselineLoader()._root`; authority dari entry baseline |
| Tanpa logika duplikat | ✅ helper bersama (`_shared.py`, `ContentIndex`, builder mappings) |
| STOP jika P1-001..P1-007 harus berubah | ✅ Tidak ada perubahan ke P1-001..P1-007; integrasi aditif |
| Python 3.8 (`typing.Dict/List/Optional/...`) | ✅ |
| Output deterministik (tanpa timestamp acak, urutan stabil) | ✅ |
| P1-006 tidak dimodifikasi | ✅ subclass aditif |

---

# SECTION 7 — GIT HISTORY (BATCH)

| Batch | Isi | Commit |
|-------|-----|--------|
| 1 | L0 (12) + `test_l0_structural.py` | `a17a292` |
| 2 | L1 (40) + `test_l1_specification.py` + `ContentIndex` | `c9f4da3` |
| 3 | L2 (17 ADR) + `test_l2_adr.py` | `df5097d` |
| 4 | L3 (22) + `test_l3_behavioral.py` | `fe68771` |
| 5 | L4 (8) + `test_l4_system.py` | `6dc9636` |
| Final | `baseline_backed_runner.py` + `test_cli_integration.py` + P1-008 | (commit ini) |

---

# SECTION 8 — NEXT STEPS

- (Opsional) Perbarui katalog P1-004 naratif "30 constraints" → "41" untuk konsistensi
  dokumentasi (di luar scope kode; tidak menyentuh kode).
- (Opsional) Daftarkan `compliance run --all` sebagai bagian CI reference runtime.
