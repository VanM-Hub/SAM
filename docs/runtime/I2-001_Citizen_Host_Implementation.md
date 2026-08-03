# I2-001 — Citizen Host Reference Implementation

**Document ID:** I2-001
**Title:** Citizen Host Reference Implementation
**Status:** Completed
**Date:** 2026-08-03
**Author:** Chief Architect (Project SAM Architecture Decision Making)
**Audience:** Implementation Team, Engineering, Architecture
**Source of Authority:** Foundation | Specification (CITIZEN_SPEC) | Blueprint (G0-001) | ADR-000..ADR-007 | R4-001 | R4-002 | R5-001 | I0-001 | I1-001
**Derived From:** I0-001 Reference Runtime Implementation Blueprint, I1-001 Repository Skeleton
**Implementation Target:** `src/sam/runtime/citizen_host/`

---

# Executive Summary

I2-001 adalah **implementasi Unit pertama** dari Reference Runtime: **Citizen Host** — unit permukaan (surface) Runtime yang menjadi titik masuk seluruh interaksi eksternal.

**Ini adalah implementasi nyata pertama** — kode Python. Bukan skeleton. Bukan desain. Bukan blueprint.

```
R4-001 Architecture     →  "Apa komponen?"
R4-002 Design           →  "Bagaimana strukturnya?"
R5-001 Engineering      →  "Bagaimana unitnya?"
I0-001 Blueprint        →  "Apa kontrak codingnya?"
I1-001 Skeleton         →  "Di mana kodenya?"
I2-001 Citizen Host     →  "Kode unit pertama" ◀ ANDA DI SINI
   ↓
I2-002 ...              →  "Kode unit berikutnya"
```

**Apa yang diimplementasikan:**
- Seluruh responsibility Citizen Host dari R4/R5/I0
- 8 file source (+ 7 package inits)
- 5 file unit test skeleton (+ 1 package init)
- Minimal shared infrastructure stubs (shared/, contracts/, registry/)

---

# SECTION 1 — IMPLEMENTATION RESPONSIBILITY

## 1.1 Responsibility Turunan

| # | Responsibility | Source | Implementation |
|---|---|---|---|
| R1 | Own bounded capability domain | GOVERNANCE, CITIZEN_SPEC | `models/domain.py` — BoundedCapabilityDomain |
| R8 | Support certification | GOVERNANCE | `services/certification_service.py` |
| R9 | Expose health | GOVERNANCE | `services/health_service.py` |
| — | Boundary enforcement (Contracts + Registry) | ADR-006 | `validation/boundary_validator.py` |
| — | Entry point delegation | R5-001, I0-001 | `interfaces/host_interface.py`, `services/host_service.py` |

## 1.2 Responsibility Yang TIDAK Diimplementasikan

| Bukan Tanggung Jawab | Kenapa |
|---|---|
| External access implementation | Milik Provider/Connector (ADR-006) |
| Provider/Connector lifecycle | Di luar Runtime boundary |
| SDK/API/protocol | Architecture forbidden |
| Capability execution | Milik Execution Scheduler (unit 6) |
| Approval decisions | Milik Approval Coordinator (unit 5) |
| Audit recording | Milik Audit Recorder (unit 7) |

---

# SECTION 2 — PUBLIC CONTRACT

## 2.1 HostInterface

Citizen Host mengekspos satu public interface — `HostInterface` — sebagai surface unit Runtime.

```
HostInterface:
  ┌────────────────────────────────────────────┐
  │  accept_request(capability_request)         │
  │      → delegasi ke Capability Manager       │
  │                                             │
  │  get_health()                               │
  │      → HealthStatus                         │
  │                                             │
  │  request_certification(cert_request)        │
  │      → CertificationStatus                  │
  │                                             │
  │  get_domain()                               │
  │      → BoundedCapabilityDomain              │
  └────────────────────────────────────────────┘
```

## 2.2 Contract Semantics

| Operasi | Input | Output | Delegasi ke |
|---|---|---|---|
| `accept_request` | CapabilityRequest (identity + version) | DelegationResult | Capability Manager |
| `get_health` | — | HealthStatus (available/degraded/unavailable) | — |
| `request_certification` | CertificationRequest | CertificationStatus (certified/not-certified/pending) | — (internal) |
| `get_domain` | — | BoundedCapabilityDomain | — (internal) |

## 2.3 Boundary Access Validation

Setiap request yang masuk HARUS melalui Contracts + Registry. `BoundaryValidator` memvalidasi bahwa request:

1. Berasal dari Contracts + Registry (ADR-006)
2. Tidak mengandung direct access ke unit lain
3. Tidak mencoba bypass entry point

Jika validasi gagal → `InvalidBoundaryAccess` error.

---

# SECTION 3 — INTERNAL STRUCTURE

## 3.1 Package Structure

```
citizen_host/
├── __init__.py                       # Package exports
├── models/                           # Data models
│   ├── __init__.py
│   ├── domain.py                     # BoundedCapabilityDomain
│   ├── health.py                     # HealthStatus
│   └── certification.py              # CertificationStatus, CertificationRequest
├── interfaces/                       # Public-facing interfaces
│   ├── __init__.py
│   └── host_interface.py             # HostInterface — surface entry point
├── services/                         # Business logic
│   ├── __init__.py
│   ├── host_service.py               # Main service orchestrator
│   ├── health_service.py             # Health computation
│   └── certification_service.py      # Certification processing
├── lifecycle/                        # Lifecycle management
│   ├── __init__.py
│   └── host_lifecycle.py             # Host lifecycle state machine
├── validation/                       # Boundary validation
│   ├── __init__.py
│   └── boundary_validator.py         # Contracts + Registry boundary check
└── exceptions/                       # Domain exceptions
    ├── __init__.py
    └── boundary_errors.py            # InvalidBoundaryAccess + variants
```

## 3.2 Layer Dependencies

```
interfaces/host_interface.py
  → services/host_service.py
    → services/health_service.py
    → services/certification_service.py
    → validation/boundary_validator.py
      → exceptions/boundary_errors.py
      → models/domain.py
    → lifecycle/host_lifecycle.py
      → models/health.py
```

Semua layer bergantung ke `models/` (data) — tidak ada yang bergantung ke atas.

---

# SECTION 4 — IMPLEMENTATION FILES

## 4.1 models/domain.py

| Property | Value |
|---|---|
| **Purpose** | BoundedCapabilityDomain — identitas Runtime sebagai Citizen |
| **Responsibility** | Mendefinisikan struktur domain yang dimiliki oleh Citizen Host |
| **Depends On** | — (pure model, no internal deps) |
| **Must Not Depend On** | services/, interfaces/, lifecycle/, validation/, exceptions/ |
| **Exports** | `BoundedCapabilityDomain` |

## 4.2 models/health.py

| Property | Value |
|---|---|
| **Purpose** | HealthStatus — status kesehatan Runtime |
| **Responsibility** | Mendefinisikan enum state: AVAILABLE, DEGRADED, UNAVAILABLE |
| **Depends On** | — (pure model) |
| **Must Not Depend On** | services/, interfaces/, lifecycle/, validation/, exceptions/ |
| **Exports** | `HealthStatus` |

## 4.3 models/certification.py

| Property | Value |
|---|---|
| **Purpose** | CertificationStatus + CertificationRequest |
| **Responsibility** | Mendefinisikan struktur sertifikasi |
| **Depends On** | — (pure model) |
| **Must Not Depend On** | services/, interfaces/, lifecycle/, validation/, exceptions/ |
| **Exports** | `CertificationStatus`, `CertificationRequest` |

## 4.4 interfaces/host_interface.py

| Property | Value |
|---|---|
| **Purpose** | Public surface — entry point tunggal ke Citizen Host |
| **Responsibility** | Menerima seluruh interaksi eksternal, mendelegasikan ke services |
| **Depends On** | models/domain, services/host_service |
| **Must Not Depend On** | capability_manager, discovery_resolver, contract_enforcer, approval_coordinator, execution_scheduler, audit_recorder, internal |
| **Exports** | `HostInterface` |

## 4.5 services/host_service.py

| Property | Value |
|---|---|
| **Purpose** | Orchestrator — mengkoordinasikan seluruh service Citizen Host |
| **Responsibility** | Delegasi request, orkestrasi health+certification+boundary |
| **Depends On** | models/*, services/health_service, services/certification_service, validation/boundary_validator, lifecycle/host_lifecycle |
| **Must Not Depend On** | interfaces/ (called by it, not calling it) |
| **Exports** | `HostService` |

## 4.6 services/health_service.py

| Property | Value |
|---|---|
| **Purpose** | Komputasi health status Runtime |
| **Responsibility** | Menghasilkan HealthStatus: AVAILABLE / DEGRADED / UNAVAILABLE |
| **Depends On** | models/health, lifecycle/host_lifecycle |
| **Must Not Depend On** | Any external module |
| **Exports** | `HealthService` |

## 4.7 services/certification_service.py

| Property | Value |
|---|---|
| **Purpose** | Pemrosesan certification request |
| **Responsibility** | Menerima CertificationRequest, menghasilkan CertificationStatus |
| **Depends On** | models/certification, lifecycle/host_lifecycle |
| **Must Not Depend On** | Any external module |
| **Exports** | `CertificationService` |

## 4.8 lifecycle/host_lifecycle.py

| Property | Value |
|---|---|
| **Purpose** | Host lifecycle state machine |
| **Responsibility** | State: UNINITIALIZED → INITIALIZING → RUNNING → DEGRADED → STOPPING → STOPPED |
| **Depends On** | — |
| **Must Not Depend On** | services/, interfaces/, validation/, exceptions/ |
| **Exports** | `HostLifecycleState`, `HostLifecycle` |

## 4.9 validation/boundary_validator.py

| Property | Value |
|---|---|
| **Purpose** | Validasi akses melalui Contracts + Registry |
| **Responsibility** | Memastikan setiap request masuk melalui Contracts + Registry (ADR-006) |
| **Depends On** | models/domain, exceptions/boundary_errors |
| **Must Not Depend On** | services/, interfaces/ |
| **Exports** | `BoundaryValidator` |

## 4.10 exceptions/boundary_errors.py

| Property | Value |
|---|---|
| **Purpose** | Domain exceptions untuk boundary violation |
| **Responsibility** | InvalidBoundaryAccess, UnauthorizedEntryPoint, DirectUnitAccess |
| **Depends On** | — |
| **Must Not Depend On** | services/, interfaces/, lifecycle/, validation/, models/ |
| **Exports** | `InvalidBoundaryAccess`, `UnauthorizedEntryPoint`, `DirectUnitAccess` |

---

# SECTION 5 — IMPLEMENTATION RULES

## 5.1 MUST Rules

| # | Rule | Source | Implemented In |
|---|---|---|---|
| M1 | Satu bounded capability domain per Citizen Host | GOVERNANCE | `models/domain.py` |
| M2 | Seluruh interaksi eksternal melalui Contracts + Registry | ADR-006 | `validation/boundary_validator.py` |
| M3 | Mengekspos health untuk query eksternal | GOVERNANCE | `services/health_service.py` |
| M4 | Mendukung sertifikasi | GOVERNANCE | `services/certification_service.py` |
| M5 | Delegasi Capability declaration ke Capability Manager | R5-001 | `interfaces/host_interface.py` |
| M6 | Tidak mengeksekusi operasi | GOVERNANCE | Semua file |
| M7 | Tidak menyetujui operasi | R5-001 | Semua file |
| M8 | Tidak merekam audit events | R5-001 | Semua file |
| M9 | Output hanya delegation — tidak ada side effect eksekusi | R5-001 | `services/host_service.py` |
| M10 | Dependency hanya ke shared/contracts/registry | I1-001 | Semua imports |

## 5.2 MUST NOT Rules

| # | Rule | Source | Verified |
|---|---|---|---|
| MN1 | Tidak mengimplementasikan external access | ADR-006 | ✅ No Provider/Connector code |
| MN2 | Tidak mengelola Provider/Connector lifecycle | GOVERNANCE | ✅ |
| MN3 | Tidak memverifikasi implementasi Provider | ADR-006 | ✅ |
| MN4 | Tidak menyediakan SDK/API/protocol | Architecture | ✅ |
| MN5 | Tidak import dari unit lain (lateral) | I1-001 | ✅ |
| MN6 | Tidak import dari internal/ | I1-001 | ✅ |
| MN7 | Tidak mengambil tanggung jawab unit lain | R5-001 | ✅ |

## 5.3 Invariant Rules

| # | Invariant | Source |
|---|---|---|
| I1 | BoundedCapabilityDomain selalu tunggal — Runtime hanya punya satu domain | R4-001 I1 |
| I2 | HealthStatus selalu up-to-date — query kapan saja return status terkini | R4-002 |
| I3 | CertificationStatus selalu deterministik untuk input yang sama | R4-001 I15 |
| I4 | BoundaryValidator tidak boleh di-bypass — semua request melalui validasi | ADR-006 |
| I5 | HostLifecycle state transisi hanya melalui path yang diizinkan | R5-001 C2 |

## 5.4 Boundary Rules

| # | Rule | Source |
|---|---|---|
| B1 | External boundary = Contracts + Registry — no other mechanism | ADR-006 |
| B2 | Internal boundary = Capability Manager — delegasi saja | R4-001 |
| B3 | No lateral communication with other units | R5-001 B6 |
| B4 | Health + Certification adalah read-only — tidak mengubah capability state | R5-001 |

---

# SECTION 6 — TEST STRATEGY

## 6.1 Test Structure

```
tests/runtime/citizen_host/
├── __init__.py
├── test_models.py           # Model integrity tests
├── test_health.py            # Health service tests
├── test_certification.py     # Certification service tests
├── test_boundary.py          # Boundary validation tests
└── test_lifecycle.py         # Lifecycle state transition tests
```

## 6.2 Test Coverage Matrix

| Test File | Test Target | Coverage |
|---|---|---|
| `test_models.py` | BoundedCapabilityDomain, HealthStatus, CertificationStatus, CertificationRequest | Model creation, field validation, immutability |
| `test_health.py` | HealthService | Health computation, state-based availability |
| `test_certification.py` | CertificationService | Certification request processing, determinism |
| `test_boundary.py` | BoundaryValidator | Valid/invalid access detection, error types |
| `test_lifecycle.py` | HostLifecycle | State transitions, invalid transition rejection |

## 6.3 Test Principles

| # | Principle |
|---|---|
| T1 | Tests hanya untuk source code yang sudah ada |
| T2 | Tidak mock unit lain — stub internal saja |
| T3 | Lifecycle tests: validasi transition state hanya melalui path diizinkan |
| T4 | Boundary tests: validasi hanya Contracts + Registry, tolak yang lain |
| T5 | Model tests: validasi field integrity, immutability |

---

# SECTION 7 — TRACEABILITY

## 7.1 Specification → Implementation

| Specification | ADR | Architecture → Design → Engineering → Blueprint | Citizen Host File |
|---|---|---|---|
| CITIZEN_SPEC | ADR-000, ADR-006 | Citizen Host (all layers) | `models/domain.py` |
| CITIZEN_SPEC | ADR-006 | External Boundary | `validation/boundary_validator.py` |
| GOVERNANCE | ADR-006 | Health + Certification | `services/health_service.py`, `services/certification_service.py` |
| CITIZEN_SPEC | ADR-000 | One cohesive Runtime | `lifecycle/host_lifecycle.py` |
| GOVERNANCE | — | Entry point | `interfaces/host_interface.py` |

## 7.2 Full Traceability Chain

```
CITIZEN_SPECIFICATION
  ↓
G0-001 §1: Citizen Host — "Host and govern Citizens; own Citizen lifecycle"
  ↓
ADR-000: One cohesive Runtime per domain
ADR-006: External access = Contracts + Registry only
ADR-001: Accountable Decision Framework (approval structure)
  ↓
R4-001 §3.1: Citizen Host — Purpose, Responsibility, Must, Must Not
  ↓
R4-002 §2.2: Citizen Host — Structural Contract, Input/Output
  ↓
R5-001 §2.1: Citizen Host Unit — Consumes/Produces/Owns/Must/Must Not
  ↓
I0-001 §2.1: Citizen Host Implementation Unit — Mandatory/Optional/Forbidden
  ↓
I1-001 §2.1: citizen_host/ module — Ownership, Dependency, Must Not Depend On
  ↓
I2-001: CITIZEN HOST IMPLEMENTATION
  ├── models/domain.py            ← R1: bounded capability domain
  ├── models/health.py            ← R9: expose health
  ├── models/certification.py     ← R8: support certification
  ├── interfaces/host_interface.py ← Entry point surface
  ├── services/host_service.py    ← Orchestrator
  ├── services/health_service.py   ← R9 implementation
  ├── services/certification_service.py ← R8 implementation
  ├── lifecycle/host_lifecycle.py  ← Host lifecycle
  ├── validation/boundary_validator.py ← ADR-006 boundary enforcement
  └── exceptions/boundary_errors.py    ← Domain exceptions
```

---

# VALIDATION

## Audit 1 — Responsibility Completeness

| Responsibility | Implemented In | Status |
|---|---|---|
| R1 — Own bounded capability domain | `models/domain.py` + `services/host_service.py` | ✅ |
| R8 — Support certification | `models/certification.py` + `services/certification_service.py` | ✅ |
| R9 — Expose health | `models/health.py` + `services/health_service.py` | ✅ |
| — Boundary enforcement | `validation/boundary_validator.py` | ✅ |
| — Entry point delegation | `interfaces/host_interface.py` + `services/host_service.py` | ✅ |
| — Host lifecycle management | `lifecycle/host_lifecycle.py` | ✅ |
| — Domain error handling | `exceptions/boundary_errors.py` | ✅ |

**Hasil:** ✅ LULUS — seluruh responsibility Citizen Host tercakup. Tidak ada responsibility unit lain (execution, approval, audit).

---

## Audit 2 — Specification Compliance

| Specification | Requirement | Citizen Host Compliance |
|---|---|---|
| CITIZEN_SPEC | Citizen memiliki bounded governance responsibility | ✅ `BoundedCapabilityDomain` |
| CITIZEN_SPEC | Citizen tidak memiliki architectural privilege | ✅ Tidak ada override architecture |
| CITIZEN_SPEC | Citizen tidak mengambil strategic decisions | ✅ Tidak ada decision-making code |
| GOVERNANCE | Own one bounded capability domain | ✅ Singleton pattern enforced |
| GOVERNANCE | Expose health | ✅ `HealthService` |
| GOVERNANCE | Support certification | ✅ `CertificationService` |

**Hasil:** ✅ LULUS — specification compliant.

---

## Audit 3 — ADR Compliance

| ADR | Requirement | Citizen Host Compliance |
|---|---|---|
| ADR-000 | One cohesive Runtime per domain | ✅ Satu `BoundedCapabilityDomain` |
| ADR-001 | Accountable Decision Framework | ✅ Tidak menghasilkan Approval decision (bukan wewenangnya) |
| ADR-002 | Capability resolution policy | ✅ Delegasi ke Capability Manager, bukan resolve sendiri |
| ADR-003 | Idempotency via Contract declaration | ✅ Tidak mengeksekusi — idempotency bukan tanggung jawabnya |
| ADR-004 | Linear failure propagation → Audit | ✅ Exception hierarchy mengarah ke Audit |
| ADR-005 | Strict Linear Ordering | ✅ Tidak mengeksekusi — ordering bukan tanggung jawabnya |
| ADR-006 | External = Contracts + Registry | ✅ `BoundaryValidator` enforces this |
| ADR-007 | Verification as state transition | ✅ Tidak memverifikasi — verification di Audit |

**Hasil:** ✅ LULUS — 8/8 ADR compliant.

---

## Audit 4 — Architecture Compliance

| R4-001 Requirement | Citizen Host Compliance |
|---|---|
| Purpose: Entry point, boundary surface | ✅ `HostInterface` sebagai surface |
| Must: Own one bounded capability domain | ✅ `BoundedCapabilityDomain` |
| Must: Interact through Contracts + Registry | ✅ `BoundaryValidator` |
| Must: Expose health | ✅ `HealthService` |
| Must: Support certification | ✅ `CertificationService` |
| Must Not: Implement external access | ✅ Tidak ada Provider/Connector |
| Must Not: Manage Provider lifecycle | ✅ |
| Must Not: Provide SDK/API/protocol | ✅ |
| Authority: GOVERNANCE + CITIZEN_SPEC | ✅ Referensi jelas |

**Hasil:** ✅ LULUS — architecture compliant.

---

## Audit 5 — Boundary Integrity

| Boundary | Enforcement | Status |
|---|---|---|
| External boundary = Contracts + Registry | `BoundaryValidator.validate_access()` | ✅ |
| Internal boundary = Capability Manager delegation only | `HostService.delegate_request()` | ✅ |
| No lateral communication | Semua imports terbatas ke models/ + services/ | ✅ |
| No unit-to-unit direct access | Tidak import dari unit module lain | ✅ |

**Hasil:** ✅ LULUS — boundary integrity maintained.

---

## Audit 6 — Dependency Integrity

| Dependency Rule | Verified |
|---|---|
| Import dari shared/contracts/registry saja | ✅ — shared infrastructure references |
| Tidak import dari unit lain | ✅ — verified |
| Tidak import dari internal/ | ✅ — verified |
| Tidak circular dependency internal | ✅ — dag: models ← lifecycle ← services ← interfaces |
| Tidak bergantung pada unit di bawah | ✅ — hanya delegasi, bukan dependecy |

**Hasil:** ✅ LULUS — dependency integrity maintained.

---

## Audit 7 — Test Readiness

| Kriteria | Status |
|---|---|
| Test structure mirror source structure | ✅ |
| 5 test file skeleton | ✅ |
| Coverage per responsibility (models, health, certification, boundary, lifecycle) | ✅ |
| No mock of unimplemented units | ✅ |
| Test principles documented (Section 6) | ✅ |

**Hasil:** ✅ LULUS — test skeleton ready.

---

## Audit 8 — Final Certification

| Kriteria | Status |
|---|---|
| 8 source files + 7 package inits = 15 files | ✅ |
| 5 test files + 1 package init = 6 files | ✅ |
| Total files created: 21 | ✅ |
| 3 shared infrastructure stubs (shared/, contracts/, registry/) | ✅ |
| Semua responsibility terimplementasi (R1, R8, R9 + boundary + lifecycle) | ✅ |
| 8 audits LULUS | ✅ |
| Tidak ada kode unit lain | ✅ |
| Tidak ada keputusan arsitektur baru | ✅ |

**Hasil:** ✅ LULUS — **Citizen Host Certified.**

---

# STOP CONDITION

**STOP Status:** NOT ACTIVE

**Verifikasi:**
- ✅ Tidak membutuhkan ADR baru — 8 ADR Accepted
- ✅ Tidak membutuhkan perubahan Architecture — R4-001 final
- ✅ Tidak membutuhkan perubahan Design — R4-002 final
- ✅ Tidak membutuhkan perubahan Engineering — R5-001 final
- ✅ Tidak membutuhkan perubahan Blueprint — I0-001 final
- ✅ Tidak membutuhkan perubahan Skeleton — I1-001 final
- ✅ Tidak membutuhkan perubahan Specification — Specification beku
- ✅ Tidak membutuhkan perubahan Foundation — Foundation complied

---

**END OF I2-001 — Citizen Host Reference Implementation**
