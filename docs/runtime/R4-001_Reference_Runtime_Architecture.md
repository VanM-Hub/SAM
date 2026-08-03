# R4-001 — Reference Runtime Architecture

**Document ID:** R4-001
**Title:** Reference Runtime Architecture
**Status:** Completed
**Date:** 2026-08-03
**Author:** Chief Architect (Project SAM Architecture Decision Making)
**Audience:** Architecture, Design, Implementation
**Source of Authority:** Foundation | Specification | Blueprint | ADR-000..ADR-007

---

# Executive Summary

R4-001 menyatukan seluruh Foundation, Specification, Blueprint, dan 8 ADR Accepted menjadi SATU arsitektur Runtime utuh. Ini adalah definisi arsitektural Reference Runtime — BUKAN implementasi, BUKAN class design, BUKAN API, BUKAN pseudocode. Hasil akhir: Architecture of the Reference Runtime — baseline resmi untuk R4.

**Arsitektur ini menetapkan:**
- 7 komponen Runtime (Citizen Host, Capability Manager, Discovery Resolver, Contract Enforcer, Approval Coordinator, Execution Scheduler, Audit Recorder) — tidak ada komponen ke-8
- Interaction model linear sepanjang chain: Registry → Contract → Approval → Execution → Verification → Audit
- Verification sebagai "Audit-observed State Transition" (out-of-chain, ADR-007) — bukan komponen baru
- External boundary = Contracts + Registry (ADR-006) — tidak ada mekanisme akses ketiga
- Propagation failure linear → Audit sebagai titik terminasi (ADR-004)
- Resolution exact-preferred dengan fallback kompatibel deterministik (ADR-002)
- Strict Linear Ordering berdasarkan urutan Approval (ADR-005)
- Idempotency via Contract declaration + Execution observation (ADR-003)
- Single Cohesive Runtime per domain (ADR-000)
- Accountable Decision Framework untuk Approval (ADR-001)

---

# SECTION 1 — ARCHITECTURAL PURPOSE

## 1.1 Apa Itu Reference Runtime

Reference Runtime adalah **model arsitektural** dari Runtime Project SAM — representasi utuh dari seluruh komponen Runtime, interaksinya, batasannya, invariannya, dan lifecycle-nya. Ia menyatukan seluruh keputusan arsitektur dari Foundation, Specification, Blueprint, dan ADR-000..ADR-007 menjadi **satu arsitektur yang koheren**.

Reference Runtime adalah **arsitektur referensi** — bukan instance Runtime tertentu, bukan deployment, bukan implementasi. Ia adalah cetak biru arsitektural dari mana setiap Runtime konkret akan diturunkan.

**Anchor:**
- R1-001 L34 ("The Minimal Reference Runtime contains exactly the seven responsibility containers that realize the Specification concepts")
- GOVERNANCE ("Every Runtime shall: own one bounded responsibility, publish capabilities, expose immutable contracts, support certification, expose health, participate in auditing")

## 1.2 Tujuan

1. **Menyatukan seluruh keputusan arsitektur** — Foundation + Specification + Blueprint + ADR-000..007 → menjadi satu arsitektur Runtime utuh tanpa kontradiksi, tumpang tindih, atau celah.
2. **Mendefinisikan komponen Runtime** — 7 komponen lengkap dengan purpose, responsibility, inputs, outputs, must, must not, authority, dependency.
3. **Membangun interaction model** — dari Citizen turun hingga Audit, mencakup Verification (ADR-007) sebagai state transition out-of-chain.
4. **Mengekstrak seluruh invariant** — tidak menciptakan invariant baru, hanya mengekstraksi dari sumber yang sudah ada.
5. **Membangun dependency graph** — acyclic, single direction, authority-preserving.
6. **Mendefinisikan boundary** — internal, external, citizen, verification, failure, deployment.
7. **Membuktikan implementation independence** — arsitektur tidak bergantung pada bahasa, framework, database, OS, network, serialization, deployment platform.

## 1.3 Apa yang BUKAN Tujuan

Reference Runtime Architecture **BUKAN**:

| Bukan | Bukti |
|---|---|
| **Implementation** — tidak mendefinisikan class, package, function, atau algoritma | GOVERNANCE: "Implementation may evolve. Architecture should remain stable." |
| **API / Interface** — tidak mendefinisikan method signature, REST endpoint, atau protokol komunikasi | R1-001: Component boundaries adalah tanggung jawab, bukan interface teknis |
| **Pseudocode** — tidak mendeskripsikan logika program | Arsitektur = struktur + hubungan; implementasi = kode |
| **Class design** — tidak mendefinisikan hierarki class atau pola desain OOP | Blueprint: "Blueprint tidak menetapkan class design" |
| **Technology selection** — tidak memilih bahasa pemrograman, framework, atau database | Implementation Independence (Audit 7) |
| **Deployment mechanism** — tidak mendefinisikan container, orchestration, atau infrastruktur | ADR-000 L38: "topologi deployment tidak pernah ditetapkan oleh Foundation/Specification" |
| **Redesign** — tidak mengubah atau mendesain ulang komponen yang sudah ada | R3-004 Verdict A: Architecture Decision Layer Complete — semua keputusan sudah dibuat |
| **New decisions** — tidak membuat ADR baru, tidak mengubah ADR yang sudah ada | R3-004 Closure: Layer CLOSED — tidak ada celah keputusan tersisa |

**Anchor:** PHILOSOPHY; CONSTITUTION Article VII; GOVERNANCE Implementation Independence; R1-001.

---

# SECTION 2 — ARCHITECTURAL BOUNDARY

## 2.1 Inside Runtime

Komponen yang berada **di dalam** Runtime membentuk chain linear:

```
Citizen Host → Capability Manager → Discovery Resolver → Contract Enforcer
    → Approval Coordinator → Execution Scheduler → Audit Recorder
```

**Definisi "Inside":**
- Komponen yang menjalankan tanggung jawab bounded dari GOVERNANCE Runtime Governance
- Komponen yang berpartisipasi dalam chain linear R1-001 Component Interaction
- Komponen yang diatur oleh Specification beku (CITIZEN_SPEC, CAPABILITY_SPEC, REGISTRY_SPEC, CONTRACT_SPEC, APPROVAL_SPEC, EXECUTION_SPEC, AUDIT_SPEC)
- Komponen yang tunduk pada keputusan ADR-000..ADR-007

**Anchor:** R1-001 L65 ("Inside: the seven responsibility containers"); G0-001 Component Map; R1-001 R1-R10.

## 2.2 Outside Runtime

Komponen yang berada **di luar** Runtime adalah Citizens yang berinteraksi dengan Runtime melalui Contracts + Registry:

| Outside | Deskripsi |
|---|---|
| **Provider** | Mengimplementasikan akses ke sistem eksternal (LLM, database, API). Tidak memiliki kewenangan governance atas operasi Runtime. |
| **Connector** | Menjembatani komunikasi antara Runtime dan layanan eksternal. Tidak menjalankan governance Runtime. |
| **Citizen eksternal lain** | Agent, Runtime lain, atau entitas Citizen masa depan yang berinteraksi melalui mekanisme universal yang sama. |

**Anchor:** SAM_ARCHITECTURE L103; ADR-006 ("Provider dan Connector adalah Citizens di luar chain Runtime"); R1-001 L51 ("Runtime does not implement external access").

## 2.3 Boundary

External boundary didefinisikan oleh **Contracts + Registry** — dua mekanisme cross-boundary yang ditetapkan oleh baseline beku. Tidak ada mekanisme akses ketiga.

**Struktur Boundary:**

```
                  EXTERNAL                     |                     RUNTIME
                                               |
  Provider ←→ Contracts + Registry ←→ Boundary → Citizen Host → Capability Manager
  Connector ←→ Contracts + Registry ←→         → Discovery Resolver → Contract Enforcer
  Agent     ←→ Contracts + Registry ←→         → Approval Coordinator → Execution Scheduler
  Future    ←→ Contracts + Registry ←→         → Audit Recorder
```

**Prinsip Boundary:**
1. **Structural, bukan physical:** boundary didefinisikan oleh tipe interaksi (publish/discover/contract), bukan oleh lokasi fisik, jaringan, atau deployment. (ADR-006)
2. **Single surface:** Contracts + Registry membentuk permukaan (surface) Runtime — titik di mana domain internal Runtime berhenti dan dunia Citizen lainnya dimulai. (R1-001 L58/L65)
3. **Linear causality:** setiap interaksi melintasi chain Runtime (Registry → Contract → Approval → Execution → Audit) tanpa shortcut, tanpa side channel. (R1-001 L104/L116)
4. **Ownership separation:** Runtime memiliki bounded capability domain; Provider/Connector memiliki external access. Tidak ada tumpang tindih kepemilikan. (ADR-006)

**Anchor:** ADR-006; R1-001 L58, L65, L104, L116, L118; SAM_ARCHITECTURE; GOVERNANCE L198, L283.

---

# SECTION 3 — RUNTIME COMPONENTS

Runtime terdiri dari **7 komponen** — tidak ada komponen ke-8. Verification (C-08) bukan komponen; ia adalah state transition dalam lifecycle Audit (ADR-007).

## 3.1 Citizen Host

### Purpose
Citizen Host adalah unit pemerintahan (governing unit) Runtime — pemilik bounded capability domain, penanggung jawab publikasi Capability, sertifikasi, dan health Runtime.

### Responsibility
- R1: Own the Runtime's bounded capability domain
- R8: Support certification
- R9: Expose health
- Menerima seluruh interaksi yang memasuki Runtime dari luar (sebagai entry point)

### Inputs
- Capability Request dari Citizen eksternal
- Certification request
- Health probe

### Outputs
- Delegasi ke Capability Manager untuk publikasi Capability
- Certification status
- Health status

### Must
- Memiliki satu bounded capability domain (GOVERNANCE)
- Menerbitkan Capabilities (GOVERNANCE)
- Mengekspos health (GOVERNANCE)
- Mendukung sertifikasi (GOVERNANCE)
- Berinteraksi hanya melalui Contracts + Registry dengan entitas luar

### Must Not
- Mengimplementasikan external access (R1-001 R1-R10)
- Mengelola lifecycle Provider/Connector (ADR-006)
- Memverifikasi implementasi Provider/Connector
- Menyediakan SDK/API/protocol untuk integrasi eksternal

### Authority
- GOVERNANCE Runtime Governance
- CITIZEN_SPEC
- Adalah Citizen dalam konteks CITIZEN_SPEC

### Dependency
- Tidak memiliki dependency ke atas dalam chain
- Bergantung pada Constitution sebagai otoritas tertinggi

**Anchor:** R1-001 R1, R8, R9; G0-001; GOVERNANCE; ADR-006; CITIZEN_SPEC.

---

## 3.2 Capability Manager

### Purpose
Capability Manager mengelola publikasi, lifecycle, dan ketersediaan Capability yang dimiliki oleh Runtime.

### Responsibility
- R2: Publish capabilities (explicitly, discoverable, immutable)
- Mengelola lifecycle Capability (Declared → Registered → Certified → Available → Deprecated → Retired)
- Memastikan Capability published memiliki descriptor yang valid

### Inputs
- Capability declaration (dari Citizen Host)
- Lifecycle state transition request

### Outputs
- Published Capability (dengan descriptor + contract reference)
- Capability lifecycle state

### Must
- Menerbitkan Capability secara eksplisit, discoverable, immutable (GOVERNANCE)
- Setiap Capability memiliki descriptor lengkap (CAPABILITY_SPEC)
- Mengikuti Capability lifecycle: Declared → Registered → Certified → Available → Deprecated → Retired

### Must Not
- Mengeksekusi Capability — Registry tidak mengeksekusi
- Mendefinisikan ulang Capability — Capability didefinisikan oleh Capability Specification
- Menggantikan Registry — Registry yang melakukan discovery/resolution

### Authority
- CAPABILITY_SPEC

### Dependency
- Ke bawah: bergantung pada Citizen Host untuk deklarasi Capability
- Operasional: Capability Specification

**Anchor:** R1-001 R2; G0-001; CAPABILITY_SPEC; GOVERNANCE.

---

## 3.3 Discovery Resolver

### Purpose
Discovery Resolver menjawab pertanyaan: "diberikan Capability Request, Capability mana yang diterima oleh requester?" — melakukan discovery dan resolution terhadap Capability yang terdaftar.

### Responsibility
- R4: Discover & resolve capabilities
- Menerapkan kebijakan resolusi exact-preferred dengan fallback kompatibel deterministik (ADR-002)

### Inputs
- Capability Request (reference ke Capability yang diminta)

### Outputs
- Capability Descriptor (CAPABILITY_SPEC)
- Contract Reference
- Not Found / Version Mismatch / Error (defined failures)

### Must
- Discovery SHALL be idempotent (REGISTRY_SPEC L129)
- Discovery SHALL NOT have side effects (REGISTRY_SPEC)
- Resolusi SHALL deterministik (REGISTRY_SPEC L147/L149)
- Memilih exact match terlebih dahulu (ADR-002)
- Fallback ke version-compatible jika exact tidak ada (ADR-002)
- Tie-break deterministik via identitas + versi (ADR-002)
- Suspended/removed objects NOT candidates (REGISTRY_SPEC)
- Deprecated hanya dipilih jika tidak ada non-deprecated (REGISTRY_SPEC)
- Version-incompatible (major berbeda) tidak dipilih (REGISTRY_SPEC)

### Must Not
- Menjadi Approval — Registry tidak memutuskan apakah operasi diizinkan
- Menjadi Execution — Registry tidak menjalankan Capability
- Menjadi Runtime — Registry tidak memiliki atau mengeksekusi Runtime
- Menjadi Audit — Registry tidak merekam audit events
- Menjadi Contract — Registry tidak mendefinisikan Contracts
- Menerima konteks implisit — resolusi hanya dari Capability Request (ADR-002 D-17)

### Authority
- REGISTRY_SPEC
- ADR-002

### Dependency
- Ke bawah: bergantung pada Capability Manager yang mempublikasikan Capability ke Registry
- Operasional: REGISTRY_SPEC, ADR-002

**Anchor:** R1-001 R4; G0-001; REGISTRY_SPEC; ADR-002; CAPABILITY_SPEC.

---

## 3.4 Contract Enforcer

### Purpose
Contract Enforcer menyediakan immutable Contract yang mengatur struktur komunikasi antara dua Citizen — jaminan bahwa sender dan receiver sepakat pada bentuk interaksi tanpa berbagi implementasi.

### Responsibility
- R3: Expose immutable contracts
- Menyediakan Contract berdasarkan Contract Reference dari Discovery Resolver
- Menegakkan compatibility rules

### Inputs
- Contract Reference (dari Discovery Resolver)
- Version negotiation request

### Outputs
- Contract (Input, Output, Metadata, Constraints, Compatibility, Error)
- Negotiated version
- Negotiation failure (jika tidak ada versi kompatibel)

### Must
- Contract SHALL immutable (GOVERNANCE)
- Contract SHALL describe Input, Output, Metadata, Constraints, Compatibility, Error (CONTRACT_SPEC)
- Compatibility negotiation: kedua Citizen sepakat pada satu versi (CONTRACT_SPEC)
- Preferensi non-deprecated version (CONTRACT_SPEC)
- Contract mendeklarasikan idempotency operasi (ADR-003)
- Declare compatibility relative to predecessor (CONTRACT_SPEC)

### Must Not
- Mengeksekusi operasi — Contract tidak menjalankan
- Menyetujui operasi — Contract bukan Approval
- Menemukan Capability — Contract bukan Registry
- Mendefinisikan identitas Citizen — Contract bukan Citizen Specification

### Authority
- CONTRACT_SPEC
- ADR-003 (idempotency declaration)

### Dependency
- Ke bawah: bergantung pada Discovery Resolver untuk Contract Reference
- Operasional: CONTRACT_SPEC, ADR-003

**Anchor:** R1-001 R3; G0-001; CONTRACT_SPEC; ADR-003.

---

## 3.5 Approval Coordinator

### Purpose
Approval Coordinator adalah gerbang otorisasi antara intent dan execution — menghasilkan keputusan binding apakah suatu operasi boleh dijalankan.

### Responsibility
- R5: Produce authorization decision before execution
- Menerapkan Accountable Decision Framework (ADR-001)

### Inputs
- Approval Request: Decision Context + Referenced Contract + Referenced Capability (+ Referenced Citizen)

### Outputs
- Approval Decision: Approved / Rejected / Expired / Cancelled / Superseded
- Defined failures: Missing Contract / Unknown Capability / Registry Resolution Failed / Invalid Request / Expired Request / Approval Conflict

### Must
- Keputusan selalu mendahului eksekusi (gate, tidak boleh di-bypass) (APPROVAL_SPEC)
- Keputusan berbentuk deterministik dalam state tetap (APPROVAL_SPEC, ADR-001)
- Keputusan binding (APPROVAL_SPEC)
- Keputusan explainable dan auditable (ADR-001)
- Mekanisme terbuka: automated atau human-mediated, selama akuntabel (ADR-001)
- Mengikuti lifecycle: Created → Pending → Approved/Rejected/Expired → Archived

### Must Not
- Menjalankan operasi — Approval bukan Execution
- Menemukan Capability — Approval bukan Registry
- Mendefinisikan Contract — Approval bukan Contract
- Merekam audit — Approval bukan Audit
- Mem-bypass: tidak ada eksekusi tanpa Approval

### Authority
- APPROVAL_SPEC
- ADR-001

### Dependency
- Ke bawah: bergantung pada Contract Enforcer untuk Contract dan Capability yang di-resolve
- Operasional: APPROVAL_SPEC, ADR-001

**Anchor:** R1-001 R5; G0-001; APPROVAL_SPEC; ADR-001.

---

## 3.6 Execution Scheduler

### Purpose
Execution Scheduler menjalankan operasi yang sudah di-approve — melakukan (perform) tindakan yang dimandatkan oleh Approval, mengamati deklarasi idempotency, dan menerapkan strict linear ordering.

### Responsibility
- R6: Apply only approved operations (idempotent)
- Menerapkan Strict Linear Ordering berdasarkan urutan Approval (ADR-005)
- Mengamati deklarasi idempotency Contract (ADR-003)

### Inputs
- Approved operation (dari Approval Coordinator)
- Contract reference (untuk deklarasi idempotency)
- Execution identity

### Outputs
- Execution Result: Completed / Failed / Cancelled / Timed Out
- Defined failures: Missing Approval / Invalid Approval / Missing Contract / Capability Unavailable / Execution Timeout / Execution Failure / Execution Conflict
- Observable outcome (untuk Audit — EXECUTION_SPEC L206)

### Must
- Hanya mengeksekusi operasi yang sudah Approved (APPROVAL_SPEC, EXECUTION_SPEC)
- Strict Linear Ordering: Approval-arrival order → Execution order (ADR-005)
- Satu operasi mencapai state terminal sebelum operasi berikutnya dimulai (ADR-005)
- Mengamati deklarasi idempotency Contract (ADR-003)
- Idempotent → pengulangan sah; non-idempotent → Execution Conflict (ADR-003)
- Mengikuti lifecycle: Created → Queued → Running → Completed/Failed/Cancelled → Archived
- Execution does not record — hanya menghasilkan observable outcome (EXECUTION_SPEC L206)

### Must Not
- Mendefinisikan idempotency — itu milik Contract (ADR-003)
- Mengeksekusi tanpa Approval — invarian I6 (ADR-005)
- Menjalankan operasi di luar urutan Approval — Strict Linear (ADR-005)
- Merekam audit — Execution bukan Audit
- Memutuskan — Execution bukan Approval

### Authority
- EXECUTION_SPEC
- ADR-003
- ADR-005

### Dependency
- Ke bawah: bergantung pada Approval Coordinator untuk keputusan Approved
- Operasional: EXECUTION_SPEC, ADR-003, ADR-005

**Anchor:** R1-001 R6; G0-001; EXECUTION_SPEC; ADR-003; ADR-005.

---

## 3.7 Audit Recorder

### Purpose
Audit Recorder mengamati (observe) seluruh aktivitas Runtime dan merekamnya sebagai Audit Record — menjadikan eksekusi sebagai bukti (evidence), dirantai mundur (backward chain) ke seluruh komponen sebelumnya, dan melakukan verifikasi (Verification sebagai state transition) tanpa mempengaruhi outcome.

### Responsibility
- R7: Make activity traceable (backward chain)
- R10: Participate in auditing
- Menjalankan lifecycle Audit: Recorded → Verified → Archived (AUDIT_SPEC)
- Melakukan Verification sebagai state transition Recorded → Verified (ADR-007)

### Inputs
- Observable outcome dari Execution Scheduler (EXECUTION_SPEC L206)
- Execution identity + Contract reference + Registry reference (untuk traceability)
- Failure dari komponen upstream (jika terjadi — ADR-004)

### Outputs
- Audit Record dengan state: Recorded / Verified / Archived
- Traceability chain (mundur ke Execution → Approval → Contract → Registry → Capability → Citizen)
- Defined failures: Broken Traceability / Incomplete Record / Invalid Record / Duplicate Record

### Must
- Audit mengamati dan merekam (AUDIT_SPEC L193)
- Verification sebagai state transition Recorded → Verified (ADR-007, AUDIT_SPEC L114-L118)
- Traceability mundur tanpa broken link (AUDIT_SPEC, R1-001)
- Audit tidak memutuskan — "Audit is not Approval" (AUDIT_SPEC L30)
- Audit tidak mengeksekusi — "Audit is not Execution" (AUDIT_SPEC L32)
- Audit tidak mempengaruhi outcome — "Audit observes and records. It has no influence over what Execution produces" (AUDIT_SPEC L193)
- Audit adalah titik terminasi propagasi failure (ADR-004)
- Tidak ada feedback loop dari Audit ke komponen upstream (R1-001 L118)
- Mengikuti lifecycle: Recorded → Verified → Archived

### Must Not
- Menyetujui operasi — Audit bukan Approval
- Mengeksekusi operasi — Audit bukan Execution
- Mempengaruhi outcome eksekusi — no feedback (ADR-007, R1-001 L118)
- Meneruskan failure — Audit adalah titik terminasi (ADR-004)
- Menambahkan komponen/authority baru — Verification adalah state transition, bukan komponen (ADR-007)

### Authority
- AUDIT_SPEC
- ADR-004
- ADR-007

### Dependency
- Ke bawah: bergantung pada Execution Scheduler untuk observable outcome
- Ke bawah: menerima failure dari seluruh komponen upstream (ADR-004)
- Operasional: AUDIT_SPEC, ADR-004, ADR-007

**Anchor:** R1-001 R7, R10; G0-001; AUDIT_SPEC; ADR-004; ADR-007.

---

## 3.8 Tidak Ada Komponen Ke-8

Verification (C-08) **bukan komponen ke-8.** ADR-007 menetapkan Verification sebagai **Audit-observed State Transition** (Alternative B):
- Verification adalah transisi state `Recorded → Verified` dalam lifecycle Audit Record
- Dilakukan oleh Audit Recorder sebagai pengamatan (observation) terhadap Execution outcomes
- Menggunakan Contract + Registry references untuk traceability
- Tidak memodifikasi outcome, tidak memberi feedback, tidak menciptakan komponen/authority baru

**Anchor:** ADR-007; R3-004 Audit 4 ("ADR-007 adds no 8th component").

---

# SECTION 4 — RUNTIME INTERACTION MODEL

## 4.1 Chain Utama: The Linear Flow

Seluruh interaksi Runtime mengikuti chain linear tunggal:

```
Citizen
  ↓
Registry (Discovery Resolver + Capability Manager)
  ↓
Contract (Contract Enforcer)
  ↓
Approval (Approval Coordinator)
  ↓
Execution (Execution Scheduler)
  ↓
Verification (Audit Recorder: Recorded → Verified)
  ↓
Audit (Audit Recorder: Verified → Archived)
```

**Prinsip Chain:**
1. **Linear causality** — aliran satu arah dari Citizen ke Audit (R1-001 L104)
2. **No additional interaction invented** — tidak ada jalur samping (R1-001 L118)
3. **Separation of responsibility** — setiap komponen hanya menjalankan tanggung jawabnya sendiri
4. **Audit does not feed back** — tidak ada feedback loop (R1-001 L118)

**Anchor:** R1-001 L104, L118; G0-001 Interaction Flow; SAM_ARCHITECTURE Golden Rule.

## 4.2 Detailed Interaction Steps

### Step 1: Citizen → Discovery Resolver
- Citizen mengirimkan Capability Request
- Registry mengecek Capability yang terdaftar
- Discovery Resolver menerapkan kebijakan ADR-002 (exact-preferred → fallback kompatibel → tie-break deterministik)
- Output: Capability Descriptor + Contract Reference

### Step 2: Discovery Resolver → Contract Enforcer
- Contract Reference diteruskan ke Contract Enforcer
- Contract Enforcer menyediakan immutable Contract
- Jika version negotiation diperlukan: kedua Citizen sepakat pada satu versi
- Output: Contract (Input, Output, Metadata, Constraints, Compatibility, Error) + deklarasi idempotency

### Step 3: Contract Enforcer → Approval Coordinator
- Approval Request dibentuk: Decision Context + Referenced Contract + Referenced Capability (+ Referenced Citizen)
- Approval Coordinator mengevaluasi melalui Accountable Decision Framework (ADR-001)
- Decision Framework: deterministik dalam bentuk (state tetap), terbuka mekanisme (automated/human-mediated), explainable, auditable
- Output: Approval Decision (Approved / Rejected / Expired / Cancelled / Superseded)

### Step 4: Approval Coordinator → Execution Scheduler
- Hanya jika Approved → operasi diteruskan ke Execution Scheduler
- Execution Scheduler hanya menerima operasi yang sudah Approved (I6)
- Execution Scheduler mengamati deklarasi idempotency Contract (ADR-003)
- Execution Scheduler menerapkan Strict Linear Ordering: urutan Approval = urutan Execution (ADR-005)
- Operasi dieksekusi sampai state terminal (Completed/Failed/Cancelled)
- Output: Execution Result + observable outcome

### Step 5: Execution Scheduler → Audit Recorder (Recording)
- Audit Recorder mengamati observable outcome dari Execution
- Audit Record dibuat dengan state: Recorded
- Traceability mundur: Audit ← Execution ← Approval ← Contract ← Registry ← Capability ← Citizen — tanpa broken link

### Step 6: Audit Recorder — Verification
- Audit Recorder melakukan verifikasi: memeriksa traceability, memvalidasi record
- State transition: Recorded → Verified (ADR-007)
- Verification menggunakan Contract + Registry references untuk traceability
- Tidak mempengaruhi outcome eksekusi — no feedback

### Step 7: Audit Recorder — Archival
- Record yang sudah Verified di-archive
- State transition: Verified → Archived
- Archived adalah terminal state

## 4.3 Failure Propagation Path

Jika terjadi defined failure di komponen manapun, failure dipropagasikan ke depan menuju Audit Recorder:

```
Component → defined failure → Audit Recorder (terminasi)
```

**Aturan propagasi:**
- Setiap komponen mempropagasikan **hanya** failure yang ia produksi sendiri (ADR-004)
- Propagation mengikuti chain linear yang sudah ada — tidak menciptakan jalur baru
- Audit Recorder adalah titik terminasi — mencatat, tidak meneruskan (no feedback loop)
- Failure tetap observable dan traceable — jejak asal failure utuh dari produser hingga Audit Record

**Anchor:** ADR-004; AUDIT_SPEC L137-L150.

## 4.4 External Interaction Path

Seluruh interaksi dengan entitas di luar Runtime (Provider, Connector, Citizen lain) mengikuti jalur:

```
Citizen eksternal → Registry → Contract → [chain Runtime penuh] → Contract → Registry → Citizen eksternal
```

Atau sebaliknya:
```
[chain Runtime] → Contract → Registry → Provider/Connector
```

**Prinsip:**
- Tidak ada interaksi yang melewati (bypass) chain Runtime
- Approval, Execution, dan Audit selalu berlaku untuk seluruh operasi yang melintasi boundary
- Tidak ada side channel, tidak ada shortcut

**Anchor:** ADR-006; R1-001 L116.

---

# SECTION 5 — RUNTIME INVARIANTS

Seluruh invariant diekstraksi dari sumber yang sudah ada. Tidak ada invariant yang diciptakan.

## 5.1 Invariants dari Specification & Blueprint

| ID | Invariant | Sumber |
|---|---|---|
| **I1** | Approval → Execution sequential: Approval completes at the decision, Execution begins only after Approval completes | APPROVAL_SPEC L176-L179; EXECUTION_SPEC |
| **I2** | Registry is discovery/resolution only — bukan Approval, Execution, Runtime, Audit, atau Contract | REGISTRY_SPEC Boundaries |
| **I3** | Audit does not affect outcome — Audit observes and records, has no influence over what Execution produces | AUDIT_SPEC L193; R1-001 L118 |
| **I4** | Audit is not Approval — Audit does not decide | AUDIT_SPEC L30 |
| **I5** | Audit is not Execution — Audit does not perform | AUDIT_SPEC L32 |
| **I6** | Execution performs only after approval — no execution without approved Approval | EXECUTION_SPEC; APPROVAL_SPEC |
| **I7** | Registry SHALL select exactly one deterministically — dua Registry dengan isi dan request sama → hasil sama | REGISTRY_SPEC L147/L149 |
| **I8** | Approval completes → Execution begins — urutan temporal yang tak bisa dibalik | APPROVAL_SPEC L176 |
| **I9** | Capability shall be immutable, versioned, uniquely identifiable, discoverable, certifiable, auditable, implementation-independent | CAPABILITY_SPEC; CONSTITUTION |
| **I10** | Contract is immutable — tidak berubah antar operasi | CONTRACT_SPEC; GOVERNANCE |
| **I11** | Discovery SHALL be idempotent and without side effects | REGISTRY_SPEC L129 |
| **I12** | Approved Execution Flow (Golden Rule): Mission → Governance check → Approval → Execution → Verification → Audit | SAM_ARCHITECTURE L114 |
| **I13** | No additional interaction is invented — Audit does not feed back | R1-001 L118 |
| **I14** | Linear causality along the chain — aliran interaksi satu arah | R1-001 L104 |
| **I15** | Every Runtime shall own one bounded responsibility | GOVERNANCE Runtime Governance |
| **I16** | Citizens communicate through Capabilities — never through implementation | CAPABILITY_SPEC; CITIZEN_SPEC |
| **I17** | Boundary between Runtime and everything else = Contracts + Registry (dua mekanisme, tidak ada ketiga) | R1-001 L58; ADR-006 |
| **I18** | Every external interaction goes through Registry | R1-001 L116 |

## 5.2 Invariants dari ADR

| ID | Invariant | Sumber |
|---|---|---|
| **I19** | Single Cohesive Runtime per domain — satu Runtime menghosting semua 7 komponen | ADR-000 |
| **I20** | Approval decision deterministik dalam bentuk (state tetap: Approved/Rejected/Expired/Cancelled/Superseded), explainable, auditable | ADR-001 |
| **I21** | Registry exact-preferred: exact match diutamakan, fallback kompatibel, tie-break deterministik identitas+versi | ADR-002 |
| **I22** | Idempotency declared by Contract, observed by Execution — Contract defines, Execution reads | ADR-003 |
| **I23** | Idempotent → pengulangan sah; non-idempotent → Execution Conflict | ADR-003 |
| **I24** | Failure propagation linear → Audit — dari produser ke Audit Recorder sebagai terminasi, no feedback | ADR-004 |
| **I25** | Strict Linear Ordering: Approval-arrival order → Execution order — deterministik, traceable | ADR-005 |
| **I26** | External boundary = Contracts + Registry — tidak ada mekanisme akses ketiga | ADR-006 |
| **I27** | Verification as Audit-observed State Transition (Recorded → Verified) — out-of-chain, no new component, no feedback | ADR-007 |

---

# SECTION 6 — RUNTIME RESPONSIBILITY MATRIX

| # | Responsibility | Owner | Evidence |
|---|---|---|---|
| R1 | Own the Runtime's bounded capability domain | Citizen Host | GOVERNANCE Runtime Governance; R1-001 R1 |
| R2 | Publish capabilities (explicitly, discoverable, immutable) | Capability Manager | GOVERNANCE; CAPABILITY_SPEC; R1-001 R2 |
| R3 | Expose immutable contracts | Contract Enforcer | GOVERNANCE; CONTRACT_SPEC; R1-001 R3 |
| R4 | Discover & resolve capabilities | Discovery Resolver | REGISTRY_SPEC; ADR-002; R1-001 R4 |
| R5 | Produce authorization decision before execution | Approval Coordinator | APPROVAL_SPEC; ADR-001; R1-001 R5 |
| R6 | Apply only approved operations (idempotent) | Execution Scheduler | EXECUTION_SPEC; ADR-003; ADR-005; R1-001 R6 |
| R7 | Make activity traceable (backward chain) | Audit Recorder | AUDIT_SPEC; R1-001 R7 |
| R8 | Support certification | Citizen Host | GOVERNANCE; CITIZEN_SPEC; R1-001 R8 |
| R9 | Expose health | Citizen Host | GOVERNANCE; CITIZEN_SPEC; R1-001 R9 |
| R10 | Participate in auditing | Audit Recorder (observe) + all components (expose audit identity) | GOVERNANCE; R1-001 R10 |
| R11 | Contract declares idempotency | Contract Enforcer | ADR-003; CONTRACT_SPEC |
| R12 | Execution observes idempotency declaration | Execution Scheduler | ADR-003; EXECUTION_SPEC |
| R13 | Verification state transition (Recorded → Verified) | Audit Recorder | ADR-007; AUDIT_SPEC L114-L118 |
| R14 | Failure propagation to Audit | All upstream components → Audit Recorder | ADR-004 |
| R15 | External boundary enforcement via Contracts + Registry | Citizen Host + Discovery Resolver + Contract Enforcer | ADR-006; R1-001 L58, L116 |
| R16 | Resolution policy: exact-preferred → compatible fallback → tie-break | Discovery Resolver | ADR-002 |
| R17 | Strict Linear Ordering enforcement | Execution Scheduler | ADR-005 |
| R18 | Approval Decision Framework (deterministic form, open mechanism, explainable) | Approval Coordinator | ADR-001 |

**Verifikasi:**
- ✅ Tidak ada duplikasi — setiap responsibility memiliki tepat satu owner
- ✅ Tidak ada yang hilang — seluruh R1-R10 tercakup + tanggung jawab dari ADR
- ✅ Tidak ada responsibility baru — seluruhnya berasal dari sumber yang ada (GOVERNANCE, R1-001, Specification, ADR)

---

# SECTION 7 — RUNTIME BOUNDARIES

## 7.1 Internal Boundary

Internal boundary adalah batas antar komponen di dalam Runtime — setiap komponen memiliki bounded responsibility sendiri.

**Aturan:**
- Setiap komponen berinteraksi hanya dengan komponen yang berdekatan dalam chain
- Tidak ada komponen yang melompati komponen lain (skip)
- Tidak ada komunikasi lateral (side channel) antar komponen
- Setiap komponen hanya bergantung pada komponen "di atasnya" dalam chain

**Visual:**
```
[Citizen Host] → [Capability Manager] → [Discovery Resolver] → [Contract Enforcer]
                                                                        ↓
          [Audit Recorder] ← [Execution Scheduler] ← [Approval Coordinator]
```

**Anchor:** R1-001; G0-001 Dependency Diagram.

## 7.2 External Boundary

External boundary = Contracts + Registry — permukaan (surface) Runtime. Dua mekanisme, tidak ada yang ketiga.

**Aturan:**
- Seluruh akses dari/menuju Runtime melalui Contracts + Registry (ADR-006)
- Provider, Connector, dan Citizen eksternal hanya berinteraksi melalui mekanisme ini
- Tidak ada direct access ke komponen internal Runtime
- Tidak ada side channel

**Anchor:** ADR-006; R1-001 L58, L65.

## 7.3 Citizen Boundary

Citizen boundary memisahkan identitas dan tanggung jawab antar Citizen.

**Aturan:**
- Setiap Citizen memiliki identitas unik (CITIZEN_SPEC)
- Citizens berkomunikasi melalui Capabilities, tidak melalui implementasi (CAPABILITY_SPEC)
- Citizens tidak pernah mengasumsikan Citizen lain exists — mereka request Capability melalui Registry (CAPABILITY_SPEC)
- Satu Runtime = satu Citizen Host (ADR-000)

**Anchor:** CITIZEN_SPEC; CAPABILITY_SPEC; ADR-000.

## 7.4 Verification Boundary

Verification boundary memisahkan "apa yang sebenarnya terjadi" (Execution outcome) dari "apa yang tercatat sebagai bukti" (Audit Record verified).

**Aturan:**
- Verification terjadi di dalam Audit Recorder — state transition Recorded → Verified (ADR-007)
- Verification tidak mengubah Execution outcome
- Verification tidak memberi feedback ke Execution atau komponen lain
- Verification menggunakan Contract + Registry references untuk traceability
- Verification tidak menciptakan komponen/authority baru

**Anchor:** ADR-007; AUDIT_SPEC L114-L118, L193.

## 7.5 Failure Boundary

Failure boundary memisahkan "tempat failure terjadi" (komponen produser) dari "tempat failure dicatat" (Audit Recorder).

**Aturan:**
- Setiap komponen hanya mempropagasikan failure yang ia produksi sendiri (ADR-004)
- Propagation linear sepanjang chain — dari produser ke Audit Recorder
- Audit Recorder adalah titik terminasi — mencatat, tidak meneruskan
- Tidak ada feedback loop dari failure di Audit kembali ke komponen upstream

**Anchor:** ADR-004.

## 7.6 Deployment Boundary

Deployment boundary memisahkan "apa yang didefinisikan arsitektur" dari "bagaimana arsitektur dideploy."

**Aturan:**
- Topologi deployment tidak ditetapkan oleh Foundation/Specification (ADR-000 L38)
- Satu Runtime cohesive per domain — semua 7 komponen dalam satu Runtime (ADR-000)
- Deployment topology adalah keputusan implementasi, bukan arsitektur
- Arsitecture valid regardless of deployment topology (GOVERNANCE Long-Term Governance)

**Anchor:** ADR-000; GOVERNANCE.

---

# SECTION 8 — RUNTIME DECISION SUMMARY

| ADR | Decision | Affected Component | Architectural Effect |
|---|---|---|---|
| **ADR-000** | Single Cohesive Reference Runtime — satu Runtime menghosting semua 7 komponen per domain | Semua (topologi) | Arsitecture cohesive per domain; komponen tidak terdistribusi lintas host |
| **ADR-001** | Accountable Decision Framework — Approval deterministik dalam bentuk (state tetap), terbuka mekanisme (auto/human), explainable, auditable | Approval Coordinator | Menetapkan model keputusan Approval tanpa memilih mekanisme spesifik |
| **ADR-002** | Exact-preferred dengan fallback kompatibel deterministik — exact match → version-compatible → tie-break identitas+versi | Discovery Resolver | Resolution policy untuk Registry; deterministik, idempoten, tanpa konteks implisit |
| **ADR-003** | Operation-Defined Semantics — idempotency dideklarasikan Contract, diamati Execution | Contract Enforcer + Execution Scheduler | Contract declares, Execution observes; idempotent → pengulangan sah |
| **ADR-004** | Linear Failure Propagation — dari komponen produser ke Audit Recorder sebagai terminasi | Semua (failure path) | Failure disurfacing ke Audit tanpa feedback loop, tanpa jalur baru |
| **ADR-005** | Strict Linear Ordering — urutan Approval = urutan Execution | Execution Scheduler | Execution deterministik dan traceable; operasi dieksekusi satu per satu |
| **ADR-006** | Runtime Boundary via Contracts + Registry — tidak ada mekanisme akses ketiga | Citizen Host + Discovery Resolver + Contract Enforcer | External boundary struktural; Provider/Connector di luar chain |
| **ADR-007** | Verification sebagai Audit-observed State Transition (Recorded → Verified) — out-of-chain | Audit Recorder | Verification bukan komponen baru; dilakukan oleh Audit melalui lifecycle state |

---

# SECTION 9 — RUNTIME DEPENDENCY GRAPH

## 9.1 Dependency Direction

```
                    CONSTITUTION
                         |
                    GOVERNANCE
                         |
              ┌──────────┼──────────┐
              ↓          ↓          ↓
       CITIZEN_SPEC  CAPABILITY_SPEC  (Foundation)
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
              ADR-000..007 (semua bergantung pada spec masing-masing)
                   ↓
            R4-001 Reference Runtime Architecture (this document)
```

## 9.2 Component Dependency

```
Citizen Host
    ↓
Capability Manager
    ↓
Discovery Resolver
    ↓
Contract Enforcer
    ↓
Approval Coordinator
    ↓
Execution Scheduler
    ↓
Audit Recorder
```

**Verifikasi:**
- ✅ Acyclic — tidak ada cycle, semua dependensi satu arah ke bawah
- ✅ Single direction — setiap komponen hanya bergantung pada komponen di atasnya
- ✅ Authority preserving — tidak ada komponen yang mengambil otoritas komponen lain
- ✅ Audit Recorder adalah leaf node — tidak ada komponen yang bergantung padanya

**Anchor:** G0-001 Dependency Diagram; R1-001.

## 9.3 ADR Dependency Matrix

| ADR | Bergantung pada (spec) | Bergantung pada (ADR) |
|---|---|---|
| ADR-000 | GOVERNANCE, REGISTRY_SPEC | — (root ADR) |
| ADR-001 | APPROVAL_SPEC, GOVERNANCE | ADR-000 |
| ADR-002 | REGISTRY_SPEC | ADR-000, ADR-001 |
| ADR-003 | EXECUTION_SPEC, CONTRACT_SPEC | ADR-000, ADR-001, ADR-002 |
| ADR-004 | AUDIT_SPEC, seluruh spec komponen | ADR-000..ADR-003 |
| ADR-005 | EXECUTION_SPEC, APPROVAL_SPEC | ADR-000, ADR-001, ADR-003 |
| ADR-006 | R1-001, SAM_ARCHITECTURE, GOVERNANCE | ADR-000 |
| ADR-007 | AUDIT_SPEC, EXECUTION_SPEC | ADR-000..ADR-006 |

✅ Verified: 28/28 pairwise ADR pairs consistent (R3-004 Audit 3)

---

# SECTION 10 — RUNTIME LIFECYCLE

## 10.1 Tidak Ada State Agregat Runtime

Runtime sebagai keseluruhan **tidak memiliki lifecycle state agregat** — tidak ada "Runtime Created," "Runtime Running," "Runtime Stopped" dalam Specification. Specification mendefinisikan lifecycle **per-komponen**, bukan lifecycle Runtime agregat.

## 10.2 Lifecycle Per-Komponen

| Komponen | Lifecycle | Sumber |
|---|---|---|
| **Capability** | Declared → Registered → Certified → Available → Deprecated → Retired | CAPABILITY_SPEC |
| **Registry Object** | Register → Update → Deprecate → Suspend → Remove | REGISTRY_SPEC |
| **Approval** | Created → Pending → Approved/Rejected/Expired/Cancelled → Archived | APPROVAL_SPEC |
| **Execution** | Created → Queued → Running → Completed/Failed/Cancelled/Timed Out → Archived | EXECUTION_SPEC |
| **Audit Record** | Recorded → Verified → Archived | AUDIT_SPEC |

## 10.3 Lifecycle Transisi yang Didukung

### Capability Lifecycle
```
Declared → Registered → Certified → Available → Deprecated → Retired
```
- Registered: Capability tercatat di Registry
- Certified: Capability lulus sertifikasi (descriptor integrity, contract validity, determinism, dll.)
- Available: Capability siap digunakan
- Deprecated: tetap discoverable, tidak dipilih jika ada non-deprecated
- Retired: dihapus dari active discovery

### Registry Object Lifecycle
```
Register → Update → Deprecate / Suspend
Update → Deprecate / Suspend
Deprecate → Suspend
Suspend → Register / Update
→ Remove (terminal)
```
- Suspended: tidak discoverable untuk request baru, tetap traceable
- Removed: terminal, tidak bisa transisi ke state lain

### Approval Lifecycle
```
Created → Pending → Approved / Rejected / Expired / Cancelled
Approved → Expired / Archived
Rejected / Expired / Cancelled → Archived
```
- Archived: terminal

### Execution Lifecycle
```
Created → Queued → Running → Completed / Failed / Cancelled / Timed Out
Completed / Failed / Cancelled → Archived
```
- Archived: terminal
- Timed Out: dari Running state

### Audit Record Lifecycle
```
Recorded → Verified → Archived
```
- Recorded: Audit Record dibuat, traceability chain tercatat
- Verified: verifikasi selesai — traceability valid, record lengkap (ADR-007)
- Archived: terminal

---

# SECTION 11 — RUNTIME FAILURE MODEL

## 11.1 Sumber Failure

Setiap komponen mendefinisikan failure-nya sendiri melalui Specification:

| Komponen | Defined Failures | Sumber |
|---|---|---|
| **Registry** | Citizen missing, Capability not found, Descriptor corrupted, Version not compatible | REGISTRY_SPEC L164-L173 |
| **Approval** | Missing Contract, Unknown Capability, Registry Resolution Failed, Invalid Request, Expired Request, Approval Conflict | APPROVAL_SPEC L142-L155 |
| **Execution** | Missing Approval, Invalid Approval, Missing Contract, Capability Unavailable, Execution Timeout, Execution Failure, Execution Conflict (via ADR-003) | EXECUTION_SPEC L150-L163; ADR-003 |
| **Audit** | Broken Traceability, Incomplete Record, Invalid Record, Duplicate Record | AUDIT_SPEC L137-L150 |

## 11.2 Propagation Model

Propagation linear: dari komponen produser → Audit Recorder (terminasi).

```
Registry failure → Contract → Approval → Execution → Audit
Approval failure → Execution → Audit
Execution failure → Audit
```

**Aturan (ADR-004):**
- Setiap komponen mempropagasikan HANYA failure yang ia produksi sendiri
- Propagation mengikuti chain linear yang sudah ada — tidak menciptakan jalur interaksi baru
- Audit Recorder adalah titik terminasi — mencatat, tidak meneruskan
- No feedback loop — failure di Audit tidak kembali ke upstream

## 11.3 Failure Boundary

| Failure di | Sampai ke | Tercatat di |
|---|---|---|
| Registry | Contract → Approval → Execution → Audit | Audit Record |
| Contract | Approval → Execution → Audit | Audit Record |
| Approval | Execution → Audit | Audit Record |
| Execution | Audit | Audit Record |
| Audit | — (terminasi) | Audit Record |

## 11.4 Observability

Semua failure observable — defined oleh Specification, dipropagasikan, dan dicatat di Audit Record. Tidak ada silent failure. Traceability asal failure utuh dari produser hingga Audit Record.

---

# SECTION 12 — IMPLEMENTATION INDEPENDENCE

Reference Runtime Architecture **tidak bergantung** pada:

| Dependency | Bukti Independence |
|---|---|
| **Language** | Tidak ada referensi ke bahasa pemrograman spesifik (Python, Java, Go, dll). COMPONENTS didefinisikan dalam responsibility, bukan class/interface. EXECUTION_SPEC: "does not prescribe how the result is computed." REGISTRY_SPEC: "does not prescribe a storage or matching algorithm." |
| **Framework** | Tidak ada referensi ke framework. Governance: "Implementation may evolve. Architecture should remain stable." |
| **Database** | Tidak ada referensi ke database engine atau storage mechanism. Registry menyimpan "references to objects," bukan skema database. |
| **OS** | Tidak ada referensi ke sistem operasi. ADR-000: topologi deployment tidak ditetapkan oleh Foundation/Specification. |
| **Network** | Tidak ada referensi ke protokol jaringan. Interaction model didefinisikan sebagai "responsibility references," bukan technical payloads. |
| **Serialization** | Tidak ada referensi ke format serialisasi (JSON, protobuf, XML, dll). CONTRACT_SPEC: "This specification does not mandate JSON, protobuf, or any other representation." |
| **Deployment Platform** | Tidak ada referensi ke container, orchestration, cloud provider. GOVERNANCE Long-Term Governance: governance valid "regardless of deployment topology." |

**Verifikasi tambahan:**
- ADR tidak memilih mekanisme teknis — hanya menetapkan kebijakan dan prinsip arsitektural
- Specification mendefinisikan behavior, bukan implementasi
- Blueprint mendefinisikan komponen dan tanggung jawab, bukan class atau package
- R1-001 mendefinisikan responsibility containers, bukan technical modules

**Kesimpulan:** Reference Runtime Architecture dapat diimplementasikan dalam bahasa, framework, database, OS, network protocol, serialization format, dan deployment platform apapun — selama behavior yang didefinisikan oleh Specification, ADR, dan arsitektur ini terpenuhi.

---

# SECTION 13 — OUT OF SCOPE

| Area | Status | Rasional |
|---|---|---|
| **Class / Package design** | Out of scope | Arsitektur, bukan implementasi |
| **API / Interface definition** | Out of scope | Arsitektur mendefinisikan responsibility, bukan technical interface |
| **Protocol implementation** | Out of scope | Interaction model = responsibility references, bukan technical payloads |
| **Pseudocode / Algorithm** | Out of scope | Architecture only |
| **Serialization format** | Out of scope | CONTRACT_SPEC: "does not mandate any representation" |
| **Database schema** | Out of scope | Registry menyimpan references, bukan skema |
| **Concurrency model** | Out of scope | ADR-005 menetapkan ordering, bukan concurrency mechanism |
| **Retry / Recovery strategy** | Out of scope | Mekanisme implementasi, bukan arsitektur |
| **Timeout / Circuit breaker** | Out of scope | Operational resilience = implementasi |
| **Deployment mechanism** | Out of scope | ADR-000: topologi deployment tidak ditetapkan |
| **Technology selection** | Out of scope | Implementation Independence (Section 12) |
| **Monitoring dashboard / UI** | Out of scope | Presentation layer |
| **SDK / Client library** | Out of scope | Consumer tooling, bukan arsitektur Runtime |
| **Performance optimization** | Out of scope | Bukan ranah arsitektur |
| **Scaling strategy** | Out of scope | ADR-000: scaling adalah keputusan deployment |
| **Security implementation** | Out of scope | Arsitektur mendefinisikan separation of responsibility, bukan mekanisme keamanan spesifik |

---

# VALIDATION

## Audit 1 — Component Completeness

**Pertanyaan:** Apakah seluruh komponen Runtime terdefinisi?

| Komponen | Defined? | Section | Evidence |
|---|---|---|---|
| Citizen Host | ✅ | 3.1 | R1-001 R1, R8, R9; G0-001 |
| Capability Manager | ✅ | 3.2 | R1-001 R2; G0-001 |
| Discovery Resolver | ✅ | 3.3 | R1-001 R4; G0-001 |
| Contract Enforcer | ✅ | 3.4 | R1-001 R3; G0-001 |
| Approval Coordinator | ✅ | 3.5 | R1-001 R5; G0-001 |
| Execution Scheduler | ✅ | 3.6 | R1-001 R6; G0-001 |
| Audit Recorder | ✅ | 3.7 | R1-001 R7, R10; G0-001 |

**Hasil:** ✅ LULUS — 7/7 komponen terdefinisi lengkap. Tidak ada komponen ke-8.

---

## Audit 2 — Responsibility Integrity

**Pertanyaan:** Apakah setiap responsibility memiliki owner, tidak ada duplikasi, tidak ada yang hilang?

| Responsibility | Owner | Evidence |
|---|---|---|
| R1-R10 | Citizen Host (R1,R8,R9), Capability Manager (R2), Contract Enforcer (R3), Discovery Resolver (R4), Approval Coordinator (R5), Execution Scheduler (R6), Audit Recorder (R7,R10) | R1-001 |
| Idempotency declaration | Contract Enforcer | ADR-003 |
| Idempotency observation | Execution Scheduler | ADR-003 |
| Verification (C-08) | Audit Recorder | ADR-007 |
| Failure propagation | All upstream → Audit Recorder | ADR-004 |
| External boundary | Citizen Host + Discovery Resolver + Contract Enforcer | ADR-006 |
| Resolution policy | Discovery Resolver | ADR-002 |
| Strict Linear Ordering | Execution Scheduler | ADR-005 |
| Accountable Decision Framework | Approval Coordinator | ADR-001 |

**Hasil:** ✅ LULUS — 18 responsibility, 7 owner, 0 duplikasi, 0 missing.

---

## Audit 3 — ADR Consistency

**Pertanyaan:** Apakah seluruh ADR konsisten dengan Reference Runtime Architecture?

| ADR | Decision | Consistent in R4-001? |
|---|---|---|
| ADR-000 | Single Cohesive Runtime per domain | ✅ Section 2.1, 3.8 |
| ADR-001 | Accountable Decision Framework | ✅ Section 3.5, 4.2 Step 3 |
| ADR-002 | Exact-preferred + fallback kompatibel deterministik | ✅ Section 3.3, 4.2 Step 1 |
| ADR-003 | Idempotency: Contract declares, Execution observes | ✅ Section 3.4, 3.6, 4.2 Step 4 |
| ADR-004 | Linear failure propagation → Audit terminasi | ✅ Section 4.3, 11.2 |
| ADR-005 | Strict Linear Ordering (Approval-arrival order) | ✅ Section 3.6, 4.2 Step 4 |
| ADR-006 | Boundary = Contracts + Registry | ✅ Section 2.3, 4.4, 7.2 |
| ADR-007 | Verification as Audit-observed State Transition | ✅ Section 3.7, 4.2 Step 6, 7.4 |

**Hasil:** ✅ LULUS — 8/8 ADR konsisten; 0 kontradiksi.

---

## Audit 4 — Specification Compliance

**Pertanyaan:** Apakah Reference Runtime Architecture mematuhi seluruh Specification?

| Specification | Key Rule | Compiled in R4-001? |
|---|---|---|
| CITIZEN_SPEC | Identity, Capability publication, certification, health | ✅ Section 3.1, 7.3 |
| CAPABILITY_SPEC | Immutable, versioned, discoverable, lifecycle | ✅ Section 3.2 |
| REGISTRY_SPEC | Discovery/resolution, deterministic, idempotent, no side effects | ✅ Section 3.3 |
| CONTRACT_SPEC | Structure, compatibility, version negotiation | ✅ Section 3.4 |
| APPROVAL_SPEC | Gate, binding decision, defined states, lifecycle | ✅ Section 3.5 |
| EXECUTION_SPEC | Perform only, lifecycle, idempotency, defined failures | ✅ Section 3.6 |
| AUDIT_SPEC | Record, traceability, lifecycle Recorded→Verified→Archived, no outcome influence | ✅ Section 3.7 |

**Hasil:** ✅ LULUS — seluruh 7 Specification complied.

---

## Audit 5 — Foundation Compliance

**Pertanyaan:** Apakah Reference Runtime Architecture mematuhi Foundation (Constitution, Governance, Mission, Philosophy)?

| Foundation Document | Key Principle | Compiled in R4-001? |
|---|---|---|
| CONSTITUTION | Determinism (Art. VII), bounded responsibility, integrity | ✅ Section 5 (I1, I7, I9), Section 3 |
| GOVERNANCE | Runtime Governance (one bounded responsibility, publish capabilities, immutable contracts, certification, health, auditing) | ✅ Section 3, Section 6 (R1-R10) |
| GOVERNANCE | Long-Term Governance (valid regardless of deployment topology) | ✅ Section 7.6, 12 |
| MISSION | Project purpose | ✅ Section 1.2 |
| PHILOSOPHY | Why Determinism Matters, Implementation Independence | ✅ Section 12 |

**Hasil:** ✅ LULUS — Foundation complied.

---

## Audit 6 — Authority Integrity

**Pertanyaan:** Apakah chain otoritas terjaga — tidak ada reverse dependency, tidak ada circular authority, tidak ada authority leakage?

**Chain:**
```
Constitution → Governance → Architecture → Specification → ADR → Reference Runtime → Implementation
```

**Verifikasi:**
- ✅ Constitution adalah puncak — tidak ada yang di atasnya
- ✅ Specification tidak mengubah Constitution
- ✅ ADR tidak mengubah Specification (R2-001 Audit 5)
- ✅ Reference Runtime tidak mengubah ADR, Specification, atau Foundation
- ✅ Reference Runtime tidak menciptakan authority baru
- ✅ Dependency graph acyclic, single direction (Section 9)
- ✅ Tidak ada component yang mengambil otoritas component lain

**Hasil:** ✅ LULUS — authority chain intact.

---

## Audit 7 — Implementation Independence

**Pertanyaan:** Apakah Reference Runtime Architecture bebas dari ketergantungan implementasi?

| Aspek | Status | Evidence |
|---|---|---|
| Language | ✅ Independent | Section 12 |
| Framework | ✅ Independent | Section 12 |
| Database | ✅ Independent | Section 12 |
| OS | ✅ Independent | Section 12 |
| Network | ✅ Independent | Section 12 |
| Serialization | ✅ Independent | Section 12 |
| Deployment Platform | ✅ Independent | Section 12 |

**Hasil:** ✅ LULUS — architecture is implementation-independent.

---

## Audit 8 — Architecture Readiness

**Pertanyaan:** Apakah Reference Runtime Architecture siap menjadi baseline untuk R4?

**Kriteria:**
1. ✅ Seluruh 7 komponen terdefinisi lengkap (Section 3)
2. ✅ Interaction model utuh — Citizen ke Audit, mencakup Verification (Section 4)
3. ✅ 27 invariant terekstraksi tanpa menciptakan yang baru (Section 5)
4. ✅ 18 responsibility dengan owner, 0 duplikasi, 0 missing (Section 6)
5. ✅ 6 boundary terdefinisi (Section 7)
6. ✅ 8 ADR decision dirangkum (Section 8)
7. ✅ Dependency graph acyclic, single direction (Section 9)
8. ✅ Lifecycle per-komponen didokumentasikan — state agregat Runtime explicitly declared NOT EXIST (Section 10)
9. ✅ Failure model lengkap: sumber, propagation, termination, observability (Section 11)
10. ✅ Implementation independence terbukti (Section 12)
11. ✅ 15 area out-of-scope explicitly listed (Section 13)
12. ✅ 8 audit lulus semua (Validation)

**Hasil:** ✅ LULUS — Architecture Ready. Reference Runtime Architecture complete dan siap sebagai baseline R4.

---

# STOP CONDITION

**STOP Status:** NOT ACTIVE

**Verifikasi:**
- ✅ Tidak membutuhkan ADR baru — 8 ADR Accepted mencakup seluruh Candidate Blueprint (R3-004 Verdict A)
- ✅ Tidak membutuhkan perubahan ADR — seluruh ADR konsisten (Audit 3)
- ✅ Tidak membutuhkan perubahan Specification — seluruh spec complied (Audit 4)
- ✅ Tidak membutuhkan perubahan Foundation — seluruh foundation complied (Audit 5)
- ✅ Tidak membutuhkan authority baru — authority chain intact (Audit 6)
- ✅ Tidak membutuhkan komponen baru — 7 komponen lengkap, tidak ada ke-8 (Audit 1)

---

**END OF R4-001 — Reference Runtime Architecture**
