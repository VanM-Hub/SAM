# I2-004 — Contract Enforcer Reference Implementation

**Document ID:** I2-004
**Title:** Contract Enforcer Reference Implementation
**Status:** Completed
**Date:** 2026-08-03
**Implementation Unit:** 4 of 7
**Source of Authority:** Foundation | CONTRACT_SPEC | ADR-000…ADR-007 | R4-001 | R4-002 | R5-001 | I0-001 | I1-001

---

# Executive Summary

I2-004 mengimplementasikan **Contract Enforcer Unit** — Unit 4 dari 7 Reference Runtime Implementation Units. Unit ini menyediakan Contract immutable dengan struktur lengkap, deklarasi idempotency per operasi (ADR-003), verifikasi compatibility, dan version negotiation. Contract Enforcer adalah gate komunikasi antar Citizen — ia menjamin bahwa kedua pihak sepakat pada shape interaksi sebelum interaksi terjadi.

Contract Enforcer depend pada **dua infrastructure module saja**: `shared` (models/types) dan `contracts` (contract definitions). Ia tidak mengetahui internal unit lain — tidak mengakses Discovery Resolver, tidak menyetujui (Approval Coordinator), tidak mengeksekusi, tidak merekam audit.

---

# CONTENTS

1. Source Mapping & Justification
2. Architecture Compliance
3. Module Structure
4. Implementation Detail
5. Specification Compliance
6. Dependency Integrity
7. Boundary Enforcement
8. Audit Certifications

---

# SECTION 1 — SOURCE MAPPING & JUSTIFICATION

## 1.1 Traceability Matrix

| Source | Section | Requirement | Implementation Location |
|---|---|---|---|
| CONTRACT_SPEC | Contract Structure | Contract = Input + Output + Metadata + Constraints + Compatibility + Error | `contract_enforcer/models/contract_model.py` |
| CONTRACT_SPEC | Contract Identity | contract_id + version + capability_reference | `contracts/` shared types + Contract model |
| CONTRACT_SPEC | Compatibility Rules | Backward, Forward, Breaking, Compatible, Deprecated | `contract_enforcer/validation/compatibility_validator.py` |
| CONTRACT_SPEC | Version Negotiation | Agree on single version, prefer compatible, prefer non-deprecated | `contract_enforcer/services/negotiator_service.py` |
| CONTRACT_SPEC | Failure Behaviour | Unknown Contract, Unsupported Version, Invalid Contract, Malformed Payload, Missing Field, Incompatible Contract | `contract_enforcer/exceptions/` |
| CONTRACT_SPEC | Interoperability | Agree on Contract Identity + Structure + Compatibility + Negotiation | `contract_enforcer/services/enforcer_service.py` |
| ADR-003 | Contract declares idempotency | IDEMPOTENT / NON-IDEMPOTENT per operasi | `contracts/` idempotency types + Contract model |
| ADR-003 | Safe default | Tanpa deklarasi → assume non-idempotent | `contract_enforcer/validation/idempotency_validator.py` |
| ADR-006 | External boundary = Contracts + Registry | Contract Enforcer adalah bagian border | Boundary enforcement validates entry points |
| R5-001 §2.4 | Engineering Unit Contract Enforcer | R3 (immutable contracts), R11 (idempotency declaration) | Full implementation |
| I0-001 §2.4 | Implementation Unit Contract Enforcer | All MUST/MUST NOT | Full implementation |
| I1-001 §2.4 | Module contract_enforcer | Depends on shared + contracts only | Verified in §6 |

## 1.2 Responsibility Distribution

| # | Responsibility | Implementation |
|---|---|---|
| R3 | Expose immutable contracts | Contract model (frozen dataclass), enforcer service |
| R11 | Declare idempotency | IdempotencyDeclaration in Contract, validated per operation |

## 1.3 Must & Must Not

**Must:**
- Contract immutable — frozen model
- Contract memiliki: Input, Output, Metadata, Constraints, Compatibility, Error
- Compatibility negotiation — pilih versi kompatibel tertinggi
- Preferensi non-deprecated
- Contract mendeklarasikan idempotency per operasi
- Contract declare compatibility relative to predecessor

**Must Not:**
- Tidak mengeksekusi operasi
- Tidak menyetujui operasi  
- Tidak menemukan Capability
- Tidak mengamati idempotency saat runtime (milik Execution)
- Tidak merekam audit

---

# SECTION 2 — ARCHITECTURE COMPLIANCE

## 2.1 Position in Reference Runtime

```
7-Component Model (G0-001):
  [Citizen Host] → [Capability Manager] → [Discovery Resolver]
       → [Contract Enforcer] → [Approval Coordinator]
       → [Execution Scheduler] → [Audit Recorder]

Unit 4: Contract Enforcer
  Consumes: Contract Reference (dari Discovery Resolver)
  Produces: Contract + Idempotency Declaration + Negotiated Version
```

## 2.2 ADR Compliance

| ADR | Decision | How Implemented |
|---|---|---|
| ADR-000 | One cohesive Runtime | Contract Enforcer = satu modul dalam satu Runtime |
| ADR-002 | Capability Resolution (indirect) | Contract Reference berasal dari Discovery Resolver; unit ini TIDAK meresolve |
| ADR-003 | Idempotency: Contract declares | IdempotencyDeclaration di Contract; unit ini MENDEFINISIKAN deklarasi, Execution MENGAMATI |
| ADR-006 | External boundary = Contracts + Registry | Contract adalah salah satu dari dua mekanisme eksternal boundary |

---

# SECTION 3 — MODULE STRUCTURE

## 3.1 Directory Layout

```
src/sam/runtime/contract_enforcer/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── contract_model.py          # Contract (frozen), ContractField
│   ├── compatibility_result.py    # CompatibilityResult, CompatibilityStatus
│   └── negotiation_result.py      # NegotiationResult, NegotiationStatus
├── interfaces/
│   ├── __init__.py
│   └── enforcer_interface.py      # ContractEnforcerInterface (Protocol)
├── services/
│   ├── __init__.py
│   ├── enforcer_service.py        # ContractEnforcer — main orchestrator
│   ├── health_service.py          # HealthService
│   └── negotiator_service.py      # Version negotiator
├── lifecycle/
│   ├── __init__.py
│   └── enforcer_lifecycle.py      # 5-state lifecycle
├── state/
│   ├── __init__.py
│   └── contract_state.py          # Contract state machine
├── validation/
│   ├── __init__.py
│   ├── contract_validator.py      # Full structure validation
│   ├── compatibility_validator.py # Compatibility rule validation
│   ├── negotiation_validator.py   # Negotiation process validation
│   └── idempotency_validator.py   # Idempotency declaration validation
└── exceptions/
    ├── __init__.py
    └── contract_errors.py         # Error hierarchy
```

Shared infrastructure (`contracts/`):
```
src/sam/runtime/contracts/
├── __init__.py                    # ContractIdempotency, ContractIdentity
```

## 3.2 Package Ownership

| Package | Owns |
|---|---|
| `models/` | Contract, CompatibilityResult, NegotiationResult |
| `interfaces/` | ContractEnforcerInterface Protocol |
| `services/` | ContractEnforcer orchestrator, HealthService, NegotiatorService |
| `lifecycle/` | ContractEnforcerLifecycle (5-state) |
| `state/` | ContractState machine |
| `validation/` | ContractValidator, CompatibilityValidator, NegotiationValidator, IdempotencyValidator |
| `exceptions/` | ContractError hierarchy |

---

# SECTION 4 — IMPLEMENTATION DETAIL

## 4.1 Contract Model

`contract_enforcer/models/contract_model.py`:

**Contract** (frozen dataclass):
- `contract_id: str` — global identifier
- `version: str` — semver version
- `capability_reference: str` — reference to capability
- `input_schema: Dict[str, Any]` — input specification
- `output_schema: Dict[str, Any]` — output specification
- `metadata: Dict[str, Any]` — descriptive metadata
- `constraints: Dict[str, Any]` — conditions/constraints
- `compatibility: Dict[str, Any]` — compatibility declarations (backward, forward, breaking_changes)
- `error_definitions: Dict[str, str]` — defined failure outcomes
- `idempotency_declaration: str` — IDEMPOTENT / NON-IDEMPOTENT

**Methods:**
- `validate() -> bool` — basic field presence check
- `is_idempotent() -> bool` — returns True if idempotency == IDEMPOTENT
- `is_compatible_with(predecessor: Contract) -> CompatibilityResult`

## 4.2 Contract Identity (shared infrastructure)

`contracts/__init__.py`:

- `ContractIdempotency` enum: IDEMPOTENT, NON-IDEMPOTENT
- `ContractIdentity` (frozen): contract_id, version, capability_reference

## 4.3 ContractEnforcer Interface

`contract_enforcer/interfaces/enforcer_interface.py`:

- `ContractEnforcerInterface` Protocol:
  - `validate_contract(contract: Contract) -> bool`
  - `negotiate_contract(offered: ContractIdentity, supported: List[ContractIdentity]) -> NegotiationResult`
  - `verify_compatibility(contract: Contract, predecessor: Contract) -> CompatibilityResult`
  - `get_health() -> str`

## 4.4 ContractEnforcer Service

`contract_enforcer/services/enforcer_service.py`:

Orchestrator yang mengelola:
- Internal registry of known contracts
- Validation, negotiation, compatibility orchestration
- Lifecycle management

## 4.5 Negotiator Service

`contract_enforcer/services/negotiator_service.py`:

Version negotiation algorithm:
1. Collect all versions of the same contract_id from both parties
2. Filter to versions in both parties' supported lists → intersection
3. Exclude DEPRECATED from intersection (but keep as fallback)
4. If non-deprecated intersection exists → pick highest version
5. If only deprecated exists → DEPRECATED_ONLY
6. If no intersection → NEGOTIATION_FAILED
7. Deterministic: same inputs → same result

## 4.6 Lifecycle

`contract_enforcer/lifecycle/enforcer_lifecycle.py`:

- `ContractEnforcerLifecycleState`: UNINITIALIZED, INITIALIZING, RUNNING, STOPPING, STOPPED
- `RUNNING.is_operational() → True`
- `STOPPED.is_terminal() → True`

## 4.7 Exceptions

`contract_enforcer/exceptions/contract_errors.py`:

- `ContractError` (base)
- `InvalidContract` — malformed or invalid contract
- `UnknownContract` — contract not recognized
- `UnsupportedVersion` — version not supported
- `IncompatibleContract` — no mutually compatible version
- `NegotiationFailure` — negotiation failed
- `MissingField` — required field absent
- `EnforcerNotOperational` — lifecycle not RUNNING

---

# SECTION 5 — SPECIFICATION COMPLIANCE

| CONTRACT_SPEC Requirement | Implementation |
|---|---|
| Contract = Input + Output + Metadata + Constraints + Compatibility + Error | All 6 fields in Contract model |
| Contract Identity = ID + Version + Capability Reference | ContractIdentity in `contracts/` |
| Compatibility: backward, forward, breaking, compatible, deprecated | CompatibilityResult + CompatibilityValidator |
| Version negotiation: agree on single version, prefer compatible, prefer non-deprecated | NegotiatorService algorithm |
| Failures: Unknown, Unsupported, Invalid, Malformed, Missing, Incompatible | ContractError hierarchy |
| Interoperability: agree on Identity + Structure + Compatibility + Negotiation | Full Contract model + services |

---

# SECTION 6 — DEPENDENCY INTEGRITY

## 6.1 Dependency DAG

```
    shared ──► contracts ──► contract_enforcer
```

`contract_enforcer` imports:
- `sam.runtime.shared.*` — enums, types, constants
- `sam.runtime.contracts.*` — ContractIdentity, ContractIdempotency

`contract_enforcer` MUST NOT import:
- `sam.runtime.citizen_host`
- `sam.runtime.capability_manager`
- `sam.runtime.discovery_resolver`
- `sam.runtime.approval_coordinator`
- `sam.runtime.execution_scheduler`
- `sam.runtime.audit_recorder`
- `sam.runtime.registry`
- `sam.runtime.internal`

## 6.2 Layer Dependency

Internal layer dependency (within contract_enforcer):
```
models ← contracts ← state ← lifecycle ← validation ← services ← interfaces (top)
```

---

# SECTION 7 — BOUNDARY ENFORCEMENT

## 7.1 Public Contract

Only these are publicly consumable:
- `validate_contract(contract) -> bool`
- `negotiate_contract(offered, supported) -> NegotiationResult`
- `verify_compatibility(contract, predecessor) -> CompatibilityResult`
- `get_health() -> str`

## 7.2 Boundary Rules

| Rule | Description |
|---|---|
| BR-1 | ContractEnforcer does not resolve capabilities |
| BR-2 | ContractEnforcer does not produce approval decisions |
| BR-3 | ContractEnforcer does not execute operations |
| BR-4 | ContractEnforcer does not record audit |
| BR-5 | ContractEnforcer defines idempotency; does not observe it at runtime |

---

# SECTION 8 — AUDIT CERTIFICATIONS

## Audit 1 — Responsibility Completeness
**LULUS.** Semua responsibility dari R5-001 §2.4 dan I0-001 §2.4 diimplementasikan:
- ✅ R3: Expose immutable contracts → Contract frozen model
- ✅ R11: Declare idempotency → IdempotencyDeclaration di Contract

## Audit 2 — Specification Compliance
**LULUS.** Semua CONTRACT_SPEC requirement dipenuhi:
- ✅ Contract Structure (6 fields)
- ✅ Contract Identity (3 elements)
- ✅ Compatibility Rules (5 types)
- ✅ Version Negotiation (4 rules)
- ✅ Failure Behaviour (6 defined failures)
- ✅ Interoperability guarantee

## Audit 3 — ADR Compliance
**LULUS.**
- ✅ ADR-003: Contract declares idempotency (IDEMPOTENT/NON-IDEMPOTENT), Execution observes
- ✅ ADR-006: Contract as external boundary mechanism
- ✅ ADR-000, ADR-001, ADR-002, ADR-004, ADR-005, ADR-007: tidak dilanggar

## Audit 4 — Architecture Compliance
**LULUS.** Contract Enforcer Unit sesuai posisi R4-001 Component 4, mengonsumsi Contract Reference dari Discovery Resolver dan memproduksi Contract + Idempotency Declaration + Negotiated Version.

## Audit 5 — Boundary Integrity
**LULUS.** Tidak mengeksekusi, tidak menyetujui, tidak menemukan Capability, tidak merekam audit.

## Audit 6 — Dependency Integrity
**LULUS.** Hanya depend pada `shared` + `contracts`. Tidak ada import dari unit module lain.

## Audit 7 — Test Results
*(akan diisi setelah test dijalankan)*

## Audit 8 — Final Certification
*(akan diisi setelah semua test PASSED)*

---

## STOP Condition

| Trigger | Status |
|---|---|
| Perlu ADR baru | Tidak |
| Perlu ubah Foundation | Tidak |
| Perlu ubah Specification | Tidak |
| Perlu ubah Architecture | Tidak |
| Perlu ubah Design | Tidak |
| Perlu ubah Engineering | Tidak |
| Perlu ubah Blueprint | Tidak |

→ **STOP tidak aktif.** Implementasi dapat dilanjutkan.
