# I2-002 — Capability Manager Reference Implementation

**Document ID:** I2-002
**Title:** Capability Manager Reference Implementation
**Status:** Completed
**Date:** 2026-08-03
**Author:** Chief Architect (Project SAM Architecture Decision Making)
**Audience:** Implementation Team, Engineering, Architecture
**Source of Authority:** Foundation | CAPABILITY_SPEC | Blueprint (G0-001) | ADR-000..ADR-007 | R4-001 | R4-002 | R5-001 | I0-001 | I1-001 | I2-001
**Derived From:** I0-001 Reference Runtime Implementation Blueprint, I1-001 Repository Skeleton
**Implementation Target:** `src/sam/runtime/capability_manager/`

---

# Executive Summary

I2-002 adalah implementasi **Unit 2** dari Reference Runtime: **Capability Manager** — unit pengelola publikasi dan lifecycle Capability. Unit ini mewujudkan Capability sebagai entitas yang terdaftar, tersertifikasi, dan discoverable di Registry.

```
R4-001 Architecture     →  "Apa komponen?"
R4-002 Design           →  "Bagaimana strukturnya?"
R5-001 Engineering      →  "Bagaimana unitnya?"
I0-001 Blueprint        →  "Apa kontrak codingnya?"
I1-001 Skeleton         →  "Di mana kodenya?"
I2-001 Citizen Host     →  "Unit 1 ✅"
I2-002 Capability Mgr   →  "Unit 2 ◀ ANDA DI SINI"
   ↓
I2-003 Discovery        →  "Unit 3"
```

**Apa yang diimplementasikan:**
- Seluruh responsibility Capability Manager dari R5 / I0 / I1
- 14 file source (+ 8 package inits)
- 7 file unit test (+ 1 package init)
- Capability lifecycle state machine (6 states, 5 transitions)
- Descriptor integrity validation
- Declaration + lifecycle validation
- Public interface untuk Discovery Resolver
- Tidak ada dependency lateral — hanya shared/contracts/registry

---

# SECTION 1 — IMPLEMENTATION RESPONSIBILITY

## 1.1 Responsibility Turunan

| # | Responsibility | Source | Implementation |
|---|---|---|---|
| R2 | Publish capabilities | R5-001 §2.2, I0-001 §2.2 | `publication_service.py`, `declaration_validator.py` |
| — | Manage lifecycle | R5-001 §2.2 | `state/capability_state.py`, `lifecycle_service.py` |
| — | Descriptor integrity | R5-001 §2.2 | `models/capability_descriptor.py`, `validation/descriptor_validator.py` |
| — | Capability identity | CAPABILITY_SPEC | `models/capability_descriptor.py` |
| — | Version management | CAPABILITY_SPEC | `models/capability_descriptor.py` |
| — | Certification support | GOVERNANCE | `validation/certification_validator.py` |
| — | Health reporting | R4-001 | `services/health_service.py` |

## 1.2 Responsibility Yang TIDAK Diimplementasikan

| Bukan Tanggung Jawab | Kenapa |
|---|---|
| Capability execution | Milik Execution Scheduler (Unit 6) |
| Discovery/resolution | Milik Discovery Resolver (Unit 3) |
| Contract definition | Milik Contract Enforcer (Unit 4) |
| Approval decision | Milik Approval Coordinator (Unit 5) |
| Audit recording | Milik Audit Recorder (Unit 7) |
| Registry storage | Milik shared registry infrastructure |

---

# SECTION 2 — PUBLIC CONTRACT

## 2.1 CapabilityManagerInterface

Capability Manager mengekspos public interface yang akan digunakan oleh Citizen Host (delegasi dari atas) dan Discovery Resolver (query dari bawah).

```
CapabilityManagerInterface:
  ┌────────────────────────────────────────────┐
  │  publish(declaration) → PublishedCapability │
  │      → memvalidasi descriptor              │
  │      → menyimpan capability                │
  │      → mengembalikan PublishedCapability    │
  │                                             │
  │  transition(identity, target_state)         │
  │      → CapabilityLifecycleResult            │
  │                                             │
  │  get_capability(identity)                   │
  │      → Optional[CapabilityDescriptor]       │
  │                                             │
  │  list_capabilities(filter)                  │
  │      → List[CapabilityDescriptor]           │
  │                                             │
  │  is_discoverable(identity)                  │
  │      → bool                                 │
  │                                             │
  │  get_health()                               │
  │      → HealthStatus                          │
  └────────────────────────────────────────────┘
```

## 2.2 Contract Semantics

| Operasi | Input | Output | Efek Samping |
|---|---|---|---|
| `publish` | CapabilityDeclaration | PublishedCapability | Capability tersimpan, lifecycle = Declared |
| `transition` | identity + target state | CapabilityLifecycleResult | Lifecycle berubah (jika valid) |
| `get_capability` | identity | Optional[CapabilityDescriptor] | None (read-only) |
| `list_capabilities` | filter critera | List[CapabilityDescriptor] | None (read-only) |
| `is_discoverable` | identity | bool | None (read-only) |
| `get_health` | — | HealthStatus | None (read-only) |

---

# SECTION 3 — INTERNAL STRUCTURE

## 3.1 Package Structure

```
capability_manager/
├── __init__.py                       # Package exports
├── models/                           # Data models
│   ├── __init__.py
│   ├── capability_descriptor.py      # CapabilityDescriptor (immutable)
│   ├── capability_lifecycle.py       # CapabilityLifecycle enum (6 states)
│   └── declaration.py                 # CapabilityDeclaration request
├── interfaces/                       # Public-facing interface
│   ├── __init__.py
│   └── manager_interface.py          # CapabilityManagerInterface
├── services/                         # Business logic
│   ├── __init__.py
│   ├── manager_service.py            # Main service orchestrator
│   ├── lifecycle_service.py          # Lifecycle transition engine
│   ├── publication_service.py        # Publication + registration logic
│   └── health_service.py             # Manager health reporting
├── lifecycle/                        # Manager's own lifecycle
│   ├── __init__.py
│   └── manager_lifecycle.py          # ManagerLifecycle state machine
├── state/                            # Capability state machine
│   ├── __init__.py
│   └── capability_state.py           # CapabilityState — lifecycle transitions
├── validation/                       # Invariant enforcement
│   ├── __init__.py
│   ├── descriptor_validator.py       # Descriptor integrity validation
│   ├── lifecycle_validator.py        # Transition legality validation
│   ├── declaration_validator.py      # Declaration completeness validation
│   └── certification_validator.py    # Certification criteria validation
└── exceptions/                       # Domain exceptions
    ├── __init__.py
    └── capability_errors.py          # CapabilityError hierarchy
```

## 3.2 Layer Dependencies

```
interfaces/manager_interface.py
  → services/manager_service.py
    → services/publication_service.py
      → validation/declaration_validator.py
      → models/declaration.py
      → models/capability_descriptor.py
    → services/lifecycle_service.py
      → state/capability_state.py
      → validation/lifecycle_validator.py
      → models/capability_lifecycle.py
    → validation/descriptor_validator.py
      → models/capability_descriptor.py
    → validation/certification_validator.py
      → models/capability_descriptor.py
    → lifecycle/manager_lifecycle.py
    → exceptions/capability_errors.py
```

Semua layer bergantung ke `models/` dan `state/`. Tidak ada yang bergantung ke atas.

---

# SECTION 4 — IMPLEMENTATION FILES

## 4.1 models/capability_descriptor.py

| Property | Value |
|---|---|
| **Purpose** | CapabilityDescriptor — immutable representation of a Capability |
| **Fields** | identity, name, description, owner_citizen, version, inputs, outputs, constraints, compatibility, lifecycle_state, certification_status, metadata |
| **Depends On** | models/capability_lifecycle (for lifecycle_state field) |
| **Must Not Depend On** | services/, interfaces/, validation/, exceptions/ |
| **Exports** | `CapabilityDescriptor` |

## 4.2 models/capability_lifecycle.py

| Property | Value |
|---|---|
| **Purpose** | CapabilityLifecycle — 6-state enum: DECLARED → REGISTERED → CERTIFIED → AVAILABLE → DEPRECATED → RETIRED |
| **Depends On** | — (pure enum) |
| **Must Not Depend On** | services/, interfaces/, validation/, exceptions/, models/* |
| **Exports** | `CapabilityLifecycle` |

## 4.3 models/declaration.py

| Property | Value |
|---|---|
| **Purpose** | CapabilityDeclaration — request to publish a Capability |
| **Fields** | identity, name, description, owner_citizen, version, inputs, outputs, constraints, compatibility, metadata |
| **Depends On** | — (pure model) |
| **Must Not Depend On** | services/, interfaces/, validation/, exceptions/, lifecycle/ |
| **Exports** | `CapabilityDeclaration` |

## 4.4 interfaces/manager_interface.py

| Property | Value |
|---|---|
| **Purpose** | Public contract — consumed by Citizen Host and Discovery Resolver |
| **Depends On** | models/capability_descriptor, models/capability_lifecycle, models/declaration |
| **Must Not Depend On** | services/, lifecycle/, state/, validation/, exceptions/, citizen_host, discovery_resolver, dll. |
| **Exports** | `CapabilityManagerInterface`, `PublishResult`, `TransitionResult` |

## 4.5 services/manager_service.py

| Property | Value |
|---|---|
| **Purpose** | Concrete implementation of CapabilityManagerInterface |
| **Depends On** | models/*, services/*, state/*, validation/*, lifecycle/*, exceptions/* |
| **Must Not Depend On** | interfaces/ |
| **Exports** | `CapabilityManagerService` |

## 4.6 services/publication_service.py

| Property | Value |
|---|---|
| **Purpose** | Validates declaration → creates immutable descriptor → registers |
| **Depends On** | models/declaration, models/capability_descriptor, validation/declaration_validator, validation/descriptor_validator, exceptions/* |
| **Must Not Depend On** | interfaces/, lifecycle/, state/ |
| **Exports** | `PublicationService` |

## 4.7 services/lifecycle_service.py

| Property | Value |
|---|---|
| **Purpose** | Processes lifecycle transitions with validation |
| **Depends On** | models/capability_lifecycle, state/capability_state, validation/lifecycle_validator, exceptions/* |
| **Must Not Depend On** | interfaces/ |
| **Exports** | `LifecycleService` |

## 4.8 services/health_service.py

| Property | Value |
|---|---|
| **Purpose** | Reports Manager operational health |
| **Depends On** | lifecycle/manager_lifecycle |
| **Must Not Depend On** | interfaces/ |
| **Exports** | `HealthService` |

## 4.9 lifecycle/manager_lifecycle.py

| Property | Value |
|---|---|
| **Purpose** | Manager's own lifecycle: UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED |
| **Depends On** | — |
| **Must Not Depend On** | services/, interfaces/, validation/, exceptions/ |
| **Exports** | `ManagerLifecycleState`, `ManagerLifecycle` |

## 4.10 state/capability_state.py

| Property | Value |
|---|---|
| **Purpose** | Capability state machine — defines allowed lifecycle transitions |
| **Depends On** | models/capability_lifecycle |
| **Must Not Depend On** | services/, interfaces/, lifecycle/, validation/, exceptions/ |
| **Exports** | `CapabilityState` |

## 4.11–4.14 validation/

| File | Validates | Exports |
|---|---|---|
| `descriptor_validator.py` | Descriptor fields completeness, immutability | `DescriptorValidator` |
| `lifecycle_validator.py` | Transition legality per path | `LifecycleValidator` |
| `declaration_validator.py` | Declaration field completeness | `DeclarationValidator` |
| `certification_validator.py` | Certification criteria (descriptor, contract, governance) | `CertificationValidator` |

## 4.15 exceptions/capability_errors.py

| File | Exports |
|---|---|
| `capability_errors.py` | `CapabilityError`, `InvalidDeclaration`, `InvalidTransition`, `InvalidDescriptor`, `CapabilityNotFound`, `CertificationFailed`, `DescriptorImmutable` |

---

# SECTION 5 — IMPLEMENTATION RULES

## 5.1 MUST Rules

| # | Rule | Source |
|---|---|---|
| M1 | Capability: eksplisit, discoverable, immutable setelah published | CAPABILITY_SPEC, R5-001 §2.2 |
| M2 | Descriptor lengkap: identity, version, contract reference, lifecycle state | R5-001 §2.2 |
| M3 | Lifecycle: Declared → Registered → Certified → Available → Deprecated → Retired | CAPABILITY_SPEC |
| M4 | Setelah Retired: tidak discoverable untuk request baru, tetap traceable | R5-001 §2.2 |
| M5 | Identity tidak mengandung nama implementasi | CAPABILITY_SPEC |
| M6 | Version menggunakan Major.Minor.Patch | CAPABILITY_SPEC |
| M7 | Tidak mengeksekusi Capability | R5-001 §2.2 Must Not |
| M8 | Tidak discovery/resolution | R5-001 §2.2 Must Not |
| M9 | Tidak definisi Contract | R5-001 §2.2 Must Not |
| M10 | Tidak Approval | R5-001 §2.2 Must Not |
| M11 | Dependency hanya ke shared/contracts/registry | I1-001 §2.2 |

## 5.2 MUST NOT Rules

| # | Rule | Source |
|---|---|---|
| MN1 | Tidak mengambil tanggung jawab Citizen Host | R5-001 §2.2 Must Not |
| MN2 | Tidak mengambil tanggung jawab Discovery Resolver | R5-001 §2.2 Must Not |
| MN3 | Tidak import dari unit lain (lateral) | I1-001 §6.1 |
| MN4 | Tidak import dari internal/ | I1-001 §6.1 |
| MN5 | Tidak circular dependency | I1-001 §6.1 |
| MN6 | Tidak mengekspos implementasi internal | R4-001 |

## 5.3 Invariant Rules

| # | Invariant | Source |
|---|---|---|
| I1 | Setiap Capability memiliki identity unik | CAPABILITY_SPEC |
| I2 | Descriptor tidak dapat diubah setelah published | CAPABILITY_SPEC |
| I3 | Lifecycle hanya bergerak ke depan (kecuali Deprecated → Available boleh) | CAPABILITY_SPEC |
| I4 | Capability identity tidak mengandung nama implementasi | CAPABILITY_SPEC |
| I5 | Certification deterministik untuk input yang sama | R4-001 I15 |

---

# SECTION 6 — TEST STRATEGY

## 6.1 Test Structure

```
tests/runtime/capability_manager/
├── __init__.py
├── test_descriptor.py       # Descriptor creation, immutability, field validation
├── test_lifecycle_state.py  # State transitions, forbidden paths
├── test_declaration.py      # Declaration validation
├── test_publication.py      # Publication flow (declaration → descriptor)
├── test_transition.py       # Lifecycle transition flow
├── test_certification.py    # Certification validation
└── test_health.py           # Manager health reporting
```

## 6.2 Test Principles

| # | Principle |
|---|---|
| T1 | Tests hanya untuk source code yang sudah ada |
| T2 | Tidak mock unit lain — stub internal saja |
| T3 | Lifecycle tests: validasi setiap transition, tolak path tidak diizinkan |
| T4 | Descriptor tests: validasi field, immutability (frozen), identity unik |
| T5 | Certification tests: deterministik, input sama → output sama |

---

# SECTION 7 — TRACEABILITY

## 7.1 Specification → Implementation

| Specification | Engineering | Blueprint | Capability Manager File |
|---|---|---|---|
| CAPABILITY_SPEC | R5-001 §2.2 | I0-001 §2.2 | `models/capability_descriptor.py` |
| CAPABILITY_SPEC (identity) | R5-001 §2.2 R2 | I0-001 §2.2 | `models/declaration.py`, `validation/declaration_validator.py` |
| CAPABILITY_SPEC (lifecycle) | R5-001 §2.2 | I0-001 §2.2 | `models/capability_lifecycle.py`, `state/capability_state.py` |
| CAPABILITY_SPEC (version) | R5-001 §2.2 | I0-001 §2.2 | `models/capability_descriptor.py` |
| CAPABILITY_SPEC (certification) | R5-001 §2.1 R8 | I0-001 §2.1 | `validation/certification_validator.py` |
| GOVERNANCE | R5-001 §2.2 | I0-001 §2.2 | `services/health_service.py`, `lifecycle/manager_lifecycle.py` |

## 7.2 Full Traceability Chain

```
CAPABILITY_SPECIFICATION
  ↓
G0-001 §2: Capability Manager — "Publish and govern Capabilities"
  ↓
ADR-000: One cohesive Runtime per domain
ADR-002: Capability resolution = exact-preferred, compatible fallback
ADR-003: Idempotency = Operation-Defined Semantics
  ↓
R4-001 §3.2: Capability Manager — Purpose, Responsibility, Must, Must Not
  ↓
R4-002 §2.3: Capability Manager — Structural Contract
  ↓
R5-001 §2.2: Capability Manager Unit — Consumes/Produces/Owns/Must/Must Not
  ↓
I0-001 §2.2: Capability Manager Implementation Unit — Mandatory/Optional/Forbidden
  ↓
I1-001 §2.2: capability_manager/ module — Ownership, Dependency
  ↓
I2-002: CAPABILITY MANAGER IMPLEMENTATION
  ├── models/capability_descriptor.py   ← R2: immutable descriptor
  ├── models/capability_lifecycle.py    ← R2: 6-state lifecycle
  ├── models/declaration.py             ← R2: publication request
  ├── interfaces/manager_interface.py   ← Public contract
  ├── services/manager_service.py       ← Orchestrator
  ├── services/publication_service.py   ← R2 implementation
  ├── services/lifecycle_service.py     ← Lifecycle engine
  ├── services/health_service.py        ← Health reporting
  ├── lifecycle/manager_lifecycle.py    ← Manager state machine
  ├── state/capability_state.py         ← Capability state machine
  ├── validation/descriptor_validator.py ← Descriptor integrity
  ├── validation/lifecycle_validator.py  ← Transition legality
  ├── validation/declaration_validator.py ← Declaration completeness
  ├── validation/certification_validator.py ← Certification criteria
  └── exceptions/capability_errors.py    ← Domain exceptions
```

---

# VALIDATION

## Audit 1 — Responsibility Completeness

| Responsibility | Implemented In | Status |
|---|---|---|
| R2 — Publish capabilities | `publication_service.py` + `declaration_validator.py` | ✅ |
| — Manage lifecycle | `lifecycle_service.py` + `capability_state.py` | ✅ |
| — Descriptor integrity | `descriptor_validator.py` + `capability_descriptor.py` (frozen) | ✅ |
| — Capability identity | `declaration.py` + `declaration_validator.py` | ✅ |
| — Version management | `capability_descriptor.py` | ✅ |
| — Certification support | `certification_validator.py` | ✅ |
| — Health reporting | `health_service.py` + `manager_lifecycle.py` | ✅ |

**Hasil:** ✅ LULUS — seluruh responsibility Capability Manager tercakup.

---

## Audit 2 — Specification Compliance

| Specification | Requirement | Compliance |
|---|---|---|
| CAPABILITY_SPEC | Capability immutable, versioned, uniquely identifiable | ✅ `CapabilityDescriptor` (frozen) |
| CAPABILITY_SPEC | Identity tidak mengandung nama implementasi | ✅ `DeclarationValidator` |
| CAPABILITY_SPEC | Lifecycle: Declared → Registered → Certified → Available → Deprecated → Retired | ✅ `CapabilityLifecycle` + `CapabilityState` |
| CAPABILITY_SPEC | Descriptor lengkap | ✅ `DescriptorValidator` |
| CAPABILITY_SPEC | Version Major.Minor.Patch | ✅ `CapabilityDescriptor.version` |
| CAPABILITY_SPEC | Discoverable melalui Registry | ✅ `is_discoverable()` |

**Hasil:** ✅ LULUS — specification compliant.

---

## Audit 3 — ADR Compliance

| ADR | Requirement | Compliance |
|---|---|---|
| ADR-000 | One cohesive Runtime per domain | ✅ |
| ADR-001 | Accountable Decision Framework | ✅ Tidak memutuskan approval |
| ADR-002 | Capability resolution: exact → compatible → tie-break | ✅ Tidak melakukan resolution (Discovery punya) |
| ADR-003 | Idempotency via Contract | ✅ Tidak mengeksekusi |
| ADR-004 | Failure linear → Audit | ✅ Exception hierarchy mengarah forward |
| ADR-005 | Strict Linear Ordering | ✅ Tidak mengeksekusi |
| ADR-006 | External via Contracts + Registry | ✅ Publikasi ke Registry |

**Hasil:** ✅ 7/7 ADR compliant (ADR-007 verification di Audit Unit, bukan di sini).

---

## Audit 4 — Architecture Compliance

| R4-001 Requirement | Compliance |
|---|---|
| Purpose: Publish, manage lifecycle | ✅ |
| Must: Publish discoverable capability | ✅ |
| Must: Lifecycle state management | ✅ |
| Must Not: Execute capabilities | ✅ |
| Must Not: Resolve capabilities | ✅ |
| Must Not: Define contracts | ✅ |
| Must Not: Decide approvals | ✅ |

**Hasil:** ✅ LULUS — architecture compliant.

---

## Audit 5 — Boundary Integrity

| Boundary | Enforcement | Status |
|---|---|---|
| Vertical up: menerima dari Citizen Host | `CapabilityManagerInterface.publish()` | ✅ |
| Vertical down: menyediakan ke Discovery Resolver | `CapabilityManagerInterface.get_capability()` | ✅ |
| No lateral communication | Semua imports terbatas internal | ✅ |
| No unit-to-unit direct access | Tidak import dari unit lain | ✅ |

**Hasil:** ✅ LULUS — boundary integrity maintained.

---

## Audit 6 — Dependency Integrity

| Dependency Rule | Verified |
|---|---|
| Import dari shared/contracts/registry saja | ✅ |
| Tidak import dari unit lain | ✅ |
| Tidak import dari internal/ | ✅ |
| Tidak circular dependency internal | ✅ dag direction checked |
| Tidak bergantung pada unit di bawah | ✅ hanya konsumsi dari atas |

**Hasil:** ✅ LULUS — dependency integrity maintained.

---

## Audit 7 — Test Readiness

| Kriteria | Status |
|---|---|
| Test structure mirror source structure | ✅ |
| 7 test file skeleton | ✅ |
| Coverage: descriptor, lifecycle, declaration, publication, transition, certification, health | ✅ |
| No mock of unimplemented units | ✅ |

**Hasil:** ✅ LULUS — test skeleton ready.

---

## Audit 8 — Final Certification

| Kriteria | Status |
|---|---|
| 14 source files + 8 package inits = 22 files | ✅ |
| 7 test files + 1 package init = 8 files | ✅ |
| Total: 30 files | ✅ |
| Semua responsibility terimplementasi | ✅ |
| 8 audits LULUS | ✅ |
| Tidak ada kode unit lain | ✅ |
| Tidak ada keputusan arsitektur baru | ✅ |
| ADR compliant (7/7, ADR-007 N/A) | ✅ |

**Hasil:** ✅ LULUS — **Capability Manager Certified.**

---

# STOP CONDITION

**STOP Status:** NOT ACTIVE

**Verifikasi:**
- ✅ Tidak membutuhkan ADR baru
- ✅ Tidak membutuhkan perubahan Architecture
- ✅ Tidak membutuhkan perubahan Design
- ✅ Tidak membutuhkan perubahan Engineering
- ✅ Tidak membutuhkan perubahan Blueprint
- ✅ Tidak membutuhkan perubahan Specification

---

**END OF I2-002 — Capability Manager Reference Implementation**
