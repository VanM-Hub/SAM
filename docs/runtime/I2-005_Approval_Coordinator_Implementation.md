# I2-005 — Approval Coordinator Reference Implementation

**Document ID:** I2-005
**Title:** Approval Coordinator Reference Implementation
**Status:** Completed
**Date:** 2026-08-03
**Author:** Chief Architect (Project SAM Architecture Decision Making)
**Audience:** Implementation Team, Engineering, Architecture
**Source of Authority:** Foundation | APPROVAL_SPEC | ADR-001 | R4-001 | R4-002 | R5-001 | I0-001 | I1-001
**Derived From:** I0-001 Reference Runtime Implementation Blueprint, I1-001 Repository Skeleton

---

# Executive Summary

I2-005 mengimplementasikan **Approval Coordinator** — Unit 5 dari 7 Reference Runtime Implementation Units. Unit ini adalah **gerbang otorisasi** yang menghasilkan keputusan Approval binding sebelum Execution, menerapkan Accountable Decision Framework (ADR-001).

**Implementation Chain:**
```
I2-001 (Citizen Host) ✅     — 44 tests
I2-002 (Capability Manager) ✅ — 77 tests
I2-003 (Discovery Resolver) ✅ — 81 tests
I2-004 (Contract Enforcer) ✅  — 119 tests
I2-005 (Approval Coordinator)  — this document
I2-006 (Execution Scheduler) ⬜
I2-007 (Audit Recorder) ⬜
```

---

# SECTION 1 — TRACEABILITY MATRIX

| Source | Requirement | Implementation Location |
|---|---|---|
| R5-001 R5 | Produce authorization decision before execution | `services/coordinator_service.py` — gate mutlak |
| R5-001 R18 | Apply Accountable Decision Framework | `services/coordinator_service.py` — DecisionPolicy pluggable |
| APPROVAL_SPEC | Approval Identity (ID, Decision Context, Contract Ref, Capability Ref) | `models/approval_identity.py` |
| APPROVAL_SPEC | Approval Request | `models/approval_request.py` |
| APPROVAL_SPEC | Approval Decision states (Approved/Rejected/Expired/Cancelled/Superseded) | `models/approval_decision.py` |
| APPROVAL_SPEC | Lifecycle: Created→Pending→Approved/Rejected/Expired/Cancelled→Archived | `state/approval_state.py` |
| APPORVAL_SPEC | Legal transitions | `state/approval_state.py` — `is_valid_transition()` |
| APPROVAL_SPEC | Defined failures (Missing Contract, Unknown Capability, etc.) | `exceptions/approval_errors.py` |
| ADR-001 | Deterministic output shape | `models/approval_decision.py` — 6 fixed states |
| ADR-001 | Explainable (Decision Reason) | `models/approval_decision.py` — `decision_reason` |
| ADR-001 | Auditable | `models/approval_decision.py` — `decision_context` metadata |
| ADR-001 | Mechanism-open (automated or human-mediated) | `services/coordinator_service.py` — `DecisionPolicy` callable |
| ADR-001 | Binding decision | `state/approval_state.py` — no revert from terminal |
| I1-001 | Depends only on shared + contracts | All imports verified |
| I1-001 | Must NOT depend on other units | No cross-unit imports |

---

# SECTION 2 — ARCHITECTURE COMPLIANCE

## 2.1 Position in 7-Component Model

```
Citizen Host ──→ Capability Manager ──→ Discovery Resolver
                                              │
                                              ▼
                                       Contract Enforcer
                                              │
                                              ▼
                                    [Approval Coordinator]  ← Gate
                                              │
                                              ▼
                                     Execution Scheduler
                                              │
                                              ▼
                                       Audit Recorder
```

## 2.2 ADR Compliance

| ADR | Compliance | How |
|---|---|---|
| ADR-000 | ✅ | One cohesive Approval Coordinator per domain |
| ADR-001 | ✅ | Accountable Decision Framework — deterministic output, explainable, auditable, mechanism-open |
| ADR-002 | N/A | Approval Coordinator does not resolve capabilities |
| ADR-003 | N/A | Idempotency observed by Execution, not Approval |
| ADR-004 | ✅ | Approval failures produce defined errors, not silent propagation |
| ADR-005 | N/A | Linear Ordering enforced by Execution Scheduler |
| ADR-006 | ✅ | Public API only; no internal access bypass |
| ADR-007 | N/A | Verification handled by Audit Recorder |

## 2.3 Dependency Integrity

```
shared (types/enums) ──→ contracts ──→ approval_coordinator
```

- `approval_coordinator` imports: `shared` (enums, base types), `contracts` (ContractIdentity)
- `approval_coordinator` does NOT import: `citizen_host`, `capability_manager`, `discovery_resolver`, `contract_enforcer`, `execution_scheduler`, `audit_recorder`, `registry`, `internal`

---

# SECTION 3 — MODULE STRUCTURE

```
approval_coordinator/               # Unit 5 — Authorization Gate
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── approval_identity.py        # ApprovalIdentity dataclass
│   ├── approval_request.py         # ApprovalRequest dataclass
│   └── approval_decision.py        # ApprovalDecision (6 states + reason)
├── interfaces/
│   ├── __init__.py
│   └── coordinator_interface.py    # ApprovalCoordinatorInterface Protocol
├── services/
│   ├── __init__.py
│   ├── coordinator_service.py      # ApprovalCoordinator orchestrator
│   └── health_service.py           # HealthService
├── lifecycle/
│   ├── __init__.py
│   └── coordinator_lifecycle.py    # ApprovalCoordinatorLifecycle
├── state/
│   ├── __init__.py
│   └── approval_state.py           # ApprovalState machine
├── validation/
│   ├── __init__.py
│   ├── request_validator.py        # RequestValidator
│   ├── decision_validator.py       # DecisionValidator
│   ├── lifecycle_validator.py      # LifecycleValidator
│   └── boundary_validator.py       # BoundaryValidator
└── exceptions/
    ├── __init__.py
    └── approval_errors.py          # ApprovalError hierarchy
```

---

# SECTION 4 — IMPLEMENTATION DETAILS

## 4.1 ApprovalIdentity (models/)

Frozen dataclass per APPROVAL_SPEC:
- `approval_id: str` — global identifier
- `decision_context: str` — context of the authorization decision
- `contract_reference: ContractIdentity` — reference to the governing Contract
- `capability_reference: str` — reference to the Capability
- `citizen_reference: Optional[str]` — optional Citizen reference

## 4.2 ApprovalRequest (models/)

Frozen input dataclass:
- `decision_context: str`
- `contract_reference: ContractIdentity`
- `capability_reference: str`
- `citizen_reference: Optional[str]`
- `requested_by: str` — who is making this request
- `expires_at: Optional[int]` — optional expiry timestamp

## 4.3 ApprovalDecision (models/)

Frozen decision dataclass:
- `state: ApprovalDecisionState` — APPROVED/REJECTED/EXPIRED/CANCELLED/SUPERSEDED
- `decision_reason: str` — explainable reason (ADR-001)
- `decided_at: float` — timestamp of decision
- `decided_by: str` — who/what made the decision
- `approval_id: str` — reference to the Approval
- Static factory methods: `approved()`, `rejected()`, `expired()`, `cancelled()`, `superseded()`

## 4.4 ApprovalCoordinatorInterface (interfaces/)

Protocol with 5 public methods:
- `create_approval(request: ApprovalRequest) -> ApprovalIdentity`
- `evaluate(approval_id: str, policy: DecisionPolicy) -> ApprovalDecision`
- `transition(approval_id: str, new_state: ApprovalLifecycleState) -> None`
- `get(approval_id: str) -> ApprovalState`
- `get_health() -> dict`

## 4.5 ApprovalCoordinator (services/)

Orchestrator implementing ApprovalCoordinatorInterface:
- `DecisionPolicy`: Callable[[ApprovalRequest], Type[ApprovalDecisionState]] — pluggable decision logic
- `_approvals: Dict[str, ApprovalState]` — internal store
- Gate enforcement: no evaluate/transition when not operational
- Deterministic: same request + same policy → same decision

## 4.6 HealthService (services/)

5-state health mapping:
- UNINITIALIZED → UNAVAILABLE
- INITIALIZING → DEGRADED
- RUNNING → AVAILABLE
- STOPPING → DEGRADED
- STOPPED → UNAVAILABLE

## 4.7 ApprovalCoordinatorLifecycle (lifecycle/)

5 states: UNINITIALIZED → INITIALIZING → RUNNING → STOPPING → STOPPED
- RUNNING is operational
- STOPPED is terminal
- Same-state transition = no-op

## 4.8 ApprovalState Machine (state/)

Per-approval lifecycle states (APPROVAL_SPEC):
- CREATED, PENDING, APPROVED, REJECTED, EXPIRED, CANCELLED, ARCHIVED
- Legal transitions defined by APPROVAL_SPEC transition table
- ARCHIVED is terminal
- `is_valid_transition()` validates legality
- `transition()` executes or raises InvalidTransitionError

## 4.9 Validation (validation/)

Four validators:
- **RequestValidator**: validates ApprovalRequest fields (non-empty context, valid contract ref)
- **DecisionValidator**: validates ApprovalDecision state, reason presence
- **LifecycleValidator**: validates transition legality
- **BoundaryValidator**: ensures only public API used; no bypass

## 4.10 Exceptions (exceptions/)

7 exception types per APPROVAL_SPEC:
- `ApprovalError` (base)
- `MissingContractError`
- `UnknownCapabilityError`
- `RegistryResolutionError`
- `InvalidRequestError`
- `ExpiredRequestError`
- `ApprovalConflictError`
- `InvalidTransitionError`
- `ApprovalNotFoundError`

---

# SECTION 5 — BOUNDARY ENFORCEMENT

| Rule | Enforcement |
|---|---|
| No direct execution | No execution-related code in any file |
| No contract definition | Uses ContractIdentity from contracts module only |
| No audit recording | No audit-related code |
| No bypass | All access through public API methods |
| No non-deterministic decisions | Same input + same policy = same output |

---

# SECTION 6 — TEST COVERAGE

| Test File | What It Tests |
|---|---|
| `test_approval_model.py` | ApprovalIdentity, ApprovalRequest, ApprovalDecision creation, validation, immutability, factory methods |
| `test_lifecycle.py` | CoordinatorLifecycle state machine, valid/invalid transitions |
| `test_state.py` | ApprovalState per-approval lifecycle, legal transitions, terminal behavior |
| `test_validation.py` | All 4 validators |
| `test_service.py` | ApprovalCoordinator: create, evaluate, transition, get, deterministic |
| `test_exceptions.py` | Exception hierarchy |
| `test_health.py` | Health mapping across lifecycle states |
| `test_decision.py` | ApprovalDecision model: states, reason, factories |
| `test_determinism.py` | Repeated evaluation consistency, state isolation |
| `test_construction.py` | Independent instantiation without cross-unit deps |
| `test_boundary.py` | Boundary validator, no bypass detection |

---

# SECTION 7 — AUDITS

## Audit 1 — Responsibility Completeness
- [x] R5 — Produce authorization decision → `evaluate()` in coordinator_service.py
- [x] R18 — Accountable Decision Framework → DecisionPolicy pluggable mechanism
- [x] All APPROVAL_SPEC requirements → traced in Section 1

## Audit 2 — Specification Compliance
- [x] Approval Identity fields present
- [x] Approval Request fields present
- [x] All 5 decision states
- [x] All 7 lifecycle states
- [x] All legal transitions enforced
- [x] All defined failures

## Audit 3 — ADR Compliance
- [x] ADR-001: deterministic output shape (6 fixed states)
- [x] ADR-001: explainable (decision_reason)
- [x] ADR-001: auditable (decision_context + decided_at + decided_by)
- [x] ADR-001: mechanism-open (DecisionPolicy pluggable)

## Audit 4 — Architecture Compliance
- [x] Position in 7-component model: Unit 5, gate between Contract Enforcer and Execution
- [x] Does not own discovery, execution, or audit responsibility
- [x] No architecture-level violation

## Audit 5 — Boundary Integrity
- [x] Public API: create_approval, evaluate, transition, get, get_health
- [x] No bypass path exists
- [x] Internal state not directly mutable

## Audit 6 — Dependency Integrity
- [x] Only imports: shared, contracts
- [x] No import from: citizen_host, capability_manager, discovery_resolver, contract_enforcer, execution_scheduler, audit_recorder, registry, internal
- [x] DAG-verified

## Audit 7 — Test Results
- [x] All tests pass
- [x] Combined runtime tests pass

## Audit 8 — Final Certification
- [x] No new ADR created
- [x] No Foundation/Specification/Architecture/Design/Engineering/Blueprint modification
- [x] Implementation complete + tested + committed

**STATUS: 8/8 LULUS ✅**

---

# SECTION 8 — REFERENCES

| Document | Path |
|---|---|
| APPROVAL_SPEC | `docs/specifications/APPROVAL_SPECIFICATION.md` |
| ADR-001 | `docs/adr/ADR-001_Approval_Decision_Model.md` |
| R4-001 | `docs/runtime/R4-001_Reference_Runtime_Architecture.md` |
| R4-002 | `docs/runtime/R4-002_Reference_Runtime_Design.md` |
| R5-001 | `docs/runtime/R5-001_Reference_Runtime_Engineering_Model.md` |
| I0-001 | `docs/runtime/I0-001_Reference_Runtime_Implementation_Blueprint.md` |
| I1-001 | `docs/runtime/I1-001_Reference_Runtime_Repository_Skeleton.md` |
| I2-001 | `docs/runtime/I2-001_Citizen_Host_Implementation.md` |
| I2-002 | `docs/runtime/I2-002_Capability_Manager_Implementation.md` |
| I2-003 | `docs/runtime/I2-003_Discovery_Resolver_Implementation.md` |
| I2-004 | `docs/runtime/I2-004_Contract_Enforcer_Implementation.md` |
