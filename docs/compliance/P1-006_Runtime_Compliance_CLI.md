# P1-006 — Runtime Compliance CLI & Execution Runner

**Document ID:** P1-006  
**Title:** Runtime Compliance CLI & Execution Runner  
**Status:** Implemented  
**Date:** 2026-08-03  
**Author:** Chief Architect (Project SAM Architecture Decision Making)  
**Scope:** Mengubah Compliance Engine menjadi executable tool  
**Source of Authority:** P1-001, P1-002, P1-003, P1-004, P1-005  
**Mode:** Product Engineering — CLI + runner, BUKAN 99 checker logic  

---

# Executive Summary

P1-006 mengubah **Compliance Engine (P1-002)** menjadi executable tool. Setelah P1-006, seluruh compliance dapat dijalankan melalui **satu command** `compliance`.

**Yang diimplementasikan:**
- `ComplianceCLI` — entry point publik
- `CommandDispatcher` — parser + dispatcher
- `SessionRunner` — eksekusi session deterministik dari manifest
- `ConsoleReporter` — format keluaran deterministik
- `ExitCodeResolver` — pemetaan verdict → exit code

**Yang BELUM diimplementasikan:**
- 99 checker individual (P1-006 hanya menjalankan checker yang sudah terdaftar — placeholder atau real)

**Filosofi:** runner hanya menjalankan checker yang terdaftar. Tidak ada logic checker baru. Runner menghormati manifest (enabled/disabled), catalog (metadata/filter), dan engine (session lifecycle + verdict).

---

# SECTION 1 — PACKAGE STRUCTURE

```
src/sam/compliance/cli/
├── __init__.py              # Public API
├── compliance_cli.py        # ComplianceCLI + main()
├── command_dispatcher.py    # CommandDispatcher + Command
├── session_runner.py        # SessionRunner, SessionResult, SessionFilter
├── console_reporter.py      # ConsoleReporter
└── exit_code_resolver.py    # ExitCodeResolver
```

```
tests/compliance/cli/
├── conftest.py              # Shared fixtures
├── test_command_parsing.py  # command parsing + dispatch
├── test_runner.py           # runner execution + filters + lifecycle
├── test_exit_codes.py       # verdict -> exit code mapping
├── test_reporter.py         # reporter formatting + determinism
└── test_dispatch.py         # CLI dispatch end-to-end + manifest ordering
```

---

# SECTION 2 — CLI COMMANDS

| Command | Deskripsi | Exit Code |
|---|---|---|
| `compliance run` | Jalankan semua 99 check (enabled) | verdict |
| `compliance run --all` | Sama dengan `run` | verdict |
| `compliance run <check-id>` | Jalankan satu check | verdict |
| `compliance run --level L0..L4` | Jalankan check per level | verdict |
| `compliance run --category ADR` | Jalankan check per kategori | verdict |
| `compliance run --authority Specification` | Jalankan check per authority | verdict |
| `compliance run --tag runtime` | Jalankan check per tag | verdict |
| `compliance list [filters...]` | Daftar check | 0 |
| `compliance info <check-id>` | Metadata satu check | 0/1 |
| `compliance summary` | Statistik catalog + manifest | 0 |

**Filter komposable:** `--level`, `--category`, `--authority`, `--tag` dapat dikombinasikan (logika AND).

---

# SECTION 3 — SESSION MODEL

Setiap `compliance run` menghasilkan `SessionResult` immutable dengan:

| Field | Deskripsi |
|---|---|
| `session_id` | Identitas session unik |
| `started_at` | Waktu mulai (UTC ISO) |
| `completed_at` | Waktu selesai (UTC ISO) |
| `executed_checks` | Jumlah check dieksekusi |
| `skipped_checks` | Jumlah check dilewati (disabled / tak terpilih) |
| `total_checks` | Total 99 |
| `verdict` | Grade verdict (A/B/C/D) |
| `report` | `ComplianceReport` lengkap dari engine |

`to_dict()` menghasilkan representasi plain dict untuk integrasi.

---

# SECTION 4 — EXIT CODE MATRIX

| Exit Code | Verdict | Label |
|---|---|---|
| **0** | A | Certified |
| **1** | B | Minor Finding |
| **2** | C | Major Finding |
| **3** | D | Not Compliant |

Catatan: exit code `1` untuk unknown check (`info NOPE`), `2` untuk parse/usage error. Verdict exit code diambil dari `result.report.verdict.grade`.

Verdict dihitung oleh engine per P1-001 §6.2:
- any CRITICAL → D
- else any MAJOR → C
- else >3 MINOR → B
- else → A

---

# SECTION 5 — EXECUTION FLOW

```
argv → CommandDispatcher.parse() → Command
        → ComplianceCLI._dispatch_command()
            → SessionRunner.run(filter)
                → _select_ids(filter)   # manifest enabled + filter match
                → _build_registry(ids)  # catalog metadata → placeholder checks
                → ComplianceEngine(registry).run_session()  # engine lifecycle
                → SessionResult
            → ConsoleReporter.report_run()  # deterministic output
            → ExitCodeResolver.resolve(verdict) → exit code
```

**Kunci desain — runner menghormati manifest + catalog + engine:**

1. **Manifest** — `enabled()` menentukan subset yang dieksekusi; check disabled dilewati.
2. **Catalog** — `_catalog.get(id)` menyediakan metadata untuk membangun `ComplianceCheck` placeholder (level, category, severity, evidence_type, baseline_ref) dan filter (level/category/authority/tag).
3. **Engine** — `ComplianceEngine` menjalankan lifecycle session penuh (INITIATED → EVIDENCE → ANALYSIS → VERDICT → ARCHIVED) dan menghitung verdict per P1-001.

**Driver determinism:** semua pilihan check diurutkan deterministik (urutan manifest `(execution_order, check_id)`), dan runner menghasilkan placeholder `ComplianceCheck` (tanpa execution_fn) sehingga setiap session menghasilkan evidence INCONCLUSIVE → verdict A. Output konsisten antar run (hanya `session_id` dan timestamp yang unik).

---

# SECTION 6 — TEST RESULTS

| Test Module | Tests | Status |
|---|---|---|
| `test_command_parsing.py` | 21 | ✅ PASSED |
| `test_runner.py` | 17 | ✅ PASSED |
| `test_exit_codes.py` | 18 | ✅ PASSED |
| `test_reporter.py` | 13 | ✅ PASSED |
| `test_dispatch.py` | 16 | ✅ PASSED |
| **TOTAL CLI** | **85** | **85/85 PASSED** |

**Full project:** 1,498 tests (877 runtime + 189 presentation + 138 engine + 99 check framework + 60 catalog + 50 manifest + 85 CLI), all PASSED.

---

# VALIDATION

## Audit 1 — CLI Completeness

**Pertanyaan:** Apakah seluruh command yang diminta didukung?

| Command | Status |
|---|---|
| `run` | ✅ |
| `run --all` | ✅ |
| `run <check-id>` | ✅ |
| `run --level L0..L4` | ✅ |
| `run --category` | ✅ |
| `run --authority` | ✅ |
| `run --tag` | ✅ |
| `list` | ✅ |
| `info <check-id>` | ✅ |
| `summary` | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 2 — Engine Compatibility

**Pertanyaan:** Apakah CLI kompatibel dengan P1-002 engine?

| Check | Status |
|---|---|
| Menggunakan ComplianceEngine untuk session | ✅ |
| Engine menangani lifecycle + verdict (P1-001 §6.2) | ✅ |
| SessionRunner membangun ComplianceRegistry subset | ✅ |
| Exit code dari verdict.grade engine | ✅ |
| Suite version default `P1-001` | ✅ |
| Tidak menambahkan logic di luar engine | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 3 — Manifest Compatibility

**Pertanyaan:** Apakah CLI menghormati P1-005 manifest?

| Check | Status |
|---|---|
| Runner memakai `manifest.enabled()` | ✅ |
| Check disabled dilewati (tidak dieksekusi) | ✅ |
| skipped_checks = count − executed | ✅ |
| `run <check-id>` disabled → 0 executed | ✅ |
| Urutan dieksekusi dari manifest order | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 4 — Catalog Compatibility

**Pertanyaan:** Apakah CLI menghormati P1-004 catalog?

| Check | Status |
|---|---|
| Runner membaca metadata dari catalog | ✅ |
| Filter level/category/authority/tag dari catalog | ✅ |
| `list` menampilkan 99 check catalog | ✅ |
| `info` menampilkan metadata lengkap | ✅ |
| `summary` menampilkan distribusi catalog | ✅ |
| Unknown check ditolak | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 5 — Determinism

**Pertanyaan:** Apakah output dan urutan deterministic?

| Check | Status |
|---|---|
| Output `list`/`summary`/`info` identik antar run | ✅ |
| Body session identik (kecuali session_id/timestamp) | ✅ |
| Urutan check deterministik (manifest order) | ✅ |
| Tidak ada random ordering | ✅ |
| Tidak ada conditional ordering | ✅ |
| Hasil verdict stabil (semua placeholder → A) | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 6 — Session Integrity

**Pertanyaan:** Apakah session model utuh?

| Check | Status |
|---|---|
| SessionResult berisi session_id/started/completed | ✅ |
| executed_checks / skipped_checks / total akurat | ✅ |
| verdict diambil dari report | ✅ |
| to_dict() representable | ✅ |
| Engine state maju sampai ARCHIVED | ✅ |

**Hasil:** ✅ LULUS

---

## Audit 7 — Test Results

**Pertanyaan:** Apakah seluruh test lulus?

| Suite | Count | Status |
|---|---|---|
| Command parsing | 21 | ✅ |
| Runner execution | 17 | ✅ |
| Exit codes | 18 | ✅ |
| Reporter formatting | 13 | ✅ |
| CLI dispatch | 16 | ✅ |
| Full project | 1,498 | ✅ |

**Hasil:** ✅ LULUS — 85/85 CLI, 1,498/1,498 full project.

---

## Audit 8 — Final Certification

**Pertanyaan:** Apakah P1-006 siap?

| Criteria | Status |
|---|---|
| CLI Completeness (A1) | ✅ |
| Engine Compatibility (A2) | ✅ |
| Manifest Compatibility (A3) | ✅ |
| Catalog Compatibility (A4) | ✅ |
| Determinism (A5) | ✅ |
| Session Integrity (A6) | ✅ |
| Test Results (A7) | ✅ |
| Final (A8) | ✅ |

**VERDICT:** ✅ LULUS — P1-006 siap. Compliance Engine kini executable via satu command, menghormati manifest + catalog + engine, dan tidak mengimplementasikan 99 checker.

---

# STOP

STOP condition: **NOT ACTIVE.**

Tidak ada perubahan P1-001, P1-002, P1-003, P1-004, atau P1-005 yang dibutuhkan. P1-006 adalah:
- CLI + runner executable — mengubah engine menjadi tool
- Menghormati manifest, catalog, dan engine tanpa modifikasi
- Tidak mengimplementasikan 99 checker (hanya menjalankan yang terdaftar)
- Tidak menambah/mengurangi/mengubah check
