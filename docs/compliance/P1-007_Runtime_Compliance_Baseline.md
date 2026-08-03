# P1-007 — Runtime Compliance Baseline Snapshot

**Document ID:** P1-007  
**Title:** Runtime Compliance Baseline Snapshot  
**Status:** Implemented  
**Date:** 2026-08-03  
**Author:** Chief Architect (Project SAM Architecture Decision Making)  
**Scope:** Membuat satu baseline snapshot sebagai referensi seluruh compliance checker  
**Source of Authority:** P1-001, P1-002, P1-003, P1-004, P1-005, P1-006, seluruh baseline Project SAM  
**Mode:** Product Engineering — baseline inventory + indexing, BUKAN checker logic  

---

# Executive Summary

P1-007 membuat **satu baseline snapshot** yang menjadi **referensi tunggal** seluruh compliance checker. Setelah P1-007, seluruh checker membaca baseline yang sama — **tidak ada checker yang memiliki hardcoded path ataupun daftar file sendiri**.

**Yang diimplementasikan:**
- `BaselineSnapshot` — inventory immutable
- `BaselineEntry` — satu file terindeks (file id, logical id, document type, authority, checksum, relative path, traceability)
- `BaselineLoader` — scan deterministik pohon Project SAM
- `BaselineIndex` — index lookup cepat (file_id / logical_id / path / type / authority)
- `BaselineValidator` — validasi integritas
- `BaselineSerializer` — serialisasi JSON deterministik

**Hasil:** snapshot default **valid=True, 0 issues** — memindai 3,165 file (dokumen + source + test + package) dengan 11 kategori baseline yang wajib ada.

**Prinsip kunci:** loader adalah SATU-SATUNYA tempat yang tahu cara memetakan file → type/logical id. Setelah snapshot dibangun, checker tidak pernah memindai pohon sendiri — cukup konsultasi snapshot.

---

# SECTION 1 — PACKAGE STRUCTURE

```
src/sam/compliance/baseline/
├── __init__.py              # Public API
├── entry.py                 # BaselineEntry (frozen dataclass)
├── snapshot.py              # BaselineSnapshot + ManifestError
├── loader.py                # BaselineLoader
├── index.py                 # BaselineIndex
├── validator.py             # BaselineValidator + issue/result models
└── serializer.py            # BaselineSerializer
```

```
tests/compliance/baseline/
├── conftest.py              # Shared fixtures
├── test_load_completeness.py    # loading + 11 kategori coverage
├── test_index_lookup.py         # index + lookup + selection
├── test_serialization.py        # serialization + determinism + immutability
├── test_validation.py           # validation 5 kategori
└── test_determinism.py          # determinism
```

---

# SECTION 2 — BASELINE SNAPSHOT

`BaselineSnapshot` adalah inventory immutable. Setiap `BaselineEntry`:

| Field | Deskripsi |
|---|---|
| `file_id` | id stabil (`FID-<TYPE>-<NNN>`) |
| `logical_id` | nama logis (hash deterministik path — unik) |
| `document_type` | kategori baseline |
| `authority` | otoritas (CONSTITUTION, Specification, ADR, ...) |
| `checksum` | sha256 konten file |
| `relative_path` | path relatif repo (POSIX) |
| `traceability` | referensi file_id terkait |

**Immutabilitas:** `BaselineEntry` frozen dataclass; `BaselineSnapshot` menolak file_id duplikat saat konstruksi.

---

# SECTION 3 — SNAPSHOT STATISTICS

| Kategori | Jumlah |
|---|---|
| Foundation documents | 9 |
| Specification documents | 7 |
| ADR documents | 10 |
| Runtime documents | 13 |
| Engineering documents | 23 |
| Blueprint documents | 2 |
| Compliance documents | 6 |
| Architecture documents | 24 |
| Source tree (`src/sam/`) | 2,517 |
| Test tree (`tests/`) | 554 |
| Package tree (`pyproject.toml`, `README.md`) | 2 |
| **TOTAL** | **3,165** |

**11 kategori baseline** (dari spec P1-007) semua terpenuhi: Foundation, Specification, ADR, Runtime, Engineering, Blueprint, Compliance documents + Source tree, Test tree, Package tree.

---

# SECTION 4 — BASELINE INDEX

`BaselineIndex` membangun 5 map lookup sekali lalu melayani O(1):

| Lookup | Deskripsi |
|---|---|
| `by_file_id` | file_id → entry |
| `by_logical_id` | logical_id → entry |
| `by_path` | relative_path → entry |
| `by_type` | document_type → [entry] |
| `by_authority` | authority → [entry] |

Dibangun deterministik dari `snapshot.files()` (terurut file_id) → immutable setelah konstruksi.

---

# SECTION 5 — API

| Method | Deskripsi |
|---|---|
| `load()` | Build snapshot dari pohon project |
| `files()` | Semua entry (urut deterministik) |
| `documents()` | Entry bertipe dokumen |
| `source_files()` | Entry source tree |
| `test_files()` | Entry test tree |
| `find()` | Cari berdasarkan file_id / logical_id / path (prefix) |
| `exists()` | Apakah file_id/path ada |
| `checksum()` | Checksum untuk file_id |
| `serialize()` | Representasi plain dict |

---

# SECTION 6 — VALIDATE

`BaselineValidator.validate()` mendeteksi:

| Kategori | Semantik |
|---|---|
| `duplicate_file_id` | dua entry berbagi file_id (error) |
| `duplicate_logical_id` | dua entry berbagi logical_id (error) |
| `missing_baseline` | referensi traceability ke file_id tak ada (error) |
| `checksum_mismatch` | checksum tersimpan ≠ konten disk (error) |
| `orphan_document` | dokumen tak direferensikan entry lain (warning) |

Snapshot default **valid=True, 0 issues** — seluruh checksum konsisten dengan disk, logical_id unik, tidak ada referensi hilang.

---

# SECTION 7 — TEST RESULTS

| Test Module | Tests | Status |
|---|---|---|
| `test_load_completeness.py` | 18 | ✅ PASSED |
| `test_index_lookup.py` | 21 | ✅ PASSED |
| `test_serialization.py` | 14 | ✅ PASSED |
| `test_validation.py` | 10 | ✅ PASSED |
| `test_determinism.py` | 4 | ✅ PASSED |
| **TOTAL BASELINE** | **67** | **67/67 PASSED** |

---

# VALIDATION

## Audit 1 — Snapshot Completeness

**Pertanyaan:** Apakah seluruh 11 kategori baseline terpenuhi?

| Kategori | Status |
|---|---|
| Foundation documents | ✅ 9 |
| Specification documents | ✅ 7 |
| ADR documents | ✅ 10 |
| Runtime documents | ✅ 13 |
| Engineering documents | ✅ 23 |
| Blueprint documents | ✅ 2 |
| Compliance documents | ✅ 6 |
| Source tree | ✅ 2,517 |
| Test tree | ✅ 554 |
| Package tree | ✅ 2 |
| Architecture documents | ✅ 24 |

**Hasil:** ✅ LULUS

---

## Audit 2 — Baseline Consistency

**Pertanyaan:** Apakah snapshot default valid dan konsisten?

| Check | Status |
|---|---|
| Snapshot default valid=True | ✅ |
| Checksum konsisten dengan disk (0 mismatch) | ✅ |
| logical_id unik (0 duplicate) | ✅ |
| file_id unik (0 duplicate) | ✅ |
| Semua entry punya checksum sha256 | ✅ |
| Semua path POSIX, tanpa backslash | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 3 — Loader Integrity

**Pertanyaan:** Apakah loader scan deterministik dan lengkap?

| Check | Status |
|---|---|
| Scan source/test untuk direktorium yang benar | ✅ |
| Skip __pycache__/.venv/noise dirs | ✅ |
| Document type mapping (docs/) benar | ✅ |
| Blueprint file terdeteksi (G0-001, I0-001) | ✅ |
| P1-001..P1-006 terindeks sebagai compliance docs | ✅ |
| Hasil idempoten antar load | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 4 — Index Integrity

**Pertanyaan:** Apakah index lookup akurat?

| Check | Status |
|---|---|
| Index len == snapshot count | ✅ |
| by_file_id lookup akurat | ✅ |
| by_path lookup akurat | ✅ |
| by_type / by_authority akurat | ✅ |
| Index immutable setelah build | ✅ |
| find/exists/checksum/contains akurat | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 5 — Determinism

**Pertanyaan:** Apakah snapshot deterministik?

| Check | Status |
|---|---|
| Load berulang → id/checksum/urutan identik | ✅ |
| JSON serialisasi identik (sort_keys) | ✅ |
| file_ids stabil (bukan acak) | ✅ |
| Urutan seleksi stabil | ✅ |
| Tidak ada random ordering | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 6 — Runtime Compatibility

**Pertanyaan:** Apakah kompatibel dengan stack P1 dan Python 3.8?

| Check | Status |
|---|---|
| Terpisah dari P1-001..P1-006 (tidak modifikasi) | ✅ |
| Python 3.8 compatible (Dict from typing, frozen dataclass) | ✅ |
| Tidak ada hardcoded path dalam checker (loader saja) | ✅ |
| Referensi dari manifest/catalog (P1-005/P1-004) | ✅ |
| STOP condition tidak aktif | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 7 — Test Results

**Pertanyaan:** Apakah seluruh test lulus?

| Suite | Count | Status |
|---|---|---|
| Loading + completeness | 18 | ✅ |
| Index + lookup | 21 | ✅ |
| Serialization + determinism | 14 | ✅ |
| Validation | 10 | ✅ |
| Determinism | 4 | ✅ |
| **Baseline total** | **67** | ✅ |
| **Full project** | **1,565** | ✅ |

**Hasil:** ✅ LULUS — 67/67 baseline, 1,565/1,565 full project.

---

## Audit 8 — Final Certification

**Pertanyaan:** Apakah P1-007 siap?

| Criteria | Status |
|---|---|
| Snapshot Completeness (A1) | ✅ |
| Baseline Consistency (A2) | ✅ |
| Loader Integrity (A3) | ✅ |
| Index Integrity (A4) | ✅ |
| Determinism (A5) | ✅ |
| Runtime Compatibility (A6) | ✅ |
| Test Results (A7) | ✅ |
| Final (A8) | ✅ |

**VERDICT:** ✅ LULUS — P1-007 siap. Snapshot baseline menjadi referensi tunggal seluruh checker; tidak ada checker dengan hardcoded path atau daftar file sendiri.

---

# STOP

STOP condition: **NOT ACTIVE.**

Tidak ada perubahan P1-001, P1-002, P1-003, P1-004, P1-005, atau P1-006 yang dibutuhkan. P1-007 adalah:
- Baseline snapshot — inventory deterministik sebagai referensi checker
- Menghormati P1-004 (catalog) dan P1-005 (manifest) tanpa modifikasi
- Tidak mengimplementasikan 99 checker (hanya menyediakan baseline yang akan dibaca checker)
- Tidak menambah/mengurangi/mengubah check
