# P1-005 — Runtime Compliance Manifest

**Document ID:** P1-005  
**Title:** Runtime Compliance Manifest  
**Status:** Implemented  
**Date:** 2026-08-03  
**Author:** Chief Architect (Project SAM Architecture Decision Making)  
**Scope:** Manifest deterministik — satu-satunya sumber konfigurasi eksekusi  
**Source of Authority:** P1-001, P1-002, P1-003, P1-004  
**Mode:** Product Engineering — manifest metadata, BUKAN logic checker  

---

# Executive Summary

P1-005 mengimplementasikan **ComplianceManifest** — manifest deterministik yang menghubungkan:

- **Compliance Catalog (P1-004)** — apa saja check yang ada (99 checks)
- **Compliance Framework (P1-003)** — checker apa yang mengimplementasikan tiap check
- **Compliance Engine (P1-002)** — bagaimana check dieksekusi

Manifest menjadi **satu-satunya sumber konfigurasi eksekusi**. Tidak ada konfigurasi tersebar di dalam kode.

**Yang diimplementasikan:**
- `ManifestEntry` — frozen dataclass 10 field per entry
- `ComplianceManifest` — koleksi 99 entry + query API
- `ManifestLoader` — membangun manifest lengkap dari catalog
- `ManifestValidator` — verifikasi integritas manifest
- `ManifestSerializer` — serialisasi/deserialisasi lossless

**Yang BELUM diimplementasikan:**
- Logic checker individual (P1-005 = manifest metadata + integritas saja)

---

# SECTION 1 — PACKAGE STRUCTURE

```
src/sam/compliance/manifest/
├── __init__.py        # Public API
├── entry.py           # ManifestEntry
├── manifest.py        # ComplianceManifest + ManifestError
├── loader.py          # ManifestLoader
├── validator.py       # ManifestValidator + result/issue models
└── serializer.py      # ManifestSerializer
```

---

# SECTION 2 — MANIFEST ENTRY (10 FIELD)

| # | Field | Type | Wajib | Deskripsi |
|---|---|---|---|---|
| 1 | `check_id` | `str` | ✅ | Wajib cocok dengan catalog check_id |
| 2 | `enabled` | `bool` | ✅ | Ikut eksekusi atau tidak |
| 3 | `execution_order` | `int` | ✅ | Urutan eksekusi deterministik (rendah dulu) |
| 4 | `checker_class` | `str` | ✅ | Nama kelas checker P1-003 |
| 5 | `configuration` | `Dict` | ✅ | Konfigurasi khusus checker |
| 6 | `timeout` | `Optional[float]` | — | Timeout eksekusi (None = tanpa) |
| 7 | `retry_policy` | `str` | ✅ | none / once / adaptive |
| 8 | `severity` | `Optional[Severity]` | — | Override severity (None = pakai catalog) |
| 9 | `dependencies` | `List[str]` | — | Check yang harus jalan sebelum ini |
| 10 | `tags` | `List[str]` | — | Tag eksekusi |

Semua field runtut dengan spek P1-005: check_id, enabled, execution_order, checker_class, configuration, timeout, retry_policy, severity, dependencies, tags.

---

# SECTION 3 — API

| Method | Return | Deskripsi |
|---|---|---|
| `get(check_id)` | `Optional[ManifestEntry]` | Lookup by ID |
| `entries()` | `List[ManifestEntry]` | Semua entry, sorted oleh (order, id) |
| `enabled()` | `List[ManifestEntry]` | Hanya entry enabled |
| `disabled()` | `List[ManifestEntry]` | Hanya entry disabled |
| `ordered()` | `List[ManifestEntry]` | Topological order by dependency graph |
| `resolve_dependencies(id)` | `List[ManifestEntry]` | Transitive dependency set |
| `count()` / `__len__` | `int` | Jumlah entry |
| `check_ids()` | `List[str]` | Semua ID, sorted |
| `__contains__` / `__getitem__` | — | In/access support |

**ManifestLoader API:**
| Method | Return | Deskripsi |
|---|---|---|
| `load(overrides=None)` | `ComplianceManifest` | Bangun manifest 99 entry |

**ManifestValidator API:**
| Method | Return | Deskripsi |
|---|---|---|
| `validate(manifest)` | `ManifestValidationResult` | Verifikasi integritas |

**ManifestSerializer API:**
| Method | Return | Deskripsi |
|---|---|---|
| `serialize(manifest)` | `List[dict]` | Entry → dict list |
| `to_json(manifest, indent)` | `str` | Entry → JSON string |
| `deserialize(data)` | `ComplianceManifest` | dict list → manifest |
| `from_json(text)` | `ComplianceManifest` | JSON string → manifest |

---

# SECTION 4 — DESIGN DECISION: DEPENDENCY ORIGIN

**Pertanyaan desain:** dari mana `dependencies` entry berasal?

**Keputusan:** `dependencies` adalah konstrain urutan eksekusi dan **tidak** diturunkan otomatis dari `catalog.traceability`.

**Alasan:** `traceability` di P1-004 mendokumentasikan **relasi simetris** antar check (rantai traceability dokumentasi). Contoh: `L0-01.traceability = ['L0-02']` dan `L0-02.traceability = ['L0-01']` — resiprokal sah secara dokumentasi, TAPI membentuk **cycle** bila diperlakukan sebagai dependensi eksekusi terarah.

Karena rule P1-005 mensyaratkan "dependency graph acyclic" dan "tidak boleh cycle", dan kita **tidak boleh** mengubah P1-004 (STOP condition), maka:
- `dependencies` dideklarasikan eksplisit di manifest (via overrides atau manifest yang dipersist)
- Loader default menghasilkan manifest dengan dependencies kosong → graph acyclic by construction
- Validator tetap mampu mendeteksi cycle bila dependencies diinisialisasi dengan cycle

---

# SECTION 5 — VALIDATION RULES

ManifestValidator memverifikasi:

| Rule | Kategori | Deteksi |
|---|---|---|
| Seluruh 99 check muncul | `missing` | Catalog check tidak ada di manifest |
| Tidak ada duplikat | `duplicate` | Check muncul 2+ kali |
| Seluruh checker ada | `unknown_checker` | checker_class tidak dikenal P1-003 |
| Seluruh dependency valid | `unknown_dependency` | dependency menunjuk check tak dikenal |
| Tidak ada cycle | `cycle` | Dependency graph punya cycle (Kahn) |
| Tidak ada orphan | `orphan` | Manifest entry tidak ada di catalog |

**Hasil validasi:** `ManifestValidationResult` dengan:
- `.valid` — True jika tidak ada error-level issue
- `.has_errors` — kebalikan
- `.issues` — list `ManifestValidationIssue(category, message)`
- `.error_categories()` — kategori error unik

---

# SECTION 6 — STATISTICS

## 6.1 Entry Distribution (checker_class)

| Checker Class | Count |
|---|---|
| SourceContainsCheck | 58 |
| TestResultsCheck | 22 |
| FileExistsCheck | 10 |
| FileAbsentCheck | 3 |
| ImportIllegalCheck | 3 |
| SourceAbsentCheck | 2 |
| TraceabilityCheck | 1 |
| **TOTAL** | **99** |

## 6.2 Default State

| Properti | Nilai |
|---|---|
| Total entries | 99 |
| Enabled | 99 |
| Disabled | 0 |
| Dependencies | Kosong (by design) |
| execution_order | 0..98 (deterministik) |
| Graph | Acyclic |
| Validator result | valid=True, issues=0 |

---

# SECTION 7 — TEST RESULTS

| Test Module | Tests | Status |
|---|---|---|
| `test_completeness.py` | 10 | ✅ PASSED |
| `test_ordering.py` | 16 | ✅ PASSED |
| `test_serialization.py` | 12 | ✅ PASSED |
| `test_validation.py` | 8 | ✅ PASSED |
| `test_determinism.py` | 4 | ✅ PASSED |
| **TOTAL** | **50** | **50/50 PASSED** |

**Full project:** 1,413 tests (877 runtime + 189 presentation + 138 engine + 99 check framework + 60 catalog + 50 manifest), all PASSED.

---

# VALIDATION

## Audit 1 — Manifest Completeness

**Pertanyaan:** Apakah seluruh 99 check muncul tepat sekali?

| Check | Status |
|---|---|
| 99 entries total | ✅ |
| Semua catalog checks hadir | ✅ |
| Tidak ada missing | ✅ |
| Tidak ada duplicate | ✅ |
| Semua level (L0-L4) terwakili | ✅ |
| Semua entry punya checker_class | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 2 — Catalog Consistency

**Pertanyaan:** Apakah manifest konsisten dengan P1-004 catalog?

| Check | Status |
|---|---|
| Setiap manifest entry check_id ada di catalog | ✅ |
| Entries = catalog checks (99 = 99) | ✅ |
| Loader membangun dari catalog.list_all() | ✅ |
| Tidak ada entry di luar catalog (no orphan by default) | ✅ |
| Validator bind ke catalog sebagai source of truth | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 3 — Framework Compatibility

**Pertanyaan:** Apakah manifest kompatibel dengan P1-003 framework?

| Check | Status |
|---|---|
| Setiap checker_class dikenal P1-003 | ✅ |
| Loader memetakan evidence_type → checker class | ✅ |
| Validator mendeteksi unknown_checker | ✅ |
| to_config() reconstructible via CheckFactory | ✅ (via Configuration) |

**Hasil:** ✅ LULUS

---

## Audit 4 — Engine Compatibility

**Pertanyaan:** Apakah manifest kompatibel dengan P1-002 engine?

| Check | Status |
|---|---|
| ManifestEntry.enabled → engine skip/pilih | ✅ |
| execution_order → urutan eksekusi deterministik | ✅ |
| dependencies → ordering engine | ✅ |
| Severity/level/category konsisten enum engine | ✅ |
| Manifest output siap dikonsumsi engine | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 5 — Dependency Integrity

**Pertanyaan:** Apakah dependency graph acyclic dan tanpa orphan?

| Check | Status |
|---|---|
| Default manifest acyclic (by design) | ✅ |
| Validator mendeteksi cycle (Kahn) | ✅ |
| Validator mendeteksi unknown_dependency | ✅ |
| Validator mendeteksi orphan | ✅ |
| resolve_dependencies salah id → raises | ✅ |
| ordered() menghormati dependency | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 6 — Determinism

**Pertanyaan:** Apakah manifest deterministic?

| Check | Status |
|---|---|
| ordered() deterministik (idempotent) | ✅ |
| Tidak ada conditional ordering | ✅ |
| Tidak ada random ordering | ✅ |
| Tidak ada runtime mutation | ✅ |
| Serialisasi deterministik (sort_keys) | ✅ |
| Loader stateless (2 load = identik) | ✅ |
| ManifestEntry frozen | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 7 — Test Results

**Pertanyaan:** Apakah seluruh test lulus?

| Suite | Count | Status |
|---|---|---|
| Completeness | 10 | ✅ |
| Ordering | 16 | ✅ |
| Serialization | 12 | ✅ |
| Validation | 8 | ✅ |
| Determinism | 4 | ✅ |
| Full project | 1,413 | ✅ |

**Hasil:** ✅ LULUS — 50/50 manifest, 1,413/1,413 full project.

---

## Audit 8 — Final Certification

**Pertanyaan:** Apakah P1-005 siap?

| Criteria | Status |
|---|---|
| Manifest Completeness (A1) | ✅ |
| Catalog Consistency (A2) | ✅ |
| Framework Compatibility (A3) | ✅ |
| Engine Compatibility (A4) | ✅ |
| Dependency Integrity (A5) | ✅ |
| Determinism (A6) | ✅ |
| Test Results (A7) | ✅ |
| Final (A8) | ✅ |

**VERDICT:** ✅ LULUS — P1-005 siap. Manifest menjadi satu-satunya sumber konfigurasi eksekusi.

---

# STOP

STOP condition: **NOT ACTIVE.**

Tidak ada perubahan P1-001, P1-002, P1-003, atau P1-004 yang dibutuhkan. P1-005 adalah:
- Manifest deterministik — mendaftarkan seluruh 99 check
- Tidak mengimplementasikan logic checker (hanya konfigurasi)
- Tidak menambah, mengurangi, atau mengubah check ID
- Meng-extend P1-001+P1-002+P1-003+P1-004 tanpa modifikasi
