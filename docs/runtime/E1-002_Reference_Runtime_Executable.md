# E1-002 — Reference Runtime Executable

**Document ID:** E1-002
**Title:** Reference Runtime Executable
**Status:** Completed
**Date:** 2026-08-03
**Author:** Zara (Product Engineering, atas arahan Van)
**Audience:** Engineering
**Source of Authority (trace chain):** Constitution → Governance → Specification → ADR-000..ADR-007 → R4-001 → R4-002 → R5-001 → I0-001 → I1-001 → I2-001..I2-007 → P0-001 → P1-001..P1-008 → E1-001 → **E1-002**

---

# Executive Summary

E1-002 membuat Reference Runtime (yang dikomposisikan oleh E1-001) **dapat dijalankan**. Menambah lapisan executable di `src/sam/runtime_root/main.py` (public API: `create_runtime`, `run_runtime`, `shutdown_runtime`) plus CLI `python -m sam.runtime_root`. Ini murni eksekusi deterministik (build → start → health → stop → dispose) — **tanpa fitur baru, tanpa mengubah 7 unit, arsitektur, ADR, compliance, atau baseline.**

---

## 1. Public API Executable

`src/sam/runtime_root/main.py`:

| Fungsi | Peran |
|---|---|
| `create_runtime()` | Build sebuah RuntimeRoot fresh (state BUILT); **tidak start**. |
| `run_runtime()` | Build + start; kembalikan RuntimeRoot (STARTED). |
| `shutdown_runtime(root)` | Stop (bila perlu) + dispose → DISPOSED. Raise jika sudah disposed. |

`__init__.py` mengekspos ketiganya langsung dari `sam.runtime_root`.

---

## 2. CLI

```
python -m sam.runtime_root
```

Menjalankan urutan smoke deterministik:

```
build → start → health → stop → dispose
```

Output (deterministik, tanpa timestamp/random/network):

```
sam.runtime_root: built (state=BUILT)
sam.runtime_root: started (state=STARTED)
sam.runtime_root: health=Failed (units=7, pipeline=7)
sam.runtime_root: stopped (state=STOPPED)
sam.runtime_root: disposed (state=DISPOSED)
```

Exit code: `0` sukses; `3` bila `RuntimeCompositionError` (mis. urutan lifecycle invalid).

> `health=Failed` karena discovery_resolver & contract_enforcer tidak punya `initialize()` dan secara internal tetap melaporkan unavailable. Ini agregasi jujur (E1-001 tidak mengubah unit — STOP condition). `units=7` dan `pipeline=7` mengonfirmasi ketujuh unit ter-wire.

Entry: `src/sam/runtime_root/__main__.py` → `main._main()`.

---

## 3. Smoke Test (Integration)

`tests/runtime/runtime_root/test_integration.py`:

| Test | Validasi |
|---|---|
| `test_full_lifecycle_build_start_health_stop_dispose` | Urutan penuh lewat public API E1-001 |
| `test_create_runtime_builds_root` | create_runtime → BUILT |
| `test_run_runtime_builds_and_starts` | run_runtime → STARTED + health |
| `test_shutdown_runtime_stops_and_disposes` | shutdown_runtime → DISPOSED |
| `test_shutdown_runtime_from_built` | shutdown dari BUILT → DISPOSED |
| `test_restart_via_executable_handlers` | run → shutdown → run lagi |
| `test_shutdown_runtime_after_dispose_raises` | shutdown dua kali → raise |
| `test_cli_smoke_sequence` | `python -m sam.runtime_root` exit 0, urutan benar |
| `test_cli_reports_seven_units_and_pipeline` | output `units=7`, `pipeline=7` |

Semua hijau.

---

# Audit 1 — Architecture Audit

**Bukti:** E1-002 adalah lapisan executable di atas E1-001; tidak menambah komponen Runtime, tidak mengubah arsitektur/ADR/blueprint/engineering. `main.py` hanya memaketkan panggilan ke `RuntimeBuilder`/`RuntimeRoot` (E1-001). CLI deterministik, offline, tanpa network/timestamp.

**Hasil:** ✅ LULUS

---

# Audit 2 — Implementation Audit

**Bukti:** `create_runtime` (build), `run_runtime` (build+start), `shutdown_runtime` (stop+dispose, raise bila disposed) terimplementasi dan teruji. `__main__.py` menghubungkan CLI. Public API diekspos via `__init__.py`.

**Hasil:** ✅ LULUS

---

# Audit 3 — Compliance Audit

**Bukti:** Compliance runner → **total evidence 99, deviating 0, verdict A**. `runtime_root/` di luar `src/sam/runtime/` (scope seluruh checker) — tidak menyentuh baseline/checker. Tidak ada perubahan P1-001..P1-008.

**Hasil:** ✅ LULUS — 99/99 HIJAU, verdict A.

---

# Audit 4 — Integration Audit

**Bukti:** Full runtime suite 917 passed; full project suite (excl legacy) 15,641 passed. 3 failure pre-existing terkonfirmasi (gagal juga di HEAD bersih `fe2442c`), bukan regression. Tiap test CLI menjalankan proses Python nyata (`python -m sam.runtime_root`) dan exit 0.

**Hasil:** ✅ LULUS

---

# Audit 5 — Determinism Audit

**Bukti:** CLI output identik pada setiap run (tanpa timestamp/random). Urutan lifecycle deterministik. Build deterministik (E1-001: build 100x identik). Tidak ada network.

**Hasil:** ✅ LULUS

---

# Audit 6 — Dependency Audit

**Bukti:** `main.py` mengimpor hanya `E1-001` (`runtime_builder`, `runtime_root`, `lifecycle`, `health`, `exceptions`) — tidak mengimpor unit secara langsung. Arah dependensi satu arah (executable → composition → unit). Tidak ada siklus, tidak ada service locator/global singleton baru.

**Hasil:** ✅ LULUS

---

# Audit 7 — Health Audit

**Bukti:** CLI melaporkan aggregate health; `units=7`/`pipeline=7` mengonfirmasi semua unit ter-wire. Health jujur (Failed karena DR+CE internal unavailable — unit tak diubah).

**Hasil:** ✅ LULUS

---

# Audit 8 — Final Certification

**Bukti:** Semua audit LULUS; `python -m sam.runtime_root` exit 0; smoke sequence lengkap; 0 regression; STOP condition terpenuhi.

**Hasil:** ✅ **LULUS — VERDICT A-CERTIFIED**

---

# STATUS

**SELESAI — E1-002 Reference Runtime Executable tersedia via `python -m sam.runtime_root` (build → start → health → stop → dispose). Public API `create_runtime/run_runtime/shutdown_runtime`. 99 compliance HIJAU, smoke test hijau, 0 regression.**

---
