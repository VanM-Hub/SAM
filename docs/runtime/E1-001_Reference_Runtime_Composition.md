# E1-001 — Reference Runtime Composition

**Document ID:** E1-001
**Title:** Reference Runtime Composition
**Status:** Completed
**Date:** 2026-08-03
**Author:** Zara (Product Engineering, atas arahan Van)
**Audience:** Engineering
**Source of Authority (trace chain):** Foundation → Governance → Specification → Blueprint (G0-001) → ADR-000..ADR-007 → R4-001 → R4-002 → R5-001 → I0-001 → I1-001 → I2-001..I2-007 → P0-001 → P1-001..P1-008 → **E1-001**

---

# Executive Summary

E1-001 merakit **7 Reference Runtime Unit yang sudah ada** menjadi **satu runtime hidup** melalui sebuah **Composition Root** (`RuntimeBuilder`). Ini **produk perakitan (wiring)** — **tidak menambah fitur**, **tidak mengubah arsitektur**, **tidak mengubah ADR**, **tidak mengubah compliance/baseline**, dan **tidak mengubah unit-unit runtime**.

Hasil Architecture Validation (**E1-000**) menetapkan bahwa `composition` adalah **Runtime Composition Root**, bukan Runtime Component ke-8, bukan Application Host. Sesuai keputusan, lokasi paket adalah **`src/sam/runtime_root/`** — di **lapisan perakitan (assembly layer)**, di luar paket Reference Runtime (`sam/runtime/`), mengikuti Clean Architecture (Composition Root berada di luar domain Runtime).

---

## 1. Mengapa Bukan `src/sam/runtime/composition/`

Path awal yang dipikirkan (`src/sam/runtime/composition/`) **dibatalkan** karena:

| Alasan | Bukti |
|---|---|
| **Menambah direktori ke-22** di luar struktur tetap I1-001 | I1-001 §1.2: **tepat 21 direktori** = 7 unit + 4 infra (`shared, contracts, registry, internal`) + 9 test + 1 tools. I1-001 §5.1 tidak mengenal peran "composition root" di dalam `runtime/`. |
| **Memicu checker compliance L0-11** (bagian P1-008) | `L0-11` (`RuntimeNoExtraTopLevelCheck`) memindai `src/sam/runtime/` dan melarang direktori top-level selain 7 unit + 4 support. Terverifikasi empiris: satu-satunya kegagalan dari 99 checker adalah L0-11, gara-gara folder `composition/` (verdict D, `deviating=1`). |
| **Bentrok dengan DILARANG E1-001** | E1-001 DILARANG mengubah Compliance & Baseline; memperbaiki L0-11 berarti mengubah P1-008 (STOP condition). |

**Keputusan E1-000 (disetujui Van):** Composition Root diletakkan di **`src/sam/runtime_root/`** — paket perakitan bersih di luar `sam/runtime/`, sehingga **seluruh compliance checker (yang hanya memindai `src/sam/runtime/`) tetap HIJAU tanpa menyentuh baseline/ADR/arsitektur/unit/boundary.**

---

## 2. Struktur Paket

```
src/sam/runtime_root/            # Composition Root (perakitan 7 unit)
├── __init__.py                  # Public API E1-001
├── builder.py                   # RuntimeBuilder — composition root
├── composition.py               # RuntimeComposition — assembly ter-wire
├── container.py                 # RuntimeContainer — facade publik
├── graph.py                     # DependencyGraph + UNIT_CHAIN
├── health.py                    # RuntimeHealth + HealthStatus (agregasi jujur)
├── lifecycle.py                 # RuntimeLifecycle + RuntimeState
├── registry.py                  # RuntimeRegistry
├── validator.py                 # CompositionValidator
└── exceptions.py                # CompositionException + subclasses

tests/runtime/runtime_root/      # Test mirror
├── __init__.py
├── test_composition.py          # 40 unit test
└── test_integration.py          # 8 integration test
```

### 2.1 Public API

| Simbol | Peran |
|---|---|
| **`RuntimeBuilder`** | Composition root — membuat **tepat satu** instance tiap unit & merakit chain |
| **`RuntimeContainer`** | Facade publik — `start/stop/health/validate` |
| **`RuntimeComposition`** | Assembly ter-wire (registry, graph, health, lifecycle, validation) |
| `RuntimeLifecycle`, `RuntimeState` | State machine container |
| `RuntimeHealth`, `HealthStatus` | Agregasi health jujur |
| `RuntimeRegistry` | Registry satu-instance-per-unit |
| `DependencyGraph`, `UNIT_CHAIN` | Grafik chain kanonik + urutan |
| `CompositionValidator` | Validasi kelengkapan + dependency |
| `CompositionException` (+ subtype) | Error composition |

---

## 3. Desain

### 3.1 Chain Kanonik (dari R5-001 S2 / I1-001 §3)

```
citizen_host → capability_manager → discovery_resolver → contract_enforcer
              → approval_coordinator → execution_scheduler → audit_recorder
```

`UNIT_CHAIN` dan `CANONICAL_EDGES` di `graph.py` adalah **encode persis** dari rantai ini. `DependencyGraph` memastikan:
- **Acyclic** (DFS cycle detection).
- Setiap edge **hanya** link hilir berurutan (tidak ada skip, tidak ada lateral) — melanggar chain = `DependencyGraphError`.

### 3.2 Determinisme

- **Build deterministik**: `RuntimeBuilder.build()` menghasilkan grafik yang sama persis untuk input yang sama (diuji: build 100x → grafik identik).
- **Urutan deterministik**: registry, init unit, dan hidup/mati selalu dalam urutan chain kanonik.
- **Tanpa timestamp / random**: tidak ada output acak atau timestamp; semuanya state-driven.

### 3.3 Lifecycle Container

`CREATED → COMPOSED → STARTING → RUNNING → STOPPING → STOPPED` (+ `FAILED`). Start bersifat **state-driven, bukan health-gated**: composition root memanggil `initialize()` publik unit yang punya (ApprovalCoordinator, SchedulerService, RecorderService); unit tanpa initializer self-initialise. Ini hanya orchestration level composition — **unit tidak pernah meng-initialize unit lain** (E1-001 wiring rule; I1-001 IR4 no lateral).

### 3.4 Health = Agregasi Jujur

Composition **tidak memaksa** health unit. `RuntimeHealth` mengagregasi apa yang **jujur dilaporkan** unit:

| Unit | Status (pre-init) | Setelah `initialize()` |
|---|---|---|
| citizen_host | AVAILABLE | AVAILABLE |
| capability_manager | available | available |
| discovery_resolver | unavailable | **unavailable** (tak punya `initialize()`) |
| contract_enforcer | unavailable | **unavailable** (tak punya `initialize()`) |
| approval_coordinator | {'status':'UNAVAILABLE'} | AVAILABLE |
| execution_scheduler | {'status':'unavailable'} | available |
| audit_recorder | {'status':'UNAVAILABLE'} | **HEALTHY** (bukan AVAILABLE) |

DR dan CE tetap melaporkan `UNAVAILABLE` karena internal lifecycle-nya memang dimulai uninitialized — ini **di dalam unit**, di luar scope E1-001 (unit tak boleh diubah). `RuntimeHealth._normalise` menangani format heterogen (string vs dict), memetakan `HEALTHY → AVAILABLE`, dan memeriksa `UNAVAILABLE` **sebelum** `AVAILABLE` (perbaikan substring bug).

### 3.5 Validasi

`validate()` memeriksa **integritas laporan health** (setiap unit melaporkan status yang dikenali; agregat = enum HealthStatus yang diketahui) — **bukan** memaksa semua AVAILABLE (karena DR/CE memang UNAVAILABLE). Plus kelengkapan registry (7 unit, tepat satu instance) dan dependency (DAG valid).

### 3.6 Import Rule

- **Composition mengimpor unit** (via factory lazy import) — arah: unit **tidak pernah** mengimpor composition (terverifikasi: tidak ada reverse import).
- Tidak ada import lateral antar unit — wiring hanya di lapisan composition.
- Tidak ada jalur/otoritas hardcoded di kode produksi.

---

## 4. Keputusan yang Diambil

| # | Keputusan | Alasan |
|---|---|---|
| 1 | `composition` = **Runtime Composition Root**, bukan komponen/unit/host | E1-000: tak ada komponen ke-8 (R4-001/R5-001 S1/MC1); konsep ini absen dari rantai otoritas, persis domain Implementation Freedom (R5-001 §8 IF2/IF17) |
| 2 | Lokasi = **`src/sam/runtime_root/`** | Di luar `sam/runtime/` → compliance utuh; paket perakitan bersih mengikuti konvensi `*_runtime/` |
| 3 | Path lama `runtime/composition/` **dibatalkan** | Melanggar I1-001 (dir ke-22) + memicu L0-11 (P1-008, STOP) |
| 4 | Health disagregasi secara **jujur** | E1-001 tak boleh mengubah unit; DR/CE memang UNAVAILABLE secara internal |
| 5 | Startup **state-driven, bukan health-gated** | Permulaan deterministik; unit honourable lapor UNAVAILABLE sampai init |
| 6 | `validate()` = integritas laporan + kelengkapan + DAG | Bukan paksaan AVAILABLE |

---

## 5. Fitur yang TIDAK Ditambahkan (Disiplin E1-001)

- ❌ Tidak ada unit ke-8.
- ❌ Tidak ada fitur baru apa pun di unit-unit runtime.
- ❌ Tidak ada perubahan arsitektur (R4-001) / desain (R4-002) / engineering (R5-001) / blueprint (I0-001) / skeleton (I1-001).
- ❌ Tidak ada perubahan ADR (ADR-000..007 accepted — final).
- ❌ Tidak ada perubahan Compliance / Baseline (P1-001..P1-008 tetap; 99 checker HIJAU).
- ❌ Tidak ada perubahan spec / foundation (beku).

---

# Audit 1 — Kelengkapan (7 Unit, Tepat Satu Instance)

**Bukti:** `RuntimeRegistry` memegang **tepat satu** instance per id unit kanonik; `RuntimeBuilder` membangun ke-7 unit. `CompositionValidator.check_completeness()` memastikan ketujuh id ada dan tidak ada duplikasi.

**Hasil:** ✅ LULUS

---

# Audit 2 — Dependency DAG Acyclic

**Bukti:** `DependencyGraph` menjalankan DFS cycle detection; grafik kanonik punya 6 edge linear, 0 cycle. `is_acyclic()` benar; uji integrasi membangun grafik dan memverifikasi acyclic + 6 edge kanonik.

**Hasil:** ✅ LULUS — 0 cycle, DAG murni.

---

# Audit 3 — Chain Kanonik Terjaga

**Bukti:** `CANONICAL_EDGES` = CH→CM→DR→CE→AC→ES→AR (6 edge). `_is_canonical_edge` hanya menerima edge hilir berurutan; edge off-chain (skip/lateral) memicu `DependencyGraphError`. Order registry & init selalu mengikuti `UNIT_CHAIN`.

**Hasil:** ✅ LULUS — chain linear persis R5-001 S2 / I1-001 §3.

---

# Audit 4 — Kabupaten: Tidak Ada Unit/Modul yang Diubah

**Bukti:** `git status` menunjukkan perubahan terbatas pada artefak baru `runtime_root/` (+ paket composition asal dipindah) + dokumen; **tidak ada file unit** (`sam/runtime/*/`) yang dimodifikasi. Seluruh 7 unit tetap utuh.

**Hasil:** ✅ LULUS — 7 unit tidak tersentuh.

---

# Audit 5 — Compliance (99 Checker Hijau)

**Bukti (empiris):** dengan `runtime_root/` terpasang dan `runtime/composition/` dihapus, runner compliance melaporkan:
- **total evidence: 99**, **deviating: 0**, **verdict: A**.

`composition` di luar `src/sam/runtime/` → tidak terpindai L0-11 maupun checker lain (`_RUNTIME_PREFIX` = `src/sam/runtime/`).

**Hasil:** ✅ LULUS — 99/99 HIJAU, verdict A, tanpa perubahan baseline.

---

# Audit 6 — Tidak Ada Reverse Dependency

**Bukti:** pemindaian menunjukkan tidak ada modul unit yang mengimpor `runtime_root`/`composition`. Composition mengimpor unit hanya via **lazy factory import** (di dalam lambda factory), mencegah import cycle.

**Hasil:** ✅ LULUS — direction: units → composition root, bukan sebaliknya.

---

# Audit 7 — Determinisme

**Bukti:** uji integrasi menjalankan build 100x → grafik identik (`equals` benar); 100x full lifecycle (start/stop) deterministik. Tidak ada random/timestamp; urutan selalu chain kanonik.

**Hasil:** ✅ LULUS — deterministik.

---

# Audit 8 — Authority & Boundary Terjaga

**Bukti:** rantai otoritas utuh (E1-001 di ujung setelah P1-008). Tidak ada otoritas baru dibuat. Boundary Runtime (Contracts + Registry + Citizen Host) tidak diubah — composition adalah **konsumen** external, bukan pengubah boundary. Tidak ada jalur/otoritas hardcoded di kode produksi.

**Hasil:** ✅ LULUS

---

# TEST SUMMARY

- **Unit test:** 40 (`tests/runtime/runtime_root/test_composition.py`) — builder, DAG, registry, lifecycle, health, composition, validator, container, exceptions.
- **Integration test:** 8 (`tests/runtime/runtime_root/test_integration.py`) — full lifecycle via facade, semua unit hadir, canonical getters, grafik acyclic, agregasi health, build 100x identik, 100x lifecycle, instance segar per build.
- **Total:** **48 passed** (1.08s).
- **Compliance:** **99/99 HIJAU, verdict A, 0 deviation.**

---

# STATUS

**SELESAI — Reference Runtime Composition terimplementasi di `src/sam/runtime_root/` sebagai Composition Root, tanpa mengubah unit, arsitektur, ADR, compliance, atau baseline.**

---
