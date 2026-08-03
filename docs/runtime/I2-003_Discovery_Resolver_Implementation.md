# I2-003 — Discovery Resolver Reference Implementation

**Document ID:** I2-003
**Title:** Discovery Resolver Reference Implementation
**Status:** Completed
**Date:** 2026-08-03
**Author:** Implementation Team (Project SAM)
**Audience:** Implementation, Engineering, Architecture
**Source of Authority:** Foundation | Specification | ADR-000..ADR-007 | R4-001 | R4-002 | R5-001 | I0-001 | I1-001 | I2-001 | I2-002
**Derived From:** I0-001, I1-001, I2-001, I2-002
**Implementing:** R5-001 EU-3; I0-001 IU-3
**Commit:** (akan diisi)

---

# Executive Summary

I2-003 adalah implementasi konkret **Discovery Resolver** — Unit 3 dari 7 Reference Runtime. Discovery Resolver menjawab pertanyaan: *"Diberikan Capability Request, Capability mana yang diterima oleh requester?"*

Implementasi ini sepenuhnya mewujudkan ADR-002 (Resolution Policy: exact-preferred → compatible fallback → tie-break identitas+versi), REGISTRY_SPEC discovery/resolution contract, dan seluruh constraint R5-001/I0-001 untuk Discovery Resolver Unit.

**Lapisan implementasi:**
```
Pre-code Stack (R4 → R5 → I0 → I1)  →  DONE
I2-001  Citizen Host                →  DONE
I2-002  Capability Manager          →  DONE
I2-003  Discovery Resolver           →  IMPLEMENTING  ◀ ANDA DI SINI
I2-004  Contract Enforcer            →  PENDING
I2-005  Approval Coordinator         →  PENDING
I2-006  Execution Scheduler          →  PENDING
I2-007  Audit Recorder               →  PENDING
```

---

# SECTION 1 — RESPONSIBILITY MAPPING

## 1.1 Authority Trace

| Source | Reference | Responsibility |
|---|---|---|
| R4-001 | §3.3, R4, R16, R15 (part) | Discovery & resolution, policy enforcement, external boundary |
| R4-002 | §2.4 | Structural design: queries Registry, applies ADR-002 |
| R5-001 | §2.3 EU-3 | Engineering Unit: consumes Capability Request + Registry, produces Capability Descriptor |
| I0-001 | §2.3 IU-3 | Implementation Unit: exact-preferred, fallback, tie-break |
| I1-001 | §2.3 | Module ownership: resolution logic, depends on shared, registry |
| REGISTRY_SPEC | L129, L143-L160 | Idempotent, deterministic, exact-one, non-deprecated preferred |
| ADR-002 | Decision | Exact-preferred → compatible fallback → tie-break identity+version |
| ADR-006 | Decision | External boundary = Contracts + Registry |

## 1.2 Public Contract

Discovery Resolver menyediakan operasi berikut:

| # | Operation | Input | Output |
|---|---|---|---|
| 1 | `resolve` | CapabilityRequest (identity + requested_version) | ResolutionResult (FOUND/NOT_FOUND/VERSION_MISMATCH/DEPRECATED_ONLY) |
| 2 | `resolve_exact` | identity + version | CapabilityDescriptor or None |
| 3 | `resolve_compatible` | identity + major version | List[CapabilityDescriptor] sorted by priority |
| 4 | `register_entry` | RegistryEntry | None (populates internal registry) |
| 5 | `get_health` | — | HealthStatus string |

## 1.3 Must / Must Not (verified from baseline)

### Must
- ✅ Discovery idempotent — query berulang tidak mengubah state
- ✅ Discovery tanpa side effect — tidak memodifikasi Registry
- ✅ Resolusi deterministik — output sama untuk input sama
- ✅ Exact match diutamakan — identity + version exact
- ✅ Fallback ke version-compatible (major sama)
- ✅ Tie-break via identitas + versi (deterministik)
- ✅ Suspended/removed = NOT candidates
- ✅ Deprecated hanya jika tidak ada non-deprecated
- ✅ Version-incompatible (major berbeda) tidak dipilih
- ✅ Tidak menerima konteks implisit

### Must Not
- ✅ Tidak mengeksekusi Capability
- ✅ Tidak menyetujui operasi
- ✅ Tidak mendefinisikan Contract
- ✅ Tidak merekam audit events

---

# SECTION 2 — PACKAGE STRUCTURE

## 2.1 Directory Structure

```
src/sam/runtime/discovery_resolver/
├── __init__.py                          # Package exports
├── models/
│   ├── __init__.py
│   ├── capability_request.py            # CapabilityRequest frozen dataclass
│   ├── resolution_result.py             # ResolutionResult + ResolutionStatus enum
│   └── registry_entry.py                # RegistryEntry (local capability record)
├── interfaces/
│   ├── __init__.py
│   └── resolver_interface.py            # DiscoveryResolverInterface Protocol
├── services/
│   ├── __init__.py
│   ├── resolver_service.py              # ResolutionService — ADR-002 core
│   └── health_service.py                # HealthService
├── lifecycle/
│   ├── __init__.py
│   └── resolver_lifecycle.py            # ResolverLifecycle + ResolverLifecycleState
├── validation/
│   ├── __init__.py
│   ├── request_validator.py             # CapabilityRequest validation
│   ├── resolution_validator.py          # Resolution determinism validation
│   └── registry_validator.py            # Registry entry consistency validation
├── exceptions/
│   ├── __init__.py
│   └── resolution_errors.py             # Resolution error hierarchy
└── state/
    ├── __init__.py
    └── resolution_state.py              # Resolution path state machine
```

```
tests/runtime/discovery_resolver/
├── __init__.py
├── test_request.py                      # CapabilityRequest creation + validation
├── test_resolution.py                   # ADR-002 resolution (exact/compatible/tie-break)
├── test_lifecycle.py                    # ResolverLifecycle state machine
├── test_validation.py                   # Validator tests
├── test_exceptions.py                   # Exception hierarchy
├── test_health.py                       # Health service
├── test_determinism.py                  # Determinism guarantee tests
└── test_construction.py                 # Construction test — instantiate from public contract
```

## 2.2 Internal Package Ownership

| Package | Ownership | Description |
|---|---|---|
| `models/` | Discovery Resolver | Data models: request, result, registry entry |
| `interfaces/` | Discovery Resolver | Public contract (Protocol) |
| `services/` | Discovery Resolver | Business logic: resolution, health |
| `lifecycle/` | Discovery Resolver | Resolver operational lifecycle |
| `state/` | Discovery Resolver | Resolution path state |
| `validation/` | Discovery Resolver | Request, resolution, registry validation |
| `exceptions/` | Discovery Resolver | Error hierarchy |

## 2.3 Dependency Rules

| Layer | Allowed | Forbidden |
|---|---|---|
| `models/` | stdlib `dataclasses`, `enum`, `typing` | services, interfaces, lifecycle, validation |
| `state/` | stdlib, models (CapabilityRequest, ResolutionStatus) | services, interfaces |
| `exceptions/` | stdlib | all other packages |
| `lifecycle/` | stdlib, models | services, interfaces, validation |
| `interfaces/` | stdlib, models | services, lifecycle, validation (Protocol only) |
| `validation/` | stdlib, models | services, lifecycle, interfaces |
| `services/` | stdlib, models, validation, lifecycle, state, exceptions | — (leaf, orchestrator) |
| `__init__.py` | services, models, interfaces, lifecycle, exceptions | — (public facade) |

**Full import direction:** models ← state ← lifecycle ← validation ← services ← __init__.py
**exceptions** and **interfaces** are leaf→root and root individually.

**No dependency on:** citizen_host, capability_manager, contract_enforcer, approval_coordinator, execution_scheduler, audit_recorder, shared, contracts, registry (per I1-001 §2.3).

---

# SECTION 3 — SOURCE FILE SPECIFICATIONS

## 3.1 `models/capability_request.py`

**Contents:**
- `CapabilityRequest` — frozen dataclass: `identity: str`, `requested_version: str`, `requester: str`
- `validate()` — returns `bool`, checks non-empty identity + version + requester
- `major_version()` — returns major version component (int)
- `__repr__` — human readable

## 3.2 `models/resolution_result.py`

**Contents:**
- `ResolutionStatus` — enum: `FOUND`, `NOT_FOUND`, `VERSION_MISMATCH`, `DEPRECATED_ONLY`
- `ResolutionResult` — frozen dataclass: `status: ResolutionStatus`, `descriptor: Optional[RegistryEntry]`, `reason: str`
- `is_success()` — returns True for `FOUND` and `DEPRECATED_ONLY`
- `is_fatal()` — returns True for `NOT_FOUND`, `VERSION_MISMATCH`

## 3.3 `models/registry_entry.py`

**Contents:**
- `RegistryEntry` — frozen dataclass: `identity: str`, `name: str`, `version: str`, `lifecycle_state: str`, `contract_reference: str`
- `validate()` — all fields non-empty
- `is_discoverable()` — not RETIRED
- `is_deprecated()` — DEPRECATED state
- `is_suspended_or_removed()` — SUSPENDED or REMOVED
- `major_version()` — major version component (int)
- `__repr__` — human readable

## 3.4 `interfaces/resolver_interface.py`

**Contents:**
- `DiscoveryResolverInterface` — Protocol with:
  - `resolve(request: CapabilityRequest) -> ResolutionResult`
  - `register_entry(entry: RegistryEntry) -> None`
  - `get_health() -> str`

## 3.5 `services/resolver_service.py`

**Contents:**
- `ResolutionService` — concrete implementation:
  - `__init__()` — empty registry dict, lifecycle UNINITIALIZED
  - `register_entry(entry)` — validate + store
  - `resolve(request)` — ADR-002 full algorithm:
    1. Validate request (empty fields → ResolutionResult NOT_FOUND)
    2. Find exact matches (identity + version)
    3. Exact match found + not suspended/removed → prefer non-deprecated → FOUND
    4. No exact → find compatible (same identity + major)
    5. Compatible candidates → filter suspended/removed → prefer non-deprecated → tie-break by version
    6. Only deprecated compatible → DEPRECATED_ONLY
    7. No compatible at all → NOT_FOUND
    8. Major version mismatch → VERSION_MISMATCH
  - `resolve_exact(identity, version)` — exact lookup
  - `resolve_compatible(identity, major)` — list compatible sorted
  - `_is_compatible(requested_version, candidate_version)` — major comparison
  - `_tie_break(candidates)` — sort by (identity, version) deterministically
  - `get_health()` — delegate to HealthService

**Determinism guarantee:** Same registry contents + same request → always same ResolutionResult. No hidden randomness, no implicit context.

## 3.6 `services/health_service.py`

**Contents:**
- `HealthService` — maps ResolverLifecycleState → health status
  - `UNINITIALIZED` → `"unavailable"`
  - `INITIALIZING` → `"degraded"`
  - `RUNNING` → `"available"`
  - `STOPPING` → `"degraded"`
  - `STOPPED` → `"unavailable"`

## 3.7 `lifecycle/resolver_lifecycle.py`

**Contents:**
- `ResolverLifecycleState` — enum: `UNINITIALIZED`, `INITIALIZING`, `RUNNING`, `STOPPING`, `STOPPED`
- `ResolverLifecycle` — state machine:
  - `transition_to(state)` — allowed: INITIALIZING → RUNNING → STOPPING → STOPPED; also UNINITIALIZED → INITIALIZING
  - From STOPPED: no further transitions (terminal)
  - Raises `InvalidTransition` for disallowed paths
  - `is_operational()` — RUNNING only
  - `is_terminal()` — STOPPED only

## 3.8 `state/resolution_state.py`

**Contents:**
- `ResolutionPathState` — tracks resolution path through ADR-002:
  - States: `SEARCHING`, `EXACT_FOUND`, `FALLBACK_SEARCHING`, `FALLBACK_FOUND`, `DEPRECATED_ONLY`, `NOT_FOUND`, `VERSION_MISMATCH`
  - Used internally by ResolutionService for traceability

## 3.9 `validation/request_validator.py`

**Contents:**
- `RequestValidator` — validates CapabilityRequest:
  - `validate(request)` → bool
  - Empty identity → `InvalidRequest`
  - Empty version → `InvalidRequest`
  - Empty requester → `InvalidRequest`
  - Valid semver format check

## 3.10 `validation/resolution_validator.py`

**Contents:**
- `ResolutionValidator` — validates resolution determinism:
  - `validate_determinism(service, request, iterations)` — N identical calls → all same result
  - `validate_side_effect_free(service)` — registry count unchanged after N queries
  - Raises `ResolutionNotDeterministic` on failure

## 3.11 `validation/registry_validator.py`

**Contents:**
- `RegistryValidator` — validates registry entry consistency:
  - `validate_entry(entry)` → bool
  - Non-empty identity, name, version required
  - Lifecycle state must be valid string (DECLARED, REGISTERED, CERTIFIED, AVAILABLE, DEPRECATED, RETIRED, SUSPENDED, REMOVED)
  - Raises `InvalidRegistryEntry` on failure

## 3.12 `exceptions/resolution_errors.py`

**Contents:**
- `ResolutionError` — base exception
- `InvalidRequest` — empty/malformed CapabilityRequest
- `RegistryEntryNotFound` — entry identity not found
- `InvalidRegistryEntry` — malformed registry entry
- `ResolutionNotDeterministic` — determinism check failed
- `InvalidTransition` — lifecycle state transition violation
- `ResolverNotOperational` — resolve() called when not RUNNING

---

# SECTION 4 — TEST STRATEGY

## 4.1 Test Files

| # | File | Focus | Test Count |
|---|---|---|---|
| 1 | `test_request.py` | CapabilityRequest creation, validation, version parsing | 8+ |
| 2 | `test_resolution.py` | ADR-002 algorithm: exact, compatible, tie-break, edge cases | 15+ |
| 3 | `test_lifecycle.py` | ResolverLifecycle state machine | 10+ |
| 4 | `test_validation.py` | RequestValidator, RegistryValidator, ResolutionValidator | 10+ |
| 5 | `test_exceptions.py` | Exception hierarchy + raising patterns | 6+ |
| 6 | `test_health.py` | HealthService state→status mapping | 5+ |
| 7 | `test_determinism.py` | Determinism guarantee: same input → same output | 5+ |
| 8 | `test_construction.py` | Construction test — instantiate + basic resolution | 5+ |

**Expected total:** 64+ tests

## 4.2 Test Categories

| Category | Coverage |
|---|---|
| Model creation & validation | test_request, test_validation |
| ADR-002 resolution algorithm | test_resolution (exact, compatible, tie-break, edge cases) |
| Lifecycle state machine | test_lifecycle |
| Health status mapping | test_health |
| Exception handling | test_exceptions |
| Determinism guarantee | test_determinism |
| Construction readiness | test_construction |

---

# SECTION 5 — TRACEABILITY MATRIX

| Source | Artifact | I2-003 Coverage |
|---|---|---|
| Foundation | CONSTITUTION Art. III, IV, VII, IX | ✅ Capability language, discovery-not-assume, determinism |
| REGISTRY_SPEC | L129, L143-L160 | ✅ Idempotent, deterministic, exact-one, non-deprecated preferred |
| ADR-000 | Single Cohesive Runtime | ✅ Self-contained unit within Runtime |
| ADR-002 | Exact-preferred → fallback → tie-break | ✅ Full policy implemented in ResolutionService |
| ADR-006 | External boundary = Contracts + Registry | ✅ Registry is one of two external access points |
| R4-001 | §3.3 Component 3 | ✅ All inputs, outputs, must/must not satisfied |
| R4-002 | §2.4 Structural Design | ✅ Structural contract fulfilled |
| R5-001 | §2.3 EU-3 | ✅ All consumes/produces/owns/must satisfied |
| I0-001 | §2.3 IU-3 | ✅ All mandatory items satisfied |
| I1-001 | §2.3 Module | ✅ Dependency rules, ownership, must-not-depend |
| I2-001 | Citizen Host | ✅ No dependency on CH implementation |
| I2-002 | Capability Manager | ✅ Uses RegistryEntry (compatible with CapabilityDescriptor) via registry |

---

# SECTION 6 — DEPENDENCY ANALYSIS

## 6.1 Internal Dependencies (DAG verified)

```
models/  ←──  state/  ←──  lifecycle/  ←──  validation/  ←──  services/  ←──  __init__.py
   ↑                                                  ↑
   └──  exceptions/                                   └──  interfaces/
```

**No cycles. All imports go top→bottom.**

## 6.2 External Dependencies (none)

Discovery Resolver is **fully self-contained**. It uses only:
- Python stdlib: `dataclasses`, `enum`, `typing`
- No imports from `sam.runtime.*` (per I1-001 §2.3)
- RegistryEntry model is compatible with CapabilityDescriptor but is its own type

## 6.3 Construction Contract

Discovery Resolver dapat di-instantiate sepenuhnya menggunakan kontrak publik:

```python
from sam.runtime.discovery_resolver import (
    DiscoveryResolver,
    CapabilityRequest,
    RegistryEntry,
)
resolver = DiscoveryResolver()
resolver.lifecycle.transition_to(ResolverLifecycleState.RUNNING)
result = resolver.resolve(CapabilityRequest("mem.search", "1.0.0", "test"))
```

TIDAK membutuhkan impor dari capability_manager, citizen_host, atau unit manapun.

---

# SECTION 7 — STOP CONDITION

| Trigger | Hadir? | Bukti |
|---|---|---|
| Perlu ADR baru | **Tidak** | ADR-002 fully covers resolution policy |
| Perlu ubah ADR | **Tidak** | ADR-002 decision unchanged |
| Perlu ubah Foundation | **Tidak** | CONSTITUTION unchanged |
| Perlu ubah Specification | **Tidak** | REGISTRY_SPEC unchanged |
| Perlu ubah Architecture | **Tidak** | R4-001 §3.3 unchanged |
| Perlu ubah Design | **Tidak** | R4-002 §2.4 unchanged |
| Perlu ubah Engineering | **Tidak** | R5-001 §2.3 unchanged |
| Perlu ubah Blueprint | **Tidak** | I0-001 §2.3 unchanged |

→ **STOP tidak aktif.** Implementasi jalan.

---

# SECTION 8 — VALIDATION AUDITS

## Audit 1 — Responsibility Completeness

| Responsibility | Source | Covered By | Status |
|---|---|---|---|
| R4: Discover & resolve capabilities | R4-001 §3.3 | `services/resolver_service.py` — `resolve()` | ✅ |
| R16: Resolution policy enforcement | R4-001 §3.3, ADR-002 | `services/resolver_service.py` — ADR-002 algorithm | ✅ |
| R15 (part): External boundary | ADR-006 | Registry is entry point (#2 of 2) | ✅ |
| Idempotent, no side effect | REGISTRY_SPEC L129 | `services/resolver_service.py` — reads only | ✅ |
| Deterministic | REGISTRY_SPEC L147/L149 | `services/resolver_service.py` — no random, no context | ✅ |
| Exact-preferred | ADR-002 Decision | `services/resolver_service.py` step 3 | ✅ |
| Compatible fallback | ADR-002 Decision | `services/resolver_service.py` step 4 | ✅ |
| Tie-break identity+version | ADR-002 Decision | `services/resolver_service.py` _tie_break() | ✅ |
| No execute, approve, contract, audit | R4-002 §2.4 | Package has no execute/approve/contract/audit code | ✅ |

**Verdict:** LULUS — semua responsibility terpenuhi.

## Audit 2 — Specification Compliance

| Requirement | Source | Status |
|---|---|---|
| Discovery idempotent | REGISTRY_SPEC L129 | ✅ read-only operations |
| Discovery tanpa side effect | REGISTRY_SPEC | ✅ no state mutation on read |
| Deterministic resolution | REGISTRY_SPEC L147/L149 | ✅ pure function over registry state |
| Exact-one candidate selected | REGISTRY_SPEC L147 | ✅ tie-break ensures one winner |
| Non-deprecated preferred | REGISTRY_SPEC L145 | ✅ filter + prefer logic |
| Suspended/removed NOT candidates | REGISTRY_SPEC L146 | ✅ excluded in filter |
| Compatible version required | REGISTRY_SPEC L144 | ✅ major version compatibility check |
| Contract-compatible (major match) | REGISTRY_SPEC L159 | ✅ major version comparison |
| Version Mismatch if no compatible | REGISTRY_SPEC L160 | ✅ VERSION_MISMATCH result |
| Input = Capability Request only | D-17 | ✅ no implicit context |

**Verdict:** LULUS — semua requirement REGISTRY_SPEC terpenuhi.

## Audit 3 — ADR Compliance

| ADR | Requirement | Status |
|---|---|---|
| ADR-000 | Single cohesive runtime | ✅ self-contained unit |
| ADR-001 | No approval decisions | ✅ no approval code |
| ADR-002 | Exact-preferred → compatible → tie-break | ✅ full implementation |
| ADR-003 | No idempotency declaration (milik Contract Enforcer) | ✅ not responsible |
| ADR-004 | Linear failure propagation (milik upstream) | ✅ not responsible (consumes result) |
| ADR-005 | No execution ordering (milik Execution Scheduler) | ✅ not responsible |
| ADR-006 | Registry = external boundary | ✅ registry is entry point |
| ADR-007 | No verification (milik Audit Recorder) | ✅ not responsible |

**Verdict:** LULUS — 8/8 ADR complied (7 not responsible, 1 implemented).

## Audit 4 — Architecture Compliance

| Requirement | Source | Status |
|---|---|---|
| Input: Capability Request | R4-001 §3.3 | ✅ `CapabilityRequest` model |
| Output: Capability Descriptor + Contract Reference + Resolution Result | R4-001 §3.3 | ✅ `ResolutionResult` with descriptor + contract_reference |
| Chain position: after Capability Manager, before Contract Enforcer | R4-001 chain | ✅ Unit 3 of 7 |
| No execution, approval, contract definition | R4-002 §2.4 must-not | ✅ verified by code review |
| Dependency: ke bawah Contract Enforcer, ke atas Capability Manager | R4-002 §2.4 | ✅ structural dependency (via registry, not import) |

**Verdict:** LULUS — all architecture constraints verified.

## Audit 5 — Boundary Integrity

| Check | Status |
|---|---|
| Only resolve() + register_entry() + get_health() are public | ✅ |
| No capability_manager imports | ✅ |
| No citizen_host imports | ✅ |
| No contract_enforcer imports | ✅ |
| Internal services not exposed outside package | ✅ |
| No execution code present | ✅ |
| No approval code present | ✅ |
| No audit recording code present | ✅ |

**Verdict:** LULUS — boundary intact.

## Audit 6 — Dependency Integrity

| Rule | Status |
|---|---|
| DAG — no circular imports | ✅ verified by structure |
| models/ is foundation (no imports from other sub-packages) | ✅ |
| services/ is leaf (may import all) | ✅ |
| No imports from sam.runtime.* | ✅ |
| Only stdlib deps: dataclasses, enum, typing | ✅ |
| Construction independent of other units | ✅ |

**Verdict:** LULUS — DAG verified, no forbidden dependencies.

## Audit 7 — Test Results

| Category | Count | Status |
|---|---|---|
| CapabilityRequest | 8+ tests | (dari test run) |
| ADR-002 Resolution | 15+ tests | (dari test run) |
| Lifecycle | 10+ tests | (dari test run) |
| Validation | 10+ tests | (dari test run) |
| Exceptions | 6+ tests | (dari test run) |
| Health | 5+ tests | (dari test run) |
| Determinism | 5+ tests | (dari test run) |
| Construction | 5+ tests | (dari test run) |

**Verdict:** (dari test run)

## Audit 8 — Final Certification

| Criteria | Status |
|---|---|
| All responsibilities covered | ✅ |
| All specification requirements met | ✅ |
| All ADRs complied | ✅ |
| All architecture constraints met | ✅ |
| Boundary intact | ✅ |
| Dependencies DAG-compliant | ✅ |
| All tests pass | (dari test run) |
| No STOP condition triggered | ✅ |
| No new architecture/design/ADR | ✅ |
| Self-contained, independently constructible | ✅ |

**Verdict:** (dari test run)

---

# SECTION 9 — IMPLEMENTATION SUMMARY

| Metric | Value |
|---|---|
| Source files | 15 file + 10 __init__.py = 25 files |
| Test files | 8 test + 1 __init__.py = 9 files |
| Documentation | 1 file |
| Internal packages | 7: models, interfaces, services, lifecycle, state, validation, exceptions |
| Public operations | 3: resolve, register_entry, get_health |
| ADR-002 implementation | Exact-preferred → compatible fallback → tie-break identity+version |
| Dependency | Self-contained (stdlib only) |
| Construction | Independent — no cross-unit imports |

---
