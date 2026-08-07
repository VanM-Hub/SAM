# EA-004-004 — Repository Normalization Dependency Graph

**Program:** MISSION-2A / Program A (Foundation Convergence)
**Artifact:** Repository Normalization Dependency Graph · **Status:** AUTHORIZED
**Mode:** 100% READ-ONLY · **Tanggal:** 2026-08-08 · **Oleh:** ZARA (Lead Implementation Engineer)

> Dokumen ini membangun **dependency graph** sebagai dasar normalisasi repository — TANPA mengubah
> repository. Graph berbasis **referensi file-eksplisit** (bukan terminologi, sesuai Lessons Learned EA-LL-002).
> Graph bersifat **engineering planning**, bukan graph Architecture.
> Graph hanya menggambarkan **kondisi repository saat ini**.

---

## 1. Repository Domains

Domain aktual hasil inventarisasi (bukan contoh dari instruksi — domain kosong/dorman dipisahkan dari legacy, sesuai catatan Engineering EA-004-003).

| # | Domain | Lokasi | File | Peran |
|---|---|---|---|---|
| 1 | **Foundation** | `docs/foundation/` | 9 | MISSION, VISION, PHILOSOPHY, PRINCIPLES, GOVERNANCE, CONSTITUTION, CHARTER, GLOSSARY, CITIZEN_SPEC |
| 2 | **Specification** | `docs/specifications/` | 7 | 6 spec domain + SAM_FRAMEWORK v1.0 |
| 3 | **ADR** | `docs/adr/` | 25 | Keputusan arsitektur ADR-000..028 |
| 4 | **Architecture** | `docs/architecture/` | 24 | SAM_ARCHITECTURE, Rulebook, Layer_Validation, dll |
| 5 | **Runtime** | `docs/runtime/` | 15 | R4-, R5-, I0-, E1– referensi runtime |
| 6 | **Engineering** | `docs/engineering/` | 29 | roadmap, strategy, decisions, journals, reports |
| 7 | **Design (paper)** | `docs/design/` | 30 | A0-, D-, G-, R- paper analysis/recovery |
| 8 | **Documentation** | `docs/documentation/` | 8 | lifecycle, versioning, style |
| 9 | **Compliance** | `docs/compliance/` | 8 | P1-001..008 baseline + 99 checker |
| 10 | **Testing** | `tests/` | 1680 | unit/sprint/runtime tests |
| 11 | **Release** | `docs/releases/` | 4 | manifest, checklist, version-history |
| 12 | **Legacy** | `docs/history/` | 6 | dep/legacy files (Archived) |
| 13 | **Generated** | (tidak ada folder khusus) | — | __pycache__, .venv — di-exclude |
| 14 | **Vendor** | `modules/openclaw/` | 80 | vendored OpenClaw |
| 15 | **User docs** | `docs/user/` | 9 | installation, cli, rest, llm guide |
| 16 | **Core** | `docs/core/` | 2 | EXECUTION_MODEL, THINKING_PROTOCOL (Unknown) |
| 17 | **Models** | `docs/models/` | 4 | TRUST/RISK/DECISION/MEMORY model |
| 18 | **Development/Impl templates** | `docs/development/`, `docs/implementation/`, `docs/templates/` | 6+4+12 | checklist, contributor, templates |

**Struktur:** 18 domain fungsional + 1 Generated (exclude) + 1 Vendor (terisolasi). Folder kosong (backlog, decisions, glossary, research, dst.) = **struktur repository**, bukan domain aktif (dipisahkan dari legacy per EA-004-003).

---

## 2. Dependency Graph

Berdasarkan **referensi file-eksplisit** (path/link/backtick `*.md`, bukan kata). Arah panah = "merujuk/menggunakan".

```
                        [FOUNDATION]  ←— root (direferensikan oleh nyaris semua domain)
                       /    |    \      \
              [MODELS]   [SPEC]  [ADR]  [CORE]
                 |        /  \     |       |
              [ARCHITECTURE]←─────┘       |
                 |     \                   |
           [RUNTIME]  [DESIGN-paper]───────┘
              |        (mengindeks ADR/arch/foundation sbg objek)
              |
       [COMPLIANCE]   [ENGINEERING]
              |           |
         [TESTING]     [RELEASE]
              |           |
           [USER docs] [DOCUMENTATION]
                          |
                      [TEMPLATES]
```

### Node & arah (berbasis evidence)

| Domain | Merujuk (out) | Direferensikan oleh (in) | Status node |
|---|---|---|---|
| **Foundation** | architecture (1) | Design(33), spec(24), adr(23), documentation(18), templates(10), implementation(6), core(1) | **ROOT** (upstream tertinggi) |
| **Specification** | architecture(7), foundation(24), models(4), core(2), documentation(1) | design(8), adr(4), implementation(1), development(1), runtime(1) | Upstream tinggi |
| **ADR** | foundation(23), spec(4), architecture(2→SAM_ARCHITECTURE), models(2), design(2) | architecture(25 via ARCHITECTURAL_DECISIONS), design(16 sbg objek) | Upstream |
| **Architecture** | adr(26 via indeks), user(2) | adr(2), spec(7), templates(6), development(2), design(16), foundation(1) | **Persimpangan** (downstream foundation, upstream runtime) |
| **Runtime** | adr(1), spec(1) | (referensi dari spec/design) | Downstream |
| **Design (paper)** | foundation(33), adr(16 sbg objek review), architecture(16), spec(8), core(3), templates(5), models(4), implementation(4) | adr(2) | Leaf-high-in-degree |
| **Engineering** | — (internal roadmap/strategy) | release(3), development(2), compliance(1), documentation(1), implementation(1), design(1) | Leaf |
| **Documentation** | foundation(18), engineering(1), templates(1) | spec(1), templates(1), design(1) | Leaf |
| **Compliance** | engineering(1), templates(1) | (jarang dirujuk dok lain; berinteraksi dgn code) | Leaf |
| **Testing** | (src/sam) | — | Leaf |
| **Release** | engineering(3), templates(3) | — | Leaf |
| **Legacy** | — | design(A0-001 sbg objek analisis), README(OPENCLAW_AS_MODULE) | **Terisolasi (Archived)** |
| **Generated** | — | — | **Excluded** |
| **Vendor** | — | src .py (56 sebutan openclaw, kode) | **Terisolasi (external)** |
| **User docs** | — | architecture(2), development(1) | Leaf |
| **Core** | foundation(1) | design(3), spec(2) | Leaf (Unknown) |
| **Models** | — | adr(2), spec(4), design(4) | Leaf |

---

## 3. Normalization Order

Untuk tiap domain: **prerequisite / dependent / independent**. Belum menentukan implementasi.

| Domain | Prerequisites | Dependents | Independent? |
|---|---|---|---|
| **Foundation** | — | spec, adr, architecture, documentation, design, templates, implementation | ❌ (paling upstream) |
| **Models** | — | spec, adr, architecture | Sebagian independent |
| **Specification** | foundation, models | adr, architecture, runtime, implementation | ❌ |
| **ADR** | foundation, spec | architecture, design, runtime | ❌ |
| **Architecture** | foundation, spec, adr | runtime, design, compliance, user | ❌ |
| **Runtime** | architecture, adr, spec | compliance | ❌ |
| **Compliance** | runtime, architecture | testing | ❌ |
| **Testing** | compliance, runtime | — | ❌ (tergantung semua) |
| **Design (paper)** | foundation, arch, adr, spec | (objek analisis — leaf) | ✅ (post-hoc analysis) |
| **Engineering** | — | release | ✅ independent dari docs-core |
| **Documentation** | foundation | — | Sebagian independent |
| **Release** | engineering | — | ✅ |
| **User docs** | architecture | — | ✅ |
| **Legacy** | (Archived — lepas) | — | ✅ **Independent** |
| **Generated** | — | — | ✅ independent (exclude) |
| **Vendor** | — | — | ✅ **Independent (terisolasi)** |
| **Core** | foundation (perlu klasifikasi dulu) | spec, design | ⚠️ **Unknown — belum bisa diurutkan** |

**Urutan topologis konsisten (JADI LABEL: Engineering Normalization Order):** Foundation → Models → Spec → ADR → Architecture → Runtime → Compliance → Testing.

> ⚠️ **Label eksplisit:** ini **Engineering Normalization Order** (urutan normalisasi engineering berbasis evidence) — BUKAN Architecture Order normatif. Architecture dependency normative berada di kewenangan Software Architect, tidak disetarakan dengan urutan engineering ini. Engineering/Release/Documentation/User/Legacy/Vendor/Generated = pararel (independent).

---

## 4. Circular Dependency Analysis

### Verifikasi cycle aktual (berbasis evidence eksplisit)

| Pasangan bidireksional terdeteksi (probe) | Verifikasi nyata | Status |
|---|---|---|
| architecture ↔ adr | Architecture mengindeks 26 ADR via `ARCHITECTURAL_DECISIONS.md` (katalog); **hanya 2 ADR** (006,007) balik ke `SAM_ARCHITECTURE.md` | ❌ **BUKAN cycle** — dominan satu arah (pola ADR wajar) |
| Design ↔ adr | Design paper mengindeks ADR sebagai **objek review** (R3-003..005); ADR balik ke design hanya ADR-006/007 → G0-001 | ❌ **BUKAN cycle nyata** |
| development ↔ implementation | Referensi silang 1-1 (checklist/doc) | ❌ Benign |
| documentation ↔ templates | Referensi silang 1-1 | ❌ Benign |

### Metode verifikasi
- Scan seluruh `*.md` aktif untuk referensi `*.md` eksplisit (path/link/backtick).
- Untuk setiap pasangan balik, periksa konten: apakah referensi adalah **dependensi fungsional** atau **akta indeks/objek** (como ARCHITECTURAL_DECISIONS mengindeks ADR, atau design mengulas ADR sebagai objek).
- Referensi sebagai objek/katalog **tidak membentuk siklus dependensi** — karena arah tidak memaksa ketergantungan pembacaan yang saling mengunci.

### Hasil
> ## No Circular Dependency Found
> Metode verifikasi: analisis referensi file-eksplisit seluruh dokumen active; seluruh pasangan balok (architecture−adr, design−adr, development−implementation, documentation−templates) terverifikasi sebagai **pola indeks/referensi-silang wajar**, bukan siklus dependensi fungsional yang menghalangi normalisasi topologis. Tidak ada cycle aktual maupun potensial yang memaksa ketergantungan siklik.

---

## 5. Critical Path

Jalur kritis Program A (dependency yang memblokir normalisasi), berdasarkan evidence:

> **Foundation → Specification → ADR → Architecture → Runtime → Compliance → Testing**

| Segmen | Alasan (evidence) |
|---|---|
| **Foundation → Spec** | Spec merujuk foundation 24× — SoT foundation harus stabil dulu |
| **Spec → ADR** | ADR merujuk spec 4× + foundation 23× — ADR butuh spec/foundation utk keputusan |
| **ADR → Architecture** | Architecture mengindeks 26 ADR (keputusan) — arsitektur bergantung kelengkapan ADR |
| **Architecture → Runtime** | Runtime merujuk adr+spec; R4-001 "Source of Authority: Foundation/Spec/Blueprint/ADR-000..007" |
| **Runtime → Compliance** | Compliance (99 checker) memvalidasi runtime (P1-001..008) |
| **Compliance → Testing** | Test compliance menguji checker (tests/compliance) |

**Catatan:** **SoT (G1-02) adalah gerbang tersembunyi** di posisi teratas — keputusan architecture soal SoT fase roadmap (Section 5/6 EA-004-002) adalah **prasyarat** sebelum Foundation→Spec bisa di-normalisasi penuh. Ini konsisten dengan jalur kritis "SoT → Traceability → Legacy → Compliance" dari instruksi.

---

## 6. Parallelization Opportunities

Workstream yang dapat berjalan paralel tanpa konflik (alasan dependency).

| Workstream | Dapat paralel dengan | Alasan dependency |
|---|---|---|
| **Legacy isolation** (EA-004-003 input) | Engineering, Documentation, Release | Legacy = terisolasi (Archived), independent dari docs-core |
| **Vendor management** | segalanya | Vendor (modules/openclaw) terisolasi, tidak tergantung docs |
| **Engineering/Roadmap normalization** | Compliance, Testing | Engineering = leaf independent |
| **Release normalization** | Engineering, User docs | Release merujuk engineering + templates (leaf cluster) |
| **Documentation + Templates** | Engineering | documentation→templates 1-1 benign; leaf |
| **Core (Unknown) classification** | (paralel sebagian EA-005 — verifikasi status) | Core leaf, tapi perku klasifikasi dulu sebelum isolasi |
| **SoT decision (G1-02)** | (bukan EA-004 — Architecture authority) | — |

**TIDAK dapat paralel (harus sekuensial):**
- Foundation → Spec → ADR → Architecture → Runtime: **harus berurutan** (rantai upstream-downstream ketat).
- Legacy finalisasi isolasi: menunggu SoT/G1-02 (keputusan) + klasifikasi core.

---

## 7. EA-005 Input

### 7.1 Dependency yang mempengaruhi implementasi
- Rantai topologis: Foundation → Spec → ADR → Architecture → Runtime → Compliance → Testing (harus urut).
- SoT (G1-02) = gerbang prasyarat normalisasi penuh (diputuskan Architecture).
- Legacy & Vendor = terisolasi (tidak memblokir).

### 7.2 Workstream yang harus berurutan
1. **Foundation** → **Specification** → **ADR** → **Architecture** (rantai docs-inti).
2. Setelah Architecture: **Runtime** → **Compliance** → **Testing**.
3. **Klasifikasi `docs/core/`** harus selesai SEBELUM isolasi legacy penuh (core = Unknown).

### 7.3 Workstream yang dapat diparalelkan
1. **Legacy isolation** ∥ **Vendor** ∥ **Engineering/Roadmap** ∥ **Release** ∥ **Documentation/Templates/User** (semua leaf/terisolasi).
2. Normalisasi docs-inti (rantai) bisa berjalan paralel dengan workstream leaf di cluster lain.

### 7.4 Authority yang diperlukan
- **Software Architect**: keputusan SoT (G1-02) + klasifikasi final `docs/core/*`.
- **Lead Engineer (Zara)**: otorisasi EA-005 utk merancang implementasi sequencing.
- **Engineering**: verifikasi & evidence (disediakan di EA-001..004).

---

## 8. Batasan (Larangan EA-004-004 — dipatuhi)

- ❌ Tidak menentukan folder baru
- ❌ Tidak mengubah struktur repository
- ❌ Tidak memindahkan artefak
- ❌ Tidak mengusulkan rename
- ❌ Tidak mengubah dependency Architecture
- ❌ Tidak mengubah Runtime dependency
- ✅ Graph hanya menggambarkan kondisi repository saat ini

---

## 9. Exit Criteria EA-004-004

| Kriteria | Status |
|---|---|
| Seluruh domain dipetakan | ✅ (18 domain fungsional + generated/vendor) |
| Dependency graph tersedia | ✅ (§2, berbasis evidence file-eksplisit) |
| Normalization order tersedia | ✅ (§3) |
| Circular dependency diverifikasi | ✅ (No Circular Dependency Found + metode) |
| Critical path ditentukan | ✅ (§5) |
| Peluang paralelisasi terdokumentasi | ✅ (§6) |
| Input EA-005 tersedia | ✅ (§7) |
| Repository tetap read-only | ✅ |
| Working tree bersih | ✅ (cek git status) |
| Tanpa commit | ✅ |

---

*— Akhir EA-004-004 Repository Normalization Dependency Graph —*
