# R4-002 — Reference Runtime Design

**Document ID:** R4-002
**Title:** Reference Runtime Design
**Status:** Completed
**Date:** 2026-08-03
**Author:** Chief Architect (Project SAM Architecture Decision Making)
**Audience:** Architecture, Design, Implementation
**Source of Authority:** Foundation | Specification | Blueprint | ADR-000..ADR-007 | R4-001
**Derived From:** R4-001 Reference Runtime Architecture

---

# Executive Summary

R4-002 menurunkan Reference Runtime Architecture (R4-001) menjadi **Structural Runtime Design** — deskripsi struktural yang masih berupa desain, bukan implementasi. Dokumen ini adalah jembatan antara arsitektur (apa dan mengapa) dan implementasi (bagaimana secara teknis).

**Perbedaan dengan R4-001:**
- R4-001: Architecture — mendefinisikan komponen, hubungan, boundary, invariant
- R4-002: Design — menurunkan detail struktural (interaction sequence, traceability matrix, readiness criteria) tanpa memasuki implementasi

**R4-002 tidak mendefinisikan:**
- API, interface, class, package, protocol
- Algorithm, pseudocode, concurrency mechanism
- Technology selection, serialization format, database schema
- Deployment mechanism, scaling strategy

---

# SECTION 1 — DESIGN PURPOSE

## 1.1 Peran Runtime Design

Runtime Design adalah **lapisan tengah** di antara Architecture dan Implementation:

```
Architecture (R4-001)     →  "Apa komponen dan bagaimana hubungannya?"
        ↓
Design (R4-002)           →  "Bagaimana struktur internal dan interaksinya?"
        ↓
Implementation (future)   →  "Bagaimana kode membangunnya?"
```

## 1.2 Tujuan

1. **Menurunkan** arsitektur R4-001 menjadi blueprint struktural yang lebih detail
2. **Membangun** interaction sequence lengkap — langkah demi langkah
3. **Menyusun** traceability matrix — membuktikan setiap elemen design dapat ditelusuri ke sumber
4. **Menentukan** readiness criteria — kapan implementasi bisa dimulai dan apa yang masih terlarang
5. **Menyediakan** structural template untuk setiap komponen tanpa mendikte implementasi

## 1.3 Beda Architecture vs Design vs Implementation

| Aspek | Architecture (R4-001) | Design (R4-002) | Implementation |
|---|---|---|---|
| **Komponen** | "7 komponen: Citizen Host, Capability Manager..." | Sama + structural boundary per komponen | Class, module, package |
| **Interaksi** | "Interaction model linear: Registry → Contract → ..." | Interaction sequence langkah demi langkah | Function calls, method invocations |
| **Dependency** | Direction: acyclic, single direction | Dependency graph dengan detail structural | Import statements, DI wiring |
| **Invariant** | Daftar invariant (I1-I27) | Invariant per komponen | Unit tests, assertions |
| **Boundary** | Definisi boundary (6 tipe) | Structural boundary diagram | Firewall, namespace, access control |
| **Lifecycle** | Lifecycle state per komponen | Lifecycle transition rules | State machine implementation |
| **Failure** | Propagation model | Failure mapping per komponen | Error handling code, exception hierarchy |
| **Traceability** | Authority chain | Traceability matrix lengkap | Code annotation, docstring references |
| **Readiness** | Architecture ready | Implementation readiness criteria | Build pipeline, deployment config |

---

# SECTION 2 — RUNTIME STRUCTURE

## 2.1 Structural Layout

Runtime structural layout terdiri dari **7 komponen** dalam chain linear tunggal:

```
┌─────────────────────────────────────────────────────────────────────┐
│                          RUNTIME                                     │
│                                                                      │
│  ┌──────────────┐                                                    │
│  │ Citizen Host │  ← Boundary surface: Contracts + Registry          │
│  └──────┬───────┘                                                    │
│         │                                                            │
│  ┌──────▼───────┐                                                    │
│  │  Capability  │                                                    │
│  │   Manager    │                                                    │
│  └──────┬───────┘                                                    │
│         │                                                            │
│  ┌──────▼───────┐                                                    │
│  │  Discovery   │                                                    │
│  │   Resolver   │                                                    │
│  └──────┬───────┘                                                    │
│         │                                                            │
│  ┌──────▼───────┐                                                    │
│  │  Contract    │                                                    │
│  │   Enforcer   │                                                    │
│  └──────┬───────┘                                                    │
│         │                                                            │
│  ┌──────▼───────┐                                                    │
│  │  Approval    │                                                    │
│  │ Coordinator  │                                                    │
│  └──────┬───────┘                                                    │
│         │                                                            │
│  ┌──────▼───────┐                                                    │
│  │  Execution   │                                                    │
│  │  Scheduler   │                                                    │
│  └──────┬───────┘                                                    │
│         │                                                            │
│  ┌──────▼───────┐                                                    │
│  │    Audit     │                                                    │
│  │   Recorder   │  ← Terminal: failure propagation stops here        │
│  └──────────────┘                                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Tidak ada komponen ke-8.** Verification adalah state transition di dalam Audit Recorder (Recorded → Verified — ADR-007).

## 2.2 Structural Design: Citizen Host

### Purpose
Entry point Runtime — boundary surface ke dunia eksternal Citizen. Menerima seluruh interaksi yang memasuki Runtime.

### Boundary
- **Luar:** Contracts + Registry (external boundary)
- **Dalam:** Capability Manager

### Responsibility
| # | Responsibility | Detail |
|---|---|---|
| R1 | Own bounded capability domain | Satu Runtime = satu domain = satu Citizen |
| R8 | Support certification | Menerima dan memproses certification requests untuk Capability yang dimiliki |
| R9 | Expose health | Menampilkan status kesehatan Runtime |
| — | Boundary enforcement | Memastikan seluruh interaksi masuk melalui Contracts + Registry |

### Input/Output
```
INPUT:  Capability Request  ← Citizen eksternal (via Contracts + Registry)
        Certification Request
        Health Probe

OUTPUT: Delegasi ke Capability Manager (Capability declaration)
        Certification status
        Health status
```

### Must
- Memiliki **satu** bounded capability domain (GOVERNANCE)
- Seluruh interaksi eksternal melalui Contracts + Registry — tidak ada direct access
- Tidak mengimplementasikan external access (ADR-006)

### Must Not
- Tidak mengelola lifecycle Provider/Connector
- Tidak memverifikasi implementasi Provider/Connector
- Tidak menyediakan SDK/API/protocol untuk integrasi eksternal

### Dependency
- **Otoritas:** Constitution, GOVERNANCE, CITIZEN_SPEC
- **Ke bawah:** Capability Manager (delegasi deklarasi Capability)
- **Ke atas:** tidak ada

### Structural Contract
```
Citizen Host
  - owns: one bounded capability domain
  - exposes: Contracts + Registry (surface)
  - delegates to: Capability Manager
  - does NOT own: external access, Provider lifecycle, protocol implementation
```

## 2.3 Structural Design: Capability Manager

### Purpose
Pengelola publikasi dan lifecycle Capability yang dimiliki Runtime.

### Boundary
- **Luar:** Citizen Host (input) + Registry (output — Capability terpublikasi)
- **Dalam:** Discovery Resolver

### Responsibility
| # | Responsibility | Detail |
|---|---|---|
| R2 | Publish capabilities | Eksplisit, discoverable, immutable |
| — | Manage capability lifecycle | Declared → Registered → Certified → Available → Deprecated → Retired |

### Input/Output
```
INPUT:  Capability declaration (dari Citizen Host)
        Lifecycle state transition request

OUTPUT: Published Capability (descriptor + contract reference)
        Capability lifecycle state
```

### Must
- Capability published: eksplisit, discoverable, immutable
- Setiap Capability memiliki descriptor lengkap (CAPABILITY_SPEC)
- Mengikuti lifecycle: Declared → Registered → Certified → Available → Deprecated → Retired

### Must Not
- Tidak mengeksekusi Capability — Registry yang discovery/resolve, bukan execute
- Tidak menggantikan Registry — Capability Manager mengelola publikasi, Registry melakukan discovery

### Dependency
- **Otoritas:** CAPABILITY_SPEC
- **Ke bawah:** Discovery Resolver
- **Ke atas:** Citizen Host

### Structural Contract
```
Capability Manager
  - manages: Capability lifecycle (publication, state transitions)
  - connects to: Registry (capability visible after Registration)
  - delegates to: Discovery Resolver
  - does NOT discover: discovery is Registry responsibility
  - does NOT execute: execution is Execution Scheduler responsibility
```

## 2.4 Structural Design: Discovery Resolver

### Purpose
Melakukan discovery dan resolution Capability — "diberikan Capability Request, Capability mana yang diterima?"

### Boundary
- **Luar:** Registry (Capability storage dan query)
- **Dalam:** Contract Enforcer

### Responsibility
| # | Responsibility | Detail |
|---|---|---|
| R4 | Discover & resolve capabilities | Query Registry, menerapkan ADR-002 |
| R16 | Resolution policy enforcement | Exact-preferred → compatible fallback → tie-break |

### Input/Output
```
INPUT:  Capability Request (reference ke Capability yang diminta)

OUTPUT: Capability Descriptor (CAPABILITY_SPEC)
        Contract Reference
        NOT FOUND / Version Mismatch / Error
```

### Must
- Discovery idempotent, tanpa side effect (REGISTRY_SPEC L129)
- Resolusi deterministik — input sama → output sama (REGISTRY_SPEC L147/L149)
- Exact match diutamakan (ADR-002)
- Fallback ke version-compatible (major sama, minor berbeda) jika exact tidak ada (ADR-002)
- Tie-break via identitas + versi (ADR-002)
- Suspended/removed objects NOT candidates
- Deprecated hanya dipilih jika tidak ada non-deprecated
- Version-incompatible (major berbeda) tidak dipilih
- Tidak menerima konteks implisit — resolusi hanya dari Capability Request (ADR-002 D-17)

### Must Not
- Tidak menjadi Approval — tidak memutuskan apakah operasi diizinkan
- Tidak mengeksekusi — tidak menjalankan Capability
- Tidak mendefinisikan Contract — tidak membuat aturan interaksi
- Tidak merekam audit — tidak mencatat events

### Dependency
- **Otoritas:** REGISTRY_SPEC, ADR-002
- **Ke bawah:** Contract Enforcer
- **Ke atas:** Capability Manager (Registry populated)

### Structural Contract
```
Discovery Resolver
  - queries: Registry (populated by Capability Manager)
  - applies: ADR-002 resolution policy
  - produces: Capability Descriptor + Contract Reference
  - does NOT approve: resolution ≠ authorization
  - does NOT execute: resolution ≠ performance
```

## 2.5 Structural Design: Contract Enforcer

### Purpose
Menyediakan immutable Contract — aturan komunikasi yang mengikat antara dua Citizen.

### Boundary
- **Luar:** Contract storage
- **Dalam:** Approval Coordinator

### Responsibility
| # | Responsibility | Detail |
|---|---|---|
| R3 | Expose immutable contracts | Contract = Input + Output + Metadata + Constraints + Compatibility + Error |
| R11 | Declare idempotency | Contract mendeklarasikan apakah operasi idempotent (ADR-003) |

### Input/Output
```
INPUT:  Contract Reference (dari Discovery Resolver)
        Version negotiation request

OUTPUT: Contract (Input, Output, Metadata, Constraints, Compatibility, Error)
        Idempotency declaration
        Negotiated version
        Negotiation failure
```

### Must
- Contract immutable (GOVERNANCE) — tidak berubah antar operasi
- Setiap Contract memiliki: Input, Output, Metadata, Constraints, Compatibility, Error (CONTRACT_SPEC)
- Compatibility negotiation: kedua Citizen sepakat pada satu versi
- Preferensi non-deprecated version
- Contract mendeklarasikan idempotency (ADR-003)
- Contract declare compatibility relative to predecessor (CONTRACT_SPEC)

### Must Not
- Tidak mengeksekusi operasi — Contract bukan Execution
- Tidak menyetujui operasi — Contract bukan Approval
- Tidak menemukan Capability — Contract bukan Registry

### Dependency
- **Otoritas:** CONTRACT_SPEC, ADR-003
- **Ke bawah:** Approval Coordinator
- **Ke atas:** Discovery Resolver

### Structural Contract
```
Contract Enforcer
  - exposes: immutable contract (structure, not implementation)
  - declares: idempotency (ADR-003)
  - negotiates: version compatibility
  - does NOT execute: contract ≠ operation
  - does NOT approve: contract ≠ authorization
```

## 2.6 Structural Design: Approval Coordinator

### Purpose
Gerbang otorisasi antara intent dan execution — menghasilkan keputusan binding.

### Boundary
- **Luar:** Approval gate
- **Dalam:** Execution Scheduler

### Responsibility
| # | Responsibility | Detail |
|---|---|---|
| R5 | Produce authorization decision before execution | Gate — tidak ada eksekusi tanpa Approval |
| R18 | Apply Accountable Decision Framework | ADR-001: deterministik, explainable, auditable |

### Input/Output
```
INPUT:  Approval Request
          - Decision Context
          - Referenced Contract
          - Referenced Capability
          - Referenced Citizen (opsional)

OUTPUT: Approval Decision: Approved / Rejected / Expired / Cancelled / Superseded
        Defined failures: Missing Contract / Unknown Capability /
          Registry Resolution Failed / Invalid Request /
          Expired Request / Approval Conflict
```

### Must
- Keputusan selalu mendahului eksekusi — gate, tidak boleh di-bypass
- Keputusan deterministik dalam state tetap (APPROVAL_SPEC, ADR-001)
- Keputusan binding (APPROVAL_SPEC)
- Keputusan explainable dan auditable (ADR-001)
- Mekanisme terbuka: automated atau human-mediated, selama akuntabel (ADR-001)
- Lifecycle: Created → Pending → Approved/Rejected/Expired → Archived

### Must Not
- Tidak mengeksekusi — Approval bukan Execution
- Tidak mendefinisikan Contract — Approval bukan Contract
- Tidak merekam audit — Approval bukan Audit
- Tidak dapat di-bypass — invarian I6

### Dependency
- **Otoritas:** APPROVAL_SPEC, ADR-001
- **Ke bawah:** Execution Scheduler
- **Ke atas:** Contract Enforcer

### Structural Contract
```
Approval Coordinator
  - receives: Approval Request with Contract + Capability context
  - produces: binding, deterministic, explainable decision
  - gate: no execution before Approved
  - mechanism: open (automated or human-mediated, accountable)
  - does NOT execute: approval ≠ performance
```

## 2.7 Structural Design: Execution Scheduler

### Purpose
Menjalankan operasi yang sudah di-approve dengan strict linear ordering.

### Boundary
- **Luar:** Execution domain
- **Dalam:** Audit Recorder

### Responsibility
| # | Responsibility | Detail |
|---|---|---|
| R6 | Apply only approved operations (idempotent) | Tidak ada eksekusi tanpa Approval |
| R12 | Observe idempotency declaration | Baca dari Contract; idempotent → pengulangan sah (ADR-003) |
| R17 | Enforce Strict Linear Ordering | Approval-arrival order → Execution order (ADR-005) |

### Input/Output
```
INPUT:  Approved operation (dari Approval Coordinator)
        Contract reference (untuk deklarasi idempotency)
        Execution identity

OUTPUT: Execution Result: Completed / Failed / Cancelled / Timed Out
        Observable outcome (untuk Audit — EXECUTION_SPEC L206)
        Defined failures: Missing Approval / Invalid Approval /
          Missing Contract / Capability Unavailable /
          Execution Timeout / Execution Failure / Execution Conflict
```

### Must
- Hanya mengeksekusi operasi yang sudah Approved (EXECUTION_SPEC)
- Strict Linear Ordering: urutan Approval = urutan Execution — deterministik, traceable (ADR-005)
- Satu operasi mencapai state terminal (Completed/Failed/Cancelled) sebelum operasi berikutnya (ADR-005)
- Mengamati deklarasi idempotency Contract (ADR-003)
- Idempotent operasi: pengulangan sah
- Non-idempotent operasi: pengulangan → Execution Conflict (ADR-003)
- Lifecycle: Created → Queued → Running → Completed/Failed/Cancelled/Timed Out → Archived
- Execution does not record — hanya menghasilkan observable outcome (EXECUTION_SPEC L206)

### Must Not
- Tidak mendefinisikan idempotency — itu milik Contract (ADR-003)
- Tidak mengeksekusi tanpa Approval — invarian I6
- Tidak mengeksekusi di luar urutan — Strict Linear (ADR-005)
- Tidak merekam audit — Execution bukan Audit
- Tidak memutuskan — Execution bukan Approval

### Dependency
- **Otoritas:** EXECUTION_SPEC, ADR-003, ADR-005
- **Ke bawah:** Audit Recorder
- **Ke atas:** Approval Coordinator

### Structural Contract
```
Execution Scheduler
  - receives: Approved operation
  - observes: Contract idempotency declaration (ADR-003)
  - enforces: Strict Linear Ordering (ADR-005)
  - produces: Execution Result + Observable Outcome
  - does NOT decide: execution ≠ approval
  - does NOT record: execution ≠ audit
```

## 2.8 Structural Design: Audit Recorder

### Purpose
Mengamati, merekam, memverifikasi, dan mengarsipkan seluruh aktivitas Runtime — menjadikan eksekusi sebagai bukti (evidence). Titik terminasi failure propagation.

### Boundary
- **Luar:** Audit domain
- **Dalam:** tidak ada (leaf node)

### Responsibility
| # | Responsibility | Detail |
|---|---|---|
| R7 | Make activity traceable (backward chain) | Audit ← Execution ← Approval ← Contract ← Registry ← Capability ← Citizen |
| R10 | Participate in auditing | Observe + semua komponen ekspos audit identity |
| R13 | Verification state transition | Recorded → Verified (ADR-007) |
| R14 | Failure termination | Menerima failure dari seluruh upstream, mencatat, tidak meneruskan (ADR-004) |

### Input/Output
```
INPUT:  Observable outcome (dari Execution Scheduler)
        Execution identity + Contract reference + Registry reference
        Failure dari komponen upstream (jika terjadi)

OUTPUT: Audit Record (state: Recorded / Verified / Archived)
        Traceability chain (mundur — no broken link)
        Defined failures: Broken Traceability / Incomplete Record /
          Invalid Record / Duplicate Record
```

### Must
- Mengamati dan merekam — "Audit observes and records" (AUDIT_SPEC L193)
- Verification sebagai state transition Recorded → Verified (ADR-007)
- Traceability mundur tanpa broken link (AUDIT_SPEC)
- Audit tidak memutuskan — "Audit is not Approval" (AUDIT_SPEC L30)
- Audit tidak mengeksekusi — "Audit is not Execution" (AUDIT_SPEC L32)
- Audit tidak mempengaruhi outcome — "has no influence over what Execution produces" (AUDIT_SPEC L193)
- Audit adalah titik terminasi propagasi failure (ADR-004)
- Tidak ada feedback loop (R1-001 L118)
- Lifecycle: Recorded → Verified → Archived

### Must Not
- Tidak menyetujui operasi — bukan Approval
- Tidak mengeksekusi operasi — bukan Execution
- Tidak mempengaruhi outcome — no feedback (ADR-007)
- Tidak meneruskan failure — terminasi (ADR-004)
- Tidak menambahkan komponen — Verification adalah state transition (ADR-007)

### Dependency
- **Otoritas:** AUDIT_SPEC, ADR-004, ADR-007
- **Ke bawah:** tidak ada (terminal node)
- **Ke atas:** Execution Scheduler + failure dari seluruh upstream

### Structural Contract
```
Audit Recorder
  - observes: Execution outcomes + upstream failures
  - records: Audit Record (Recorded)
  - verifies: Recorded → Verified (ADR-007 state transition)
  - archives: Verified → Archived (terminal)
  - terminates: failure propagation (ADR-004)
  - does NOT feed back: no influence over execution outcomes
  - does NOT forward: failure stops here
```

---

# SECTION 3 — DESIGN INTERACTION

## 3.1 Interaction Sequence: Normal Flow

Alur interaksi penuh dari Citizen hingga Audit:

```
STEP 1 — CITIZEN ENTRY
─────────────────────────
Citizen eksternal → Contracts + Registry (surface)
  → Citizen Host menerima Capability Request
  → Citizen Host memvalidasi: apakah request masuk melalui Contracts + Registry?
  → Jika ya: delegasi ke Capability Manager

STEP 2 — CAPABILITY REGISTRATION
─────────────────────────────────
Citizen Host → Capability Manager
  → Capability Manager memeriksa: apakah Capability yang diminta milik domain ini?
  → Jika ya: melanjutkan ke Discovery Resolver
  → Jika tidak: mengembalikan ke Citizen Host dengan informasi routing

STEP 3 — DISCOVERY & RESOLUTION
────────────────────────────────
Capability Manager → Discovery Resolver
  → Discovery Resolver menerima Capability Request
  → Query Registry untuk Capability yang cocok
  → Menerapkan ADR-002 resolution policy:
      a. Exact match? → pilih
      b. Tidak exact? → cari version-compatible (major sama)
      c. Beberapa kandidat kompatibel? → tie-break identitas + versi
      d. Hanya deprecated? → pilih (tidak ada non-deprecated)
      e. Tidak ada? → NOT FOUND
  → Output: Capability Descriptor + Contract Reference

STEP 4 — CONTRACT PROVISION
────────────────────────────
Discovery Resolver → Contract Enforcer
  → Contract Enforcer menerima Contract Reference
  → Mengambil Contract yang immutable
  → Jika version negotiation diperlukan:
      a. Kedua Citizen mengirimkan versi yang didukung
      b. Contract Enforcer memilih versi kompatibel tertinggi
      c. Preferensi non-deprecated version
      d. Jika tidak ada versi kompatibel? → Negotiation Failure
  → Contract menyediakan: Input, Output, Metadata, Constraints, Compatibility, Error
  → Contract mendeklarasikan: idempotency (YES/NO — ADR-003)
  → Output: Contract + Idempotency Declaration

STEP 5 — APPROVAL
──────────────────
Contract Enforcer → Approval Coordinator
  → Approval Coordinator menerima Approval Request:
      - Decision Context
      - Referenced Contract
      - Referenced Capability
      - Referenced Citizen (opsional)
  → Menerapkan Accountable Decision Framework (ADR-001):
      a. Evaluasi dalam state tetap, deterministik
      b. Mekanisme terbuka — automated atau human-mediated, selama akuntabel
      c. Keputusan explainable — alasan dapat dijelaskan
      d. Keputusan auditable — traceable oleh Audit
  → Output: Approval Decision — Approved / Rejected / Expired / Cancelled / Superseded
  → Lifecycle: Created → Pending → [Decision]

STEP 6 — EXECUTION
───────────────────
Approval Coordinator → Execution Scheduler (HANYA jika Approved)
  → Execution Scheduler menempatkan operasi dalam queue (Strict Linear Ordering)
  → Satu operasi dieksekusi sampai state terminal (Completed/Failed/Cancelled)
  → Sebelum eksekusi: baca deklarasi idempotency dari Contract
  → Selama eksekusi:
      a. Jika idempotent dan operasi ini pengulangan → sah (ADR-003)
      b. Jika non-idempotent dan operasi ini pengulangan → Execution Conflict (ADR-003)
  → Strict Linear: Approval-arrival order = Execution order (ADR-005)
  → Lifecycle: Created → Queued → Running → [Result] → Archived
  → Output: Execution Result + Observable Outcome

STEP 7 — AUDIT RECORDING
─────────────────────────
Execution Scheduler → Audit Recorder
  → Audit Recorder mengamati observable outcome (EXECUTION_SPEC L206)
  → Membentuk traceability chain mundur:
      Audit ← Execution ← Approval ← Contract ← Registry ← Capability ← Citizen
  → Membuat Audit Record dengan state: Recorded

STEP 8 — VERIFICATION
──────────────────────
Audit Recorder (internal state transition)
  → Memverifikasi traceability chain — seluruh link utuh?
  → Memvalidasi record — lengkap? tidak rusak?
  → State transition: Recorded → Verified (ADR-007)
  → Menggunakan Contract + Registry references untuk traceability
  → Tidak mempengaruhi execution outcome — no feedback

STEP 9 — ARCHIVAL
─────────────────
Audit Recorder (internal state transition)
  → Record yang sudah Verified di-archive
  → State transition: Verified → Archived
  → Archived adalah terminal state
```

## 3.2 Interaction Sequence: Failure Flow

```
FAILURE ORIGIN → PROPAGATION → TERMINATION
───────────────────────────────────────────

Kegagalan di Registry:
  Registry failure → Contract Enforcer → Approval Coordinator
    → Execution Scheduler → Audit Recorder (terminasi)

Kegagalan di Contract:
  Contract failure → Approval Coordinator
    → Execution Scheduler → Audit Recorder (terminasi)

Kegagalan di Approval:
  Approval failure → Execution Scheduler → Audit Recorder (terminasi)

Kegagalan di Execution:
  Execution failure → Audit Recorder (terminasi)

Kegagalan di Audit:
  Audit mencatat failure-nya sendiri — tidak dipropagasikan ke mana pun

Aturan (ADR-004):
  - Setiap komponen HANYA mempropagasikan failure yang ia produksi sendiri
  - Propagation mengikuti chain linear — tidak menciptakan jalur baru
  - Audit Recorder adalah titik terminasi
  - No feedback loop
```

## 3.3 Interaction Sequence: External Flow

```
CITIZEN EKSTERNAL → RUNTIME
────────────────────────────
Citizen eksternal → Contracts + Registry → Citizen Host
  → [chain Runtime penuh] → Contracts + Registry → Citizen eksternal

RUNTIME → PROVIDER/CONNECTOR
─────────────────────────────
[Chain Runtime] → Contracts + Registry → Provider/Connector

Prinsip:
  - Provider, Connector, Agent = Citizens di luar chain (ADR-006)
  - Interaksi hanya melalui Contracts + Registry
  - Tidak ada direct access
  - Tidak ada side channel
  - Tidak ada shortcut
```

## 3.4 Sequence Verification

| Step | Komponen Output | Komponen Input | Kompatibel dengan |
|---|---|---|---|
| Citizen → Capability | Capability Request | Citizen Host | CITIZEN_SPEC, ADR-006 |
| Capability → Registry | Capability declaration | Registry lookup | CAPABILITY_SPEC |
| Registry → Contract | Contract Reference | Contract Enforcer | REGISTRY_SPEC, ADR-002 |
| Contract → Approval | Contract + Idempotency | Approval Coordinator | CONTRACT_SPEC, ADR-003 |
| Approval → Execution | Approved operation | Execution Scheduler | APPROVAL_SPEC, ADR-001, ADR-005 |
| Execution → Audit | Observable outcome | Audit Recorder | EXECUTION_SPEC |
| Audit internal | Recorded → Verified | Audit Recorder | AUDIT_SPEC, ADR-007 |

---

# SECTION 4 — DESIGN RESPONSIBILITY

## 4.1 Responsibility Matrix

| # | Responsibility | Owner | Evidence |
|---|---|---|---|
| R1 | Own bounded capability domain | Citizen Host | GOVERNANCE; R1-001 R1 |
| R2 | Publish capabilities (eksplisit, discoverable, immutable) | Capability Manager | GOVERNANCE; CAPABILITY_SPEC; R1-001 R2 |
| R3 | Expose immutable contracts | Contract Enforcer | GOVERNANCE; CONTRACT_SPEC; R1-001 R3 |
| R4 | Discover & resolve capabilities | Discovery Resolver | REGISTRY_SPEC; ADR-002; R1-001 R4 |
| R5 | Produce authorization decision before execution | Approval Coordinator | APPROVAL_SPEC; ADR-001; R1-001 R5 |
| R6 | Apply only approved operations (idempotent) | Execution Scheduler | EXECUTION_SPEC; ADR-003; ADR-005; R1-001 R6 |
| R7 | Make activity traceable (backward chain) | Audit Recorder | AUDIT_SPEC; R1-001 R7 |
| R8 | Support certification | Citizen Host | GOVERNANCE; CITIZEN_SPEC; R1-001 R8 |
| R9 | Expose health | Citizen Host | GOVERNANCE; CITIZEN_SPEC; R1-001 R9 |
| R10 | Participate in auditing (observe + expose identity) | Audit Recorder (observe) + all components (identity) | GOVERNANCE; R1-001 R10 |
| R11 | Contract declares idempotency | Contract Enforcer | ADR-003; CONTRACT_SPEC |
| R12 | Execution observes idempotency declaration | Execution Scheduler | ADR-003; EXECUTION_SPEC |
| R13 | Verification state transition (Recorded → Verified) | Audit Recorder | ADR-007; AUDIT_SPEC L114-L118 |
| R14 | Failure propagation to Audit (termination) | All upstream → Audit Recorder | ADR-004 |
| R15 | External boundary enforcement (Contracts + Registry) | Citizen Host + Discovery Resolver + Contract Enforcer | ADR-006; R1-001 L58, L116 |
| R16 | Resolution policy (exact-preferred → compatible → tie-break) | Discovery Resolver | ADR-002 |
| R17 | Strict Linear Ordering enforcement | Execution Scheduler | ADR-005 |
| R18 | Accountable Decision Framework (deterministic + explainable) | Approval Coordinator | ADR-001 |

## 4.2 Owner Verification

| Komponen | Owned Responsibilities |
|---|---|
| Citizen Host | R1, R8, R9, R15 (part) |
| Capability Manager | R2 |
| Discovery Resolver | R4, R16, R15 (part) |
| Contract Enforcer | R3, R11, R15 (part) |
| Approval Coordinator | R5, R18 |
| Execution Scheduler | R6, R12, R17 |
| Audit Recorder | R7, R10, R13, R14 |

**Verifikasi:**
- ✅ 7 owner — tidak ada komponen tanpa tanggung jawab
- ✅ 18 responsibility — tidak ada yang tanpa owner
- ✅ 0 duplikasi — setiap responsibility memiliki tepat 1 owner
- ✅ 0 missing — seluruh R1-R10 + ADR-specific responsibility tercakup

---

# SECTION 5 — DESIGN INVARIANTS

## 5.1 Invariant dari Specification & Blueprint

| ID | Invariant | Sumber |
|---|---|---|
| I1 | Approval → Execution sequential: Approval completes, Execution begins only after | APPROVAL_SPEC L176-L179; EXECUTION_SPEC |
| I2 | Registry is discovery/resolution only — bukan Approval, Execution, Runtime, Audit, Contract | REGISTRY_SPEC Boundaries |
| I3 | Audit does not affect outcome — observes and records, no influence | AUDIT_SPEC L193; R1-001 L118 |
| I4 | Audit is not Approval | AUDIT_SPEC L30 |
| I5 | Audit is not Execution | AUDIT_SPEC L32 |
| I6 | Execution performs only after approval — no execution without approved Approval | EXECUTION_SPEC; APPROVAL_SPEC |
| I7 | Registry SHALL select exactly one deterministically | REGISTRY_SPEC L147/L149 |
| I8 | Approval completes → Execution begins | APPROVAL_SPEC L176 |
| I9 | Capability: immutable, versioned, uniquely identifiable, discoverable | CAPABILITY_SPEC; CONSTITUTION |
| I10 | Contract is immutable — tidak berubah antar operasi | CONTRACT_SPEC; GOVERNANCE |
| I11 | Discovery SHALL be idempotent and without side effects | REGISTRY_SPEC L129 |
| I12 | Golden Rule: Mission → Governance check → Approval → Execution → Verification → Audit | SAM_ARCHITECTURE L114 |
| I13 | No additional interaction invented — Audit does not feed back | R1-001 L118 |
| I14 | Linear causality — aliran interaksi satu arah | R1-001 L104 |
| I15 | Every Runtime shall own one bounded responsibility | GOVERNANCE Runtime Governance |
| I16 | Citizens communicate through Capabilities — never through implementation | CAPABILITY_SPEC; CITIZEN_SPEC |
| I17 | Boundary Runtime = Contracts + Registry — tidak ada mekanisme ketiga | R1-001 L58; ADR-006 |
| I18 | Every external interaction goes through Registry | R1-001 L116 |

## 5.2 Invariant dari ADR

| ID | Invariant | Sumber |
|---|---|---|
| I19 | Single Cohesive Runtime per domain | ADR-000 |
| I20 | Approval decision deterministik, explainable, auditable | ADR-001 |
| I21 | Registry exact-preferred → fallback kompatibel → tie-break deterministik | ADR-002 |
| I22 | Idempotency declared by Contract, observed by Execution | ADR-003 |
| I23 | Idempotent → pengulangan sah; non-idempotent → Execution Conflict | ADR-003 |
| I24 | Failure propagation linear → Audit (terminasi, no feedback) | ADR-004 |
| I25 | Strict Linear Ordering: Approval-arrival order → Execution order | ADR-005 |
| I26 | External boundary = Contracts + Registry | ADR-006 |
| I27 | Verification as Audit-observed State Transition (Recorded → Verified) | ADR-007 |

## 5.3 Invariant per Komponen

| Komponen | Invariant yang berlaku |
|---|---|
| Citizen Host | I15, I17, I18, I19 |
| Capability Manager | I9, I10, I16 |
| Discovery Resolver | I2, I7, I11, I16, I21 |
| Contract Enforcer | I10, I17, I22 |
| Approval Coordinator | I1, I4, I6, I8, I20 |
| Execution Scheduler | I1, I5, I6, I8, I22, I23, I25 |
| Audit Recorder | I3, I4, I5, I13, I14, I24, I27 |

---

# SECTION 6 — DESIGN BOUNDARIES

## 6.1 Internal Boundary

Batas antar komponen di dalam Runtime. Setiap komponen memiliki bounded responsibility sendiri.

```
┌─────────────────────────────────────────────────────────────┐
│ Internal Boundary Rules:                                    │
│                                                             │
│ 1. Interaksi hanya dengan komponen berdekatan dalam chain    │
│ 2. Tidak ada komponen yang melompati komponen lain            │
│ 3. Tidak ada komunikasi lateral antar komponen               │
│ 4. Setiap komponen hanya bergantung pada komponen di atasnya │
│ 5. Tidak ada komponen yang mengambil tanggung jawab          │
│    komponen lain                                             │
└─────────────────────────────────────────────────────────────┘
```

**Structural boundary per komponen:**

```
Citizen Host       ← Boundary surface (Contracts + Registry)
    │                (SOLE entry point from external Citizens)
    ↓
Capability Manager ← Internal boundary (Manages Capability only)
    │                (Does not discover, does not execute)
    ↓
Discovery Resolver ← Internal boundary (Discovers & resolves only)
    │                (Does not approve, does not execute)
    ↓
Contract Enforcer  ← Internal boundary (Exposes contracts only)
    │                (Does not execute, does not approve)
    ↓
Approval Coord.    ← Internal boundary (Decides only)
    │                (Does not execute, does not record)
    ↓
Execution Sched.   ← Internal boundary (Executes only)
    │                (Does not decide, does not record)
    ↓
Audit Recorder     ← Internal boundary (Records/verifies only)
                     (Does not influence, does not forward failure)
```

## 6.2 External Boundary

```
┌─────────────────────────────────────────────────────────────┐
│ External Boundary:                                          │
│                                                             │
│ Contracts + Registry = surface (permukaan) Runtime           │
│                                                             │
│ DUA mekanisme, TIDAK ADA yang ketiga                         │
│                                                             │
│ Provider  ─┐                                                │
│ Connector ─┼── Contracts + Registry ──► RUNTIME              │
│ Agent     ─┤                                                │
│ Future    ─┘                                                │
│                                                             │
│ Prinsip:                                                    │
│ - Structural, bukan physical                                │
│ - Single surface                                            │
│ - Linear causality (no shortcut, no side channel)           │
│ - Ownership separation (Runtime ≠ Provider)                 │
└─────────────────────────────────────────────────────────────┘
```

**Anchor:** ADR-006; R1-001 L58, L65.

## 6.3 Failure Boundary

```
┌─────────────────────────────────────────────────────────────┐
│ Failure Boundary:                                           │
│                                                             │
│ Komponen produser → propagasi linear → Audit Recorder        │
│                                                             │
│ Registry ────┐                                              │
│ Contract ────┤                                              │
│ Approval ────┼── linear propagation ──► Audit Recorder       │
│ Execution ───┤                         (TITIK TERMINASI)    │
│              │                         No feedback.         │
│              │                         No forwarding.       │
└──────────────┘─────────────────────────────────────────────┘
```

**Anchor:** ADR-004.

## 6.4 Verification Boundary

```
┌─────────────────────────────────────────────────────────────┐
│ Verification Boundary:                                      │
│                                                             │
│ Execution outcome ≠ Audit Record verified                   │
│                                                             │
│ Execution → produces outcome                (what happened) │
│ Audit → records outcome                     (evidence)      │
│ Audit → verifies record (Recorded→Verified)  (certification) │
│                                                             │
│ Verification:                                               │
│ - OUT-OF-CHAIN (not a component in the flow)                 │
│ - STATE TRANSITION inside Audit Recorder                    │
│ - No influence over execution outcomes                      │
│ - No feedback loop                                          │
│ - No new component                                          │
└─────────────────────────────────────────────────────────────┘
```

**Anchor:** ADR-007; AUDIT_SPEC L114-L118.

## 6.5 Deployment Boundary

```
┌─────────────────────────────────────────────────────────────┐
│ Deployment Boundary:                                        │
│                                                             │
│ Architecture → defines WHAT (components, relationships)      │
│ Design → defines HOW structural (this document)             │
│ Deployment → defines WHERE (topology, infrastructure)        │
│                                                             │
│ Architecture valid regardless of deployment topology        │
│ (GOVERNANCE Long-Term Governance)                            │
│                                                             │
│ ADR-000: topology tidak ditetapkan oleh Foundation/Spec      │
│                                                             │
│ Deployment = keputusan implementasi, bukan arsitektur        │
└─────────────────────────────────────────────────────────────┘
```

## 6.6 Citizen Boundary

```
┌─────────────────────────────────────────────────────────────┐
│ Citizen Boundary:                                           │
│                                                             │
│ Citizen A ←→ Capabilities ←→ Citizen B                      │
│                                                             │
│ Kommunikasi melalui Capabilities, bukan implementasi         │
│ Tidak ada asumsi Citizen lain exists                         │
│ Request Capability melalui Registry (discovery universal)    │
│ Setiap Citizen memiliki identitas unik                       │
│ Satu Runtime = satu Citizen Host (ADR-000)                  │
└─────────────────────────────────────────────────────────────┘
```

**Anchor:** CITIZEN_SPEC; CAPABILITY_SPEC; ADR-000.

---

# SECTION 7 — DESIGN DEPENDENCIES

## 7.1 Authority Dependency Graph

```
                    CONSTITUTION
                         │
                    GOVERNANCE
                         │
              ┌──────────┼──────────┐
              ↓          ↓          ↓
       CITIZEN_SPEC  CAPABILITY_SPEC  PHILOSOPHY
              ↓          ↓
              └────┬─────┘
                   ↓
            REGISTRY_SPEC
                   ↓
            CONTRACT_SPEC
                   ↓
            APPROVAL_SPEC
                   ↓
            EXECUTION_SPEC
                   ↓
            AUDIT_SPEC
                   ↓
         BLUEPRINT (G0-001)
                   ↓
         R1-001 (Design)
                   ↓
    ┌──────┬───────┼───────┬───────┬───────┬──────┬──────┐
    ↓      ↓       ↓       ↓       ↓       ↓      ↓      ↓
  ADR-000 ADR-001 ADR-002 ADR-003 ADR-004 ADR-005 ADR-006 ADR-007
    ↓      ↓       ↓       ↓       ↓       ↓      ↓      ↓
    └──────┴───────┴───────┴───────┴───────┴──────┴──────┘
                            ↓
                    R4-001 (Architecture)
                            ↓
                    R4-002 (Design — this document)
```

**Verifikasi:**
- ✅ Single direction — tidak ada reverse dependency
- ✅ Acyclic — tidak ada cycle
- ✅ Authority preserving — each layer doesn't contradict the layer above it

## 7.2 Component Dependency Graph

```
Citizen Host ⟶ Capability Manager ⟶ Discovery Resolver ⟶ Contract Enforcer
                                                                   │
                                                                   ↓
              Audit Recorder ⟵ Execution Scheduler ⟵ Approval Coordinator
```

**Verifikasi:**
- ✅ Linear — setiap komponen hanya bergantung pada komponen di atasnya dan Constitution/GOVERNANCE
- ✅ Acyclic — tidak ada feedback loop
- ✅ Terminal — Audit Recorder adalah leaf node (tidak ada komponen yang bergantung padanya)

## 7.3 Component-to-Authority Dependency

| Komponen | Otoritas |
|---|---|
| Citizen Host | CONSTITUTION, GOVERNANCE, CITIZEN_SPEC, ADR-000, ADR-006 |
| Capability Manager | CONSTITUTION, GOVERNANCE, CAPABILITY_SPEC |
| Discovery Resolver | CONSTITUTION, SPECIFICATION_FREEZE, REGISTRY_SPEC, ADR-002 |
| Contract Enforcer | CONSTITUTION, GOVERNANCE, CONTRACT_SPEC, ADR-003 |
| Approval Coordinator | CONSTITUTION, GOVERNANCE, APPROVAL_SPEC, ADR-001 |
| Execution Scheduler | CONSTITUTION, GOVERNANCE, EXECUTION_SPEC, ADR-003, ADR-005 |
| Audit Recorder | CONSTITUTION, GOVERNANCE, AUDIT_SPEC, ADR-004, ADR-007 |

---

# SECTION 8 — DESIGN TRACEABILITY

## 8.1 Traceability Matrix: Foundation → Design

| Foundation | Ke Specification | Ke Blueprint | Ke ADR | Ke R4-001 | Ke R4-002 |
|---|---|---|---|---|---|
| CONSTITUTION | Semua Specification | Komponen + Invariant | ADR-000..007 (determinism, integrity) | Section 5 (I1-I18) | Section 5 (I1-I18) |
| GOVERNANCE | Semua Specification | R1-R10 | ADR-000, ADR-001 | Section 3, 6 | Section 2, 4 |
| MISSION | — | Alur interaksi | — | Section 1.2, 4 | Section 3 |
| PHILOSOPHY | — | — | — | Section 12 | Section 9 |

## 8.2 Traceability Matrix: Specification → Design

| Specification | Ke Blueprint | Ke ADR | Ke R4-001 | Ke R4-002 |
|---|---|---|---|---|
| CITIZEN_SPEC | Citizen Host | ADR-000, ADR-006 | Section 3.1, 7.3 | Section 2.2, 6.6 |
| CAPABILITY_SPEC | Capability Manager, Discovery Resolver | ADR-002 | Section 3.2, 3.3 | Section 2.3, 2.4 |
| REGISTRY_SPEC | Discovery Resolver | ADR-002 | Section 3.3 | Section 2.4 |
| CONTRACT_SPEC | Contract Enforcer | ADR-003 | Section 3.4 | Section 2.5 |
| APPROVAL_SPEC | Approval Coordinator | ADR-001, ADR-005 | Section 3.5 | Section 2.6 |
| EXECUTION_SPEC | Execution Scheduler | ADR-003, ADR-005 | Section 3.6 | Section 2.7 |
| AUDIT_SPEC | Audit Recorder | ADR-004, ADR-007 | Section 3.7 | Section 2.8 |

## 8.3 Traceability Matrix: ADR → Design

| ADR | Ke Komponen | Ke R4-001 Section | Ke R4-002 Section |
|---|---|---|---|
| ADR-000 | Semua (topologi) | 2.1, 3.8 | 2.1, 6.6 |
| ADR-001 | Approval Coordinator | 3.5, 4.2 Step 3 | 2.6, 3.1 Step 5 |
| ADR-002 | Discovery Resolver | 3.3, 4.2 Step 1 | 2.4, 3.1 Step 3 |
| ADR-003 | Contract Enforcer + Execution Scheduler | 3.4, 3.6, 4.2 Step 4 | 2.5, 2.7, 3.1 Step 6 |
| ADR-004 | Semua (failure path) | 4.3, 11.2 | 3.2, 6.3 |
| ADR-005 | Execution Scheduler | 3.6, 4.2 Step 4 | 2.7, 3.1 Step 6 |
| ADR-006 | Citizen Host + Discovery Resolver + Contract Enforcer | 2.3, 4.4, 7.2 | 2.2, 3.3, 6.2 |
| ADR-007 | Audit Recorder | 3.7, 4.2 Step 6, 7.4 | 2.8, 3.1 Step 8, 6.4 |

## 8.4 Forward Traceability: R4-001 → R4-002

| R4-001 Section | Ke R4-002 Section | Status |
|---|---|---|
| 1 — Architectural Purpose | 1 — Design Purpose | ✅ Diturunkan |
| 2 — Boundary | 6 — Design Boundaries | ✅ Diturunkan (6 sub-section) |
| 3 — Components | 2 — Runtime Structure | ✅ Diturunkan (7 komponen + structural contract) |
| 4 — Interaction Model | 3 — Design Interaction | ✅ Diturunkan (9 step detail + failure + external) |
| 5 — Invariants | 5 — Design Invariants | ✅ Diekstrak (27 invariant, 0 baru) |
| 6 — Responsibility Matrix | 4 — Design Responsibility | ✅ Diturunkan (18 responsibility, 7 owner) |
| 7 — Boundaries | 6 — Design Boundaries | ✅ Diturunkan (6 boundary) |
| 8 — Decision Summary | 8 — Traceability | ✅ ADR column di matrix |
| 9 — Dependency Graph | 7 — Design Dependencies | ✅ Diturunkan (3 sub-graph) |
| 10 — Lifecycle | 2 — Komponen (lifecycle per komponen) | ✅ Embedded |
| 11 — Failure Model | 3.2 — Failure Flow | ✅ Diturunkan |
| 12 — Implementation Independence | 9 — Implementation Readiness | ✅ Diturunkan |
| 13 — Out of Scope | 10 — Out of Scope | ✅ Diperluas |

## 8.5 Design Completeness Checklist

| Elemen R4-001 | Apakah Turun di R4-002? |
|---|---|
| 7 komponen | ✅ Section 2 (structural contract per komponen) |
| Interaction model | ✅ Section 3 (9 step detail) |
| 27 invariant | ✅ Section 5 (dengan invariant per komponen) |
| 18 responsibility | ✅ Section 4 (matrix + owner verification) |
| 6 boundary | ✅ Section 6 (internal, external, failure, verification, deployment, citizen) |
| Dependency graph | ✅ Section 7 (authority + component + component-to-authority) |
| Failure model | ✅ Section 3.2 (origin → propagation → termination) |
| ADR decisions | ✅ Section 8 (traceability matrix) |
| Lifecycle | ✅ Section 2 (embedded per komponen) |
| Implementation independence | ✅ Section 9 |

---

# SECTION 9 — IMPLEMENTATION READINESS

## 9.1 What Is Now Ready for Implementation

Setelah R4-002, fase implementasi sekarang memiliki:

| Aspek | Ready? | Detail |
|---|---|---|
| **Komponen** | ✅ | 7 komponen + structural contract per komponen |
| **Interaction sequence** | ✅ | 9 step detail dari Citizen ke Audit |
| **Responsibility per komponen** | ✅ | 18 responsibility dengan 7 owner |
| **Invariant per komponen** | ✅ | 27 invariant didistribusikan ke komponen |
| **Boundary definition** | ✅ | 6 boundary dengan aturan struktural |
| **Dependency direction** | ✅ | Acyclic, single direction, authority preserving |
| **Failure model** | ✅ | Origin → propagation → termination |
| **Lifecycle per komponen** | ✅ | State + transition rules |
| **Input/Output per komponen** | ✅ | Defined interfaces (structural, not technical) |
| **Must / Must Not per komponen** | ✅ | Constraints + prohibitions |
| **Traceability** | ✅ | Foundation → Spec → Blueprint → ADR → Design |

## 9.2 What Implementation May Decide

Fase implementasi sekarang boleh memutuskan:

1. **Bahasa pemrograman** — Python, Go, Java, Rust, dll.
2. **Struktur package/module** — bagaimana mengorganisir kode dalam project
3. **Representasi data internal** — struct, class, data class, record
4. **Teknologi penyimpanan Registry** — in-memory, file, database
5. **Format serialisasi** — JSON, protobuf, MessagePack (selama Contract spec dipenuhi)
6. **Mechanisme transport antar komponen** — function call, message passing, event
7. **Testing framework** — pytest, unittest, Go testing, dll.
8. **Build system** — setuptools, poetry, go modules, cargo
9. **CI/CD pipeline** — GitHub Actions, GitLab CI, Jenkins
10. **Runtime environment** — local process, container, VM

## 9.3 What Implementation MUST NOT Decide

Fase implementasi TIDAK boleh:

| ❌ Dilarang | Kenapa |
|---|---|
| Menambah komponen ke-8 | Arsitektur: 7 komponen, ADR-007: Verification bukan komponen |
| Menghapus komponen | Seluruh 7 komponen diperlukan untuk Runtime utuh |
| Mengubah urutan chain | Linear causality (I14) — tidak bisa diubah |
| Membuat side channel | I13 — "No additional interaction is invented" |
| Membuat feedback loop dari Audit | I3, I13 — Audit tidak mempengaruhi outcome |
| Mengganti Approval sebagai gate | I6 — tidak ada eksekusi tanpa Approval |
| Mengabaikan idempotency declaration | ADR-003 — Contract declares, Execution observes |
| Mengabaikan Strict Linear Ordering | ADR-005 — Approval-arrival = Execution order |
| Mengimplementasikan external access di Runtime | ADR-006 — Provider/Connector di luar |
| Mengubah Specification behavior | Specification beku (SPECIFICATION_FREEZE) |
| Membuat Approval non-deterministik | ADR-001 — deterministik dalam state tetap |
| Membuat Registry non-deterministik | I7 — deterministik |
| Membuat Contract mutable | I10 — Contract immutable |

## 9.4 Architecture Gaps (None)

Tidak ada celah arsitektur yang tersisa. R3-004 Verdict A: Architecture Decision Layer Complete. Seluruh Candidate Blueprint sudah diputuskan oleh ADR.

---

# SECTION 10 — OUT OF SCOPE

| Area | Status | Rasional |
|---|---|---|
| API definition | Out of scope | Design, bukan technical interface |
| Interface/abstract class | Out of scope | Design struktural, bukan OOP |
| Package/module structure | Out of scope | Implementasi |
| Protocol (REST, gRPC, dll.) | Out of scope | Implementasi |
| Algorithm/pseudocode | Out of scope | Implementasi |
| Technology selection | Out of scope | Implementation Independence |
| Serialization format | Out of scope | CONTRACT_SPEC: "does not mandate any representation" |
| Database schema | Out of scope | Registry menyimpan references, bukan schema |
| Concurrency model | Out of scope | ADR-005 menetapkan ordering, bukan mechanism |
| Retry/recovery strategy | Out of scope | Mekanisme implementasi |
| Timeout/circuit breaker | Out of scope | Operational resilience |
| Deployment mechanism | Out of scope | ADR-000: topology not set by Foundation/Spec |
| Scaling/horizontal scaling | Out of scope | Deployment decision |
| Monitoring dashboard | Out of scope | Presentation layer |
| SDK/client library | Out of scope | Consumer tooling |
| Security implementation | Out of scope | Arsitektur = separation of responsibility |
| Performance optimization | Out of scope | Bukan ranah desain struktural |
| Logging framework | Out of scope | Audit ≠ logging; Audit Record ≠ log entry |
| Error handling code | Out of scope | Defined failures di Specification, handling di implementasi |

---

# VALIDATION

## Audit 1 — Design Completeness

**Pertanyaan:** Apakah seluruh elemen R4-001 terturunkan di R4-002?

| Elemen R4-001 | Terturunkan? | Section R4-002 |
|---|---|---|
| 7 komponen | ✅ | 2.1-2.8 |
| Structural contract per komponen | ✅ | 2.2-2.8 |
| Interaction model (Citizen → Audit) | ✅ | 3.1 (9 step) |
| Failure propagation | ✅ | 3.2 |
| External interaction | ✅ | 3.3 |
| 18 responsibility (R1-R18) | ✅ | 4 |
| 27 invariant (I1-I27) | ✅ | 5 |
| Invariant per komponen | ✅ | 5.3 |
| 6 boundary | ✅ | 6.1-6.6 |
| Dependency graph | ✅ | 7.1-7.3 |
| Traceability matrix | ✅ | 8 |
| Implementation readiness | ✅ | 9 |
| Out of scope | ✅ | 10 |

**Hasil:** ✅ LULUS — 13/13 elemen R4-001 terturunkan. 0 missing.

---

## Audit 2 — Architecture Consistency

**Pertanyaan:** Apakah R4-002 konsisten dengan R4-001?

| Aspek | R4-001 | R4-002 | Konsisten? |
|---|---|---|---|
| Jumlah komponen | 7 | 7 | ✅ |
| Urutan chain | Citizen Host → Capability → Discovery → Contract → Approval → Execution → Audit | Sama persis | ✅ |
| Verification | State transition (ADR-007) | State transition (Section 2.8, 3.1 Step 8) | ✅ |
| External boundary | Contracts + Registry | Contracts + Registry | ✅ |
| Failure propagation | Linear → Audit terminasi | Linear → Audit terminasi | ✅ |
| Responsibility count | 18 | 18 | ✅ |
| Invariant count | 27 | 27 | ✅ |
| Dependency direction | Acyclic, single direction | Acyclic, single direction | ✅ |

**Hasil:** ✅ LULUS — R4-002 konsisten dengan R4-001 di seluruh aspek.

---

## Audit 3 — ADR Consistency

**Pertanyaan:** Apakah R4-002 konsisten dengan ADR-000..ADR-007?

| ADR | Decision | Diterapkan di R4-002? |
|---|---|---|
| ADR-000 | Single Cohesive Runtime | ✅ Section 2.1 (satu Runtime, 7 komponen) |
| ADR-001 | Accountable Decision Framework | ✅ Section 2.6 (Approval deterministic + explainable) |
| ADR-002 | Exact-preferred + fallback | ✅ Section 2.4, 3.1 Step 3 |
| ADR-003 | Idempotency: Contract declares, Execution observes | ✅ Section 2.5 (Contract declares), 2.7 (Execution observes) |
| ADR-004 | Linear failure propagation | ✅ Section 3.2, 6.3 |
| ADR-005 | Strict Linear Ordering | ✅ Section 2.7, 3.1 Step 6 |
| ADR-006 | External boundary = Contracts + Registry | ✅ Section 2.2, 3.3, 6.2 |
| ADR-007 | Verification as state transition | ✅ Section 2.8, 3.1 Step 8, 6.4 |

**Hasil:** ✅ LULUS — 8/8 ADR konsisten.

---

## Audit 4 — Specification Compliance

**Pertanyaan:** Apakah R4-002 mematuhi seluruh Specification?

| Specification | Key behavior | Complied? |
|---|---|---|
| CITIZEN_SPEC | Identity, capability publication, certification, health | ✅ Section 2.2, 6.6 |
| CAPABILITY_SPEC | Immutable, versioned, discoverable, lifecycle | ✅ Section 2.3 |
| REGISTRY_SPEC | Discovery only, deterministic, idempotent, no side effects | ✅ Section 2.4 |
| CONTRACT_SPEC | Immutable, structure, version negotiation | ✅ Section 2.5 |
| APPROVAL_SPEC | Gate, binding decision, defined states, lifecycle | ✅ Section 2.6 |
| EXECUTION_SPEC | Perform only, lifecycle, defined failures | ✅ Section 2.7 |
| AUDIT_SPEC | Record, traceability, lifecycle, no outcome influence | ✅ Section 2.8 |

**Hasil:** ✅ LULUS — 7/7 Specification complied.

---

## Audit 5 — Foundation Compliance

**Pertanyaan:** Apakah R4-002 mematuhi Foundation?

| Foundation Document | Key Principle | Complied? |
|---|---|---|
| CONSTITUTION | Determinism, bounded responsibility, integrity | ✅ Section 5 (I1, I7, I9), Section 2 |
| GOVERNANCE (Runtime) | One bounded responsibility, publish capabilities, immutable contracts, certification, health, auditing | ✅ Section 2, 4 (R1-R10) |
| GOVERNANCE (Long-Term) | Valid regardless of deployment topology | ✅ Section 6.5, 9 |
| MISSION | Project purpose | ✅ Section 1.2 |
| PHILOSOPHY | Implementation Independence | ✅ Section 9 |

**Hasil:** ✅ LULUS — Foundation complied.

---

## Audit 6 — Authority Integrity

**Pertanyaan:** Apakah chain otoritas terjaga?

```
Constitution → Governance → Specification → Blueprint → ADR → Architecture → Design
```

**Verifikasi:**
- ✅ R4-002 tidak mengubah apapun di atasnya
- ✅ R4-002 tidak menciptakan otoritas baru
- ✅ R4-002 tidak mengubah invariant
- ✅ R4-002 tidak mengubah komponen
- ✅ R4-002 tidak menambah ADR
- ✅ 7 komponen = 7 komponen (tidak ada yang dikurangi/ditambah)
- ✅ Interaction sequence = turunan langsung dari R4-001 interaction model

**Hasil:** ✅ LULUS — authority chain intact.

---

## Audit 7 — Implementation Readiness

**Pertanyaan:** Apakah R4-002 memberikan blueprint yang cukup untuk implementation?

| Kriteria | Status |
|---|---|
| Komponen jelas (purpose, responsibility, input, output) | ✅ |
| Interaction sequence lengkap (9 step) | ✅ |
| Structural contract per komponen | ✅ |
| Dependency direction jelas | ✅ |
| Invariant per komponen | ✅ |
| Boundary definition jelas | ✅ |
| Must / Must Not per komponen | ✅ |
| Lifecycle per komponen | ✅ |
| Failure model (origin → propagation → termination) | ✅ |
| What implementation may decide | ✅ |
| What implementation must not decide | ✅ |
| Tidak ada celah arsitektur | ✅ |

**Hasil:** ✅ LULUS — Implementation ready. Design provides sufficient structural blueprint.

---

## Audit 8 — Final Runtime Design Certification

**Pertanyaan:** Apakah R4-002 siap menjadi baseline design untuk implementasi?

| Kriteria | Status |
|---|---|
| Seluruh komponen R4-001 terturunkan | ✅ Audit 1 |
| Konsisten dengan R4-001 | ✅ Audit 2 |
| Konsisten dengan 8 ADR | ✅ Audit 3 |
| Mematuhi 7 Specification | ✅ Audit 4 |
| Mematuhi Foundation | ✅ Audit 5 |
| Authority chain intact | ✅ Audit 6 |
| Implementation ready | ✅ Audit 7 |
| Tidak menciptakan komponen baru | ✅ |
| Tidak menciptakan invariant baru | ✅ |
| Tidak menciptakan keputusan arsitektur baru | ✅ |
| Tidak memasuki implementasi | ✅ |

**Hasil:** ✅ LULUS — **Runtime Design Certified.** R4-002 siap sebagai blueprint implementasi.

---

# STOP CONDITION

**STOP Status:** NOT ACTIVE

**Verifikasi:**
- ✅ Tidak membutuhkan ADR baru — 8 ADR Accepted (R3-004 Verdict A)
- ✅ Tidak membutuhkan perubahan ADR — seluruh konsisten (Audit 3)
- ✅ Tidak membutuhkan perubahan Architecture — R4-001 final (Audit 2)
- ✅ Tidak membutuhkan perubahan Specification — seluruh complied (Audit 4)
- ✅ Tidak membutuhkan perubahan Foundation — seluruh complied (Audit 5)
- ✅ Tidak membutuhkan komponen baru — 7 komponen, tidak ada ke-8 (Audit 1)

---

**END OF R4-002 — Reference Runtime Design**
