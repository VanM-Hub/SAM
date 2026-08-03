"""All 99 compliance check metadata — canonical source of truth.

Generated from P1-001 Runtime Compliance Suite.
Each entry maps exactly one check ID to its complete CheckMetadata.

Do NOT hand-edit — regenerate from build_all_entries() if P1-001 changes.
"""

from typing import List

from .models import (
    CheckMetadata, CheckLevel, CheckCategory, CheckSeverity,
    EvidenceType, CheckAuthority, CheckerClass,
)


def _sev(s: str) -> CheckSeverity:
    return CheckSeverity[s]


def _ev(t: str) -> "EvidenceType":
    return EvidenceType[t]


def _ck(t: str) -> "CheckerClass":
    return CheckerClass[t]


# Evidence → Checker class mapping
_E2C = {
    "FILE_EXISTS": CheckerClass.FILE_EXISTS,
    "FILE_ABSENT": CheckerClass.FILE_ABSENT,
    "SOURCE_CONTAINS": CheckerClass.SOURCE_CONTAINS,
    "SOURCE_ABSENT": CheckerClass.SOURCE_ABSENT,
    "IMPORT_ILLEGAL": CheckerClass.IMPORT_ILLEGAL,
    "IMPORT_LEGAL": CheckerClass.IMPORT_LEGAL,
    "TEST_PASS": CheckerClass.TEST_RESULTS,
    "TEST_COUNT": CheckerClass.TEST_RESULTS,
    "LIFECYCLE_VALID": CheckerClass.LIFECYCLE,
    "TRACE_CHAIN": CheckerClass.TRACEABILITY,
}


def build_all_entries() -> List[CheckMetadata]:
    """Build all 99 CheckMetadata entries from P1-001."""
    L0 = CheckLevel.L0_STRUCTURAL
    L1 = CheckLevel.L1_SPECIFICATION
    L2 = CheckLevel.L2_ADR
    L3 = CheckLevel.L3_BEHAVIORAL
    L4 = CheckLevel.L4_SYSTEM

    RU = CheckCategory.RUNTIME_UNITS
    SPEC = CheckCategory.SPECIFICATION
    ADR = CheckCategory.ADR
    TESTING = CheckCategory.TESTING
    INTEG = CheckCategory.INTEGRATION
    FOUND = CheckCategory.FOUNDATION

    BLUEPRINT = CheckAuthority.BLUEPRINT
    SPEC_AUTH = CheckAuthority.SPECIFICATION
    ADR_AUTH = CheckAuthority.ADR
    CONST = CheckAuthority.CONSTITUTION
    ARCH = CheckAuthority.ARCHITECTURE
    ENG = CheckAuthority.ENGINEERING
    CERT = CheckAuthority.CERTIFICATION
    SYS = CheckAuthority.SYSTEM

    entries: List[CheckMetadata] = []

    # =========================================================================
    # L0 — STRUCTURAL (12 checks)
    # =========================================================================
    _entries_l0 = [
        ("L0-01", "FileExist_UnitDirectories", "I1-001",
         "FILE_EXISTS", "CRITICAL", BLUEPRINT,
         "7 unit directories exist under src/sam/runtime/",
         "Create the 7 unit directories as defined by I1-001.",
         ["L0-02"]),
        ("L0-02", "FileAbsent_No8thUnit", "I0-001 S1",
         "FILE_ABSENT", "CRITICAL", BLUEPRINT,
         "No 8th unit directory in runtime package",
         "Remove unauthorized directories from the runtime package.",
         ["L0-01"]),
        ("L0-03", "FileExist_ModelsSubdir", "I1-001 §4",
         "FILE_EXISTS", "CRITICAL", BLUEPRINT,
         "Each unit has models/ subdirectory",
         "Create models/ subdirectory in each unit.",
         ["L0-04", "L0-05", "L0-06", "L0-07", "L0-08"]),
        ("L0-04", "FileExist_InterfacesSubdir", "I1-001 §4",
         "FILE_EXISTS", "CRITICAL", BLUEPRINT,
         "Each unit has interfaces/ subdirectory",
         "Create interfaces/ subdirectory in each unit.",
         []),
        ("L0-05", "FileExist_ServicesSubdir", "I1-001 §4",
         "FILE_EXISTS", "CRITICAL", BLUEPRINT,
         "Each unit has services/ subdirectory",
         "Create services/ subdirectory in each unit.",
         []),
        ("L0-06", "FileExist_LifecycleSubdir", "I1-001 §4",
         "FILE_EXISTS", "CRITICAL", BLUEPRINT,
         "Each unit has lifecycle/ subdirectory",
         "Create lifecycle/ subdirectory in each unit.",
         []),
        ("L0-07", "FileExist_ValidationSubdir", "I1-001 §4",
         "FILE_EXISTS", "CRITICAL", BLUEPRINT,
         "Each unit has validation/ subdirectory",
         "Create validation/ subdirectory in each unit.",
         []),
        ("L0-08", "FileExist_ExceptionsSubdir", "I1-001 §4",
         "FILE_EXISTS", "CRITICAL", BLUEPRINT,
         "Each unit has exceptions/ subdirectory",
         "Create exceptions/ subdirectory in each unit.",
         []),
        ("L0-09", "FileExist_StateSubdir", "I1-001 §4",
         "FILE_EXISTS", "MAJOR", BLUEPRINT,
         "Units with enums have state/ subdirectory",
         "Create state/ subdirectory for units with enums.",
         []),
        ("L0-10", "FileExist_InitFiles", "I1-001 §5",
         "FILE_EXISTS", "MAJOR", BLUEPRINT,
         "All __init__.py files present in expected locations",
         "Create missing __init__.py files.",
         []),
        ("L0-11", "FileAbsent_ExtraTopLevel", "I1-001 §3",
         "FILE_ABSENT", "CRITICAL", BLUEPRINT,
         "No extra top-level directories in runtime package",
         "Remove unauthorized directories from runtime package.",
         []),
        ("L0-12", "FileExist_TestMirror", "I0-001 O12",
         "FILE_EXISTS", "MINOR", BLUEPRINT,
         "Test directory structure mirrors source structure",
         "Align test directory with source directory structure.",
         []),
    ]
    for cid, name, bref, ev, sev, auth, desc, rec, links in _entries_l0:
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L0, category=RU,
            severity=_sev(sev), authority=auth,
            evidence_type=_ev(ev), checker_class=_E2C[ev],
            expected_verdict="PASS",
            source_document="I1-001", baseline_ref=bref,
            description=desc, recommendation=rec,
            traceability=links,
            tags=["structural", "filesystem"],
        ))

    # =========================================================================
    # L1 — SPECIFICATION (40 checks)
    # =========================================================================
    # Citizen (5)
    citizen = [
        ("L1-C01", "Source_CitizenCertModel", "CITIZEN_SPEC L10-12",
         "Citizenship = governance relationship; Certification model exists",
         "Implement Certification model with governance properties."),
        ("L1-C02", "Source_HostServiceAccept", "CITIZEN_SPEC L18-20",
         "Citizens publish Capabilities via HostService.accept_citizen()",
         "Implement HostService.accept_citizen() method."),
        ("L1-C03", "Source_CertificationValidates", "CITIZEN_SPEC L21-23",
         "Citizens obey Contracts; CertificationService validates contract compliance",
         "Implement CertificationService with contract validation."),
        ("L1-C04", "Source_CertIsValidAudit", "CITIZEN_SPEC L24-26",
         "Citizens participate in Governance via Certification.is_valid() audit check",
         "Implement Certification.is_valid() with governance audit."),
        ("L1-C05", "Source_HealthIdentity", "CITIZEN_SPEC L27-29",
         "Citizens are auditable via Health reporting and identity tracking",
         "Implement HealthService with identity tracking fields."),
    ]
    for cid, name, bref, desc, rec in citizen:
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L1, category=SPEC,
            severity=CheckSeverity.CRITICAL, authority=SPEC_AUTH,
            evidence_type=EvidenceType.SOURCE_CONTAINS,
            checker_class=CheckerClass.SOURCE_CONTAINS,
            expected_verdict="PASS",
            source_document="CITIZEN_SPEC", baseline_ref=bref,
            description=desc, recommendation=rec,
            tags=["specification", "citizen"],
        ))

    # Capability (6)
    capability = [
        ("L1-CA01", "Source_CapabilityDescriptor", "CAPABILITY_SPEC",
         "Universal capability language via CapabilityDescriptor model",
         "Implement CapabilityDescriptor dataclass with universal fields."),
        ("L1-CA02", "Source_CapabilityTypeEnum", "CAPABILITY_SPEC",
         "D/M/S classification via CapabilityType enum",
         "Implement CapabilityType enum with D/M/S variants."),
        ("L1-CA03", "Source_CapabilityStateEnum", "CAPABILITY_SPEC",
         "6-state lifecycle via CapabilityState enum with transition logic",
         "Implement 6-state CapabilityState enum and transition rules."),
        ("L1-CA04", "Source_CertificationValidator", "CAPABILITY_SPEC",
         "Certification process via CertificationValidator",
         "Implement CertificationValidator with full certification flow."),
        ("L1-CA05", "Source_PreserveSemantics", "CAPABILITY_SPEC",
         "Survive implementation replacement via preserve_semantics()",
         "Implement preserve_semantics() for capability semantic preservation."),
        ("L1-CA06", "Source_CanTransitionGuard", "CAPABILITY_SPEC",
         "Same-state transition = no-op via can_transition() guard",
         "Implement can_transition() guard returning False for same-state."),
    ]
    for cid, name, bref, desc, rec in capability:
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L1, category=SPEC,
            severity=CheckSeverity.CRITICAL, authority=SPEC_AUTH,
            evidence_type=EvidenceType.SOURCE_CONTAINS,
            checker_class=CheckerClass.SOURCE_CONTAINS,
            expected_verdict="PASS",
            source_document="CAPABILITY_SPEC", baseline_ref=bref,
            description=desc, recommendation=rec,
            tags=["specification", "capability"],
        ))

    # Registry (5)
    registry_spec = [
        ("L1-R01", "Source_RegistryRegister", "REGISTRY_SPEC",
         "Register Capability on publication via register() method",
         "Implement register() method for capability registration."),
        ("L1-R02", "Source_RegistryKey", "REGISTRY_SPEC",
         "Compound key (identity, version) via RegistryKey model",
         "Implement RegistryKey with identity and version fields."),
        ("L1-R03", "Source_DiscoveryMethod", "REGISTRY_SPEC",
         "Discover by request via discover() method",
         "Implement discover() method for capability lookup."),
        ("L1-R04", "Source_ResolutionPipeline", "ADR-002",
         "Exact-preferred, compatible fallback resolution pipeline",
         "Implement resolution pipeline: exact match → compatible fallback."),
        ("L1-R05", "Source_VersionSortTieBreak", "ADR-002",
         "Deterministic tie-break via alphabetical version sort",
         "Implement deterministic version sort for tie-breaking."),
    ]
    for cid, name, bref, desc, rec in registry_spec:
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L1, category=SPEC,
            severity=CheckSeverity.CRITICAL, authority=SPEC_AUTH,
            evidence_type=EvidenceType.SOURCE_CONTAINS,
            checker_class=CheckerClass.SOURCE_CONTAINS,
            expected_verdict="PASS",
            source_document="REGISTRY_SPEC", baseline_ref=bref,
            description=desc, recommendation=rec,
            tags=["specification", "registry"],
        ))

    # Contract (5)
    contract = [
        ("L1-CO01", "Source_ImmutableContract", "CONTRACT_SPEC",
         "Immutable Contracts via frozen dataclass",
         "Implement Contract as frozen dataclass."),
        ("L1-CO02", "Source_NegotiatorService", "CONTRACT_SPEC",
         "Version negotiation via NegotiatorService",
         "Implement NegotiatorService with version negotiation."),
        ("L1-CO03", "Source_CompatibilityValidator", "CONTRACT_SPEC",
         "Compatibility enforcement via CompatibilityValidator",
         "Implement CompatibilityValidator for contract compatibility."),
        ("L1-CO04", "Source_ContractFields", "CONTRACT_SPEC §2",
         "Fields: Input/Output/Metadata/Constraints/Error in ContractModel",
         "Implement ContractModel with all 5 field categories."),
        ("L1-CO05", "Source_ContractIdempotency", "ADR-003",
         "Idempotency declared by Contract via ContractIdempotency type",
         "Implement ContractIdempotency type on Contract."),
    ]
    for cid, name, bref, desc, rec in contract:
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L1, category=SPEC,
            severity=CheckSeverity.CRITICAL, authority=SPEC_AUTH,
            evidence_type=EvidenceType.SOURCE_CONTAINS,
            checker_class=CheckerClass.SOURCE_CONTAINS,
            expected_verdict="PASS",
            source_document="CONTRACT_SPEC", baseline_ref=bref,
            description=desc, recommendation=rec,
            tags=["specification", "contract"],
        ))

    # Approval (6)
    approval = [
        ("L1-AP01", "Source_DecisionPolicy", "ADR-001",
         "Accountable Decision Framework via DecisionPolicy base class",
         "Implement DecisionPolicy base class with accountability."),
        ("L1-AP02", "Source_DecideMethod", "ADR-001",
         "Deterministic decision via decide() method",
         "Implement decide() method with deterministic logic."),
        ("L1-AP03", "Source_DecisionReason", "ADR-001",
         "Decision explanation via decision_reason field",
         "Add decision_reason field to Decision model."),
        ("L1-AP04", "Source_DecisionStateEnum", "APPROVAL_SPEC",
         "6-state decision lifecycle via DecisionState enum",
         "Implement 6-state DecisionState enum."),
        ("L1-AP05", "Source_ApprovalStateEnum", "APPROVAL_SPEC",
         "7-state per-approval lifecycle via ApprovalState enum",
         "Implement 7-state ApprovalState enum."),
        ("L1-AP06", "Source_ApprovalIdField", "APPROVAL_SPEC",
         "Approval → Execution reference via approval_id field",
         "Add approval_id field linking Approval to Execution."),
    ]
    for cid, name, bref, desc, rec in approval:
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L1, category=SPEC,
            severity=CheckSeverity.CRITICAL, authority=SPEC_AUTH,
            evidence_type=EvidenceType.SOURCE_CONTAINS,
            checker_class=CheckerClass.SOURCE_CONTAINS,
            expected_verdict="PASS",
            source_document="APPROVAL_SPEC", baseline_ref=bref,
            description=desc, recommendation=rec,
            tags=["specification", "approval"],
        ))

    # Execution (6)
    execution = [
        ("L1-EX01", "Source_OrderingValidator", "ADR-005",
         "Approval-arrival ordering via OrderingValidator",
         "Implement OrderingValidator for approval-order-preserved execution."),
        ("L1-EX02", "Source_ExecutionStateEnum", "EXECUTION_SPEC",
         "8-state execution lifecycle via ExecutionState enum",
         "Implement 8-state ExecutionState enum."),
        ("L1-EX03", "Source_IdempotencyValidator", "ADR-003",
         "Operation-Defined Idempotency via IdempotencyValidator",
         "Implement IdempotencyValidator for operation-defined idempotency."),
        ("L1-EX04", "Source_ForwardOnlyFailure", "ADR-004",
         "Linear forward failure — no backward exceptions",
         "Ensure failure propagation is forward-only; no rollback."),
        ("L1-EX05", "Source_ApprovalGate", "EXECUTION_SPEC",
         "No execution without approval via ApprovalGateValidator",
         "Implement ApprovalGateValidator guarding execution entry."),
        ("L1-EX06", "Source_SchedulerProtocol", "I0-001 §2.6",
         "Protocol injection pattern via SchedulerInterface Protocol class",
         "Implement SchedulerInterface as a Protocol for dependency injection."),
    ]
    for cid, name, bref, desc, rec in execution:
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L1, category=SPEC,
            severity=CheckSeverity.CRITICAL, authority=SPEC_AUTH,
            evidence_type=EvidenceType.SOURCE_CONTAINS,
            checker_class=CheckerClass.SOURCE_CONTAINS,
            expected_verdict="PASS",
            source_document="EXECUTION_SPEC", baseline_ref=bref,
            description=desc, recommendation=rec,
            tags=["specification", "execution"],
        ))

    # Audit (7)
    audit_checks = [
        ("L1-AU01", "Source_AuditIdentity", "AUDIT_SPEC L57-69",
         "7-field immutable identity via AuditIdentity (frozen)",
         "Implement AuditIdentity with 7 frozen fields."),
        ("L1-AU02", "Source_AuditRecord", "AUDIT_SPEC L72-84",
         "Immutable audit record via AuditRecord (frozen)",
         "Implement AuditRecord as frozen dataclass."),
        ("L1-AU03", "Source_AuditRecordState", "AUDIT_SPEC L87-100",
         "3-state lifecycle via AuditRecordState enum",
         "Implement 3-state AuditRecordState enum."),
        ("L1-AU04", "Source_TraceabilityValidator", "AUDIT_SPEC L106-115",
         "5-link traceability chain via TraceabilityValidator",
         "Implement TraceabilityValidator with 5-link chain validation."),
        ("L1-AU05", "Source_ExceptionTypes", "AUDIT_SPEC L129-140",
         "6 defined failure types via 10 exception types",
         "Implement all 10 exception types as defined."),
        ("L1-AU06", "Source_VerifyMethod", "ADR-007",
         "Verification as state transition via verify() method",
         "Implement verify() method performing Recorded→Verified transition."),
        ("L1-AU07", "Source_NoFeedback", "AUDIT_SPEC L193",
         "Observe-only, no influence via validate_no_feedback",
         "Implement validate_no_feedback to ensure observe-only behavior."),
    ]
    for cid, name, bref, desc, rec in audit_checks:
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L1, category=SPEC,
            severity=CheckSeverity.CRITICAL, authority=SPEC_AUTH,
            evidence_type=EvidenceType.SOURCE_CONTAINS,
            checker_class=CheckerClass.SOURCE_CONTAINS,
            expected_verdict="PASS",
            source_document="AUDIT_SPEC", baseline_ref=bref,
            description=desc, recommendation=rec,
            tags=["specification", "audit"],
        ))

    # =========================================================================
    # L2 — ADR (17 checks)
    # =========================================================================
    adr = [
        ("L2-01", "FileAbsent_MultiHost", "ADR-000 Alt A",
         "FILE_ABSENT", "CRITICAL",
         "Single package (no multi-host distribution)",
         "Remove any multi-host distribution artifacts.",
         ["L2-02"]),
        ("L2-02", "Source_DecideReason", "ADR-001 Alt C",
         "SOURCE_CONTAINS", "CRITICAL",
         "Deterministic decision with reason",
         "Implement decide() returning deterministic result with reason."),
        ("L2-03", "Source_PluggablePolicy", "ADR-001 Alt C",
         "SOURCE_CONTAINS", "CRITICAL",
         "DecisionPolicy pluggable via base class",
         "Implement DecisionPolicy as pluggable base class."),
        ("L2-04", "Source_MatchExact", "ADR-002",
         "SOURCE_CONTAINS", "CRITICAL",
         "Exact-preferred resolution via _match_exact()",
         "Implement _match_exact() for exact capability matching."),
        ("L2-05", "Source_MatchCompatible", "ADR-002",
         "SOURCE_CONTAINS", "CRITICAL",
         "Compatible fallback via _match_compatible()",
         "Implement _match_compatible() for fallback matching."),
        ("L2-06", "Source_VersionSort", "ADR-002",
         "SOURCE_CONTAINS", "CRITICAL",
         "Deterministic tie-break (version sort)",
         "Implement deterministic alphabetical version sort."),
        ("L2-07", "Source_CompoundKey", "ADR-002",
         "SOURCE_CONTAINS", "CRITICAL",
         "Compound key (identity, version) via RegistryKey",
         "Implement RegistryKey with identity+version compound key."),
        ("L2-08", "Source_ContractIdempotencyType", "ADR-003 Alt B",
         "SOURCE_CONTAINS", "CRITICAL",
         "Contract declares idempotency via ContractIdempotency type",
         "Implement ContractIdempotency type with declared semantics."),
        ("L2-09", "Source_IdempotencyObserver", "ADR-003 Alt B",
         "SOURCE_CONTAINS", "CRITICAL",
         "Execution observes idempotency via IdempotencyValidator",
         "Implement IdempotencyValidator observing contract idempotency."),
        ("L2-10", "Source_FailureForward", "ADR-004 Alt B",
         "SOURCE_CONTAINS", "CRITICAL",
         "Failure forward-only — no backward exceptions",
         "Ensure all exceptions propagate forward; no backtrack recovery."),
        ("L2-11", "Source_AuditTermination", "ADR-004 Alt B",
         "SOURCE_CONTAINS", "CRITICAL",
         "Audit as termination via validate_no_feedback",
         "Implement validate_no_feedback as termination guard."),
        ("L2-12", "Source_ArrivalOrder", "ADR-005 Alt A",
         "SOURCE_CONTAINS", "CRITICAL",
         "Approval-arrival = execution order via OrderingValidator",
         "Implement OrderingValidator preserving arrival order."),
        ("L2-13", "SourceAbsent_NoPriorityReorder", "ADR-005 Alt A",
         "SOURCE_ABSENT", "CRITICAL",
         "No priority reordering mechanism",
         "Remove any priority or reordering mechanism from scheduler."),
        ("L2-14", "Source_BoundaryValidator", "ADR-006 Alt A",
         "SOURCE_CONTAINS", "CRITICAL",
         "External boundary = Contracts + Registry via BoundaryValidator",
         "Implement BoundaryValidator with Contracts+Registry gates."),
        ("L2-15", "SourceAbsent_NoThirdAccess", "ADR-006 Alt A",
         "SOURCE_ABSENT", "CRITICAL",
         "No third access mechanism beyond Contracts + Registry",
         "Remove any access mechanism outside Contracts and Registry."),
        ("L2-16", "Source_InUnitVerify", "ADR-007 Alt B",
         "SOURCE_CONTAINS", "CRITICAL",
         "Verification in-unit (not separate) via verify() in AR",
         "Implement verify() method within Audit Recorder unit."),
        ("L2-17", "Source_RecordedToVerified", "ADR-007 Alt B",
         "SOURCE_CONTAINS", "CRITICAL",
         "Recorded → Verified within AR via RecorderService.verify()",
         "Implement RecorderService.verify() performing the state transition."),
    ]
    for item in adr:
        cid, name, bref, ev, sev, desc, *rest = item
        rec = rest[0] if rest else ""
        links = rest[1] if len(rest) > 1 else []
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L2, category=ADR,
            severity=_sev(sev), authority=ADR_AUTH,
            evidence_type=_ev(ev), checker_class=_E2C[ev],
            expected_verdict="PASS",
            source_document="ADR", baseline_ref=bref,
            description=desc, recommendation=rec,
            traceability=links,
            tags=["adr"],
        ))

    # =========================================================================
    # L3 — BEHAVIORAL (22 checks)
    # =========================================================================
    # Determinism (7)
    unit_codes = ["CH", "CM", "DR", "CE", "AC", "ES", "AR"]
    unit_names = ["Citizen Host", "Capability Manager", "Discovery Resolver",
                  "Contract Enforcer", "Approval Coordinator",
                  "Execution Scheduler", "Audit Recorder"]
    for i, (code, name) in enumerate(zip(unit_codes, unit_names)):
        cid = "L3-D%02d" % (i + 1)
        entries.append(CheckMetadata(
            check_id=cid, name="Test_%s_Determinism" % code, level=L3,
            category=TESTING, severity=CheckSeverity.MAJOR,
            authority=CONST, evidence_type=EvidenceType.TEST_PASS,
            checker_class=CheckerClass.TEST_RESULTS,
            expected_verdict="PASS", source_document="CONSTITUTION",
            baseline_ref="Art. VII",
            description="%s: same input → same behavior (deterministic)" % code,
            recommendation="Ensure %s deterministic behavior." % name,
            tags=["behavioral", "determinism", code.lower()],
        ))

    # Idempotency (4)
    idem = [
        ("L3-ID01", "Test_CM_Idempotency", "ADR-003",
         "CM: same-state transition = no-op",
         "Verify capability_manager idempotent state transitions."),
        ("L3-ID02", "Test_CE_Idempotency", "ADR-003",
         "CE: Contract declares idempotency",
         "Verify contract_enforcer declares idempotency correctly."),
        ("L3-ID03", "Test_ES_Idempotent", "ADR-003",
         "ES: IDEMPOTENT re-execution → COMPLETED",
         "Verify execution_scheduler idempotent re-execution behavior."),
        ("L3-ID04", "Test_ES_NonIdempotent", "ADR-003",
         "ES: NON-IDEMPOTENT re-execution → Conflict",
         "Verify execution_scheduler non-idempotent conflict detection."),
    ]
    for cid, name, bref, desc, rec in idem:
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L3, category=TESTING,
            severity=CheckSeverity.MAJOR, authority=ADR_AUTH,
            evidence_type=EvidenceType.TEST_PASS,
            checker_class=CheckerClass.TEST_RESULTS,
            expected_verdict="PASS", source_document="ADR-003",
            baseline_ref=bref, description=desc, recommendation=rec,
            tags=["behavioral", "idempotency"],
        ))

    # Lifecycle (7)
    lc = [
        ("L3-LC01", "Test_CH_Lifecycle", "CITIZEN_SPEC",
         "CH: lifecycle transitions valid",
         "Verify citizen_host lifecycle state machine."),
        ("L3-LC02", "Test_CM_Lifecycle", "CAPABILITY_SPEC",
         "CM: 6-state lifecycle transitions valid",
         "Verify capability_manager 6-state lifecycle."),
        ("L3-LC03", "Test_DR_Lifecycle", "REGISTRY_SPEC",
         "DR: resolver lifecycle valid",
         "Verify discovery_resolver lifecycle."),
        ("L3-LC04", "Test_CE_Lifecycle", "CONTRACT_SPEC",
         "CE: contract state valid",
         "Verify contract_enforcer contract state transitions."),
        ("L3-LC05", "Test_AC_Lifecycle", "APPROVAL_SPEC",
         "AC: 6-state decision lifecycle valid",
         "Verify approval_coordinator decision lifecycle."),
        ("L3-LC06", "Test_ES_Lifecycle", "EXECUTION_SPEC",
         "ES: 8-state execution lifecycle valid",
         "Verify execution_scheduler 8-state lifecycle."),
        ("L3-LC07", "Test_AR_Lifecycle", "AUDIT_SPEC",
         "AR: 3-state audit lifecycle valid",
         "Verify audit_recorder 3-state lifecycle."),
    ]
    for cid, name, bref, desc, rec in lc:
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L3, category=TESTING,
            severity=CheckSeverity.MAJOR, authority=SPEC_AUTH,
            evidence_type=EvidenceType.TEST_PASS,
            checker_class=CheckerClass.TEST_RESULTS,
            expected_verdict="PASS", source_document=bref,
            baseline_ref="lifecycle spec", description=desc,
            recommendation=rec,
            tags=["behavioral", "lifecycle"],
        ))

    # Isolation (4)
    isolation = [
        ("L3-IS01", "ImportIllegal_CrossUnitImports", "R4-001, I1-001 DAG",
         "IMPORT_ILLEGAL", "CRITICAL",
         "No runtime unit imports another runtime unit",
         "Remove cross-unit imports; route through shared infrastructure.",
         ["L3-IS02"]),
        ("L3-IS02", "ImportIllegal_NoPresentationImport", "I1-001 DAG",
         "IMPORT_ILLEGAL", "CRITICAL",
         "No runtime imports presentation layer",
         "Remove any imports from sam.presentation in runtime package.",
         ["L3-IS01"]),
        ("L3-IS03", "Test_CrossUnitSideEffects", "R4-001",
         "TEST_PASS", "MAJOR",
         "No cross-unit side effects",
         "Ensure unit tests are isolated from each other."),
        ("L3-IS04", "Test_UnitIndependence", "R4-001",
         "TEST_PASS", "MAJOR",
         "Each unit independently testable",
         "Ensure each unit can be tested without other runtime units."),
    ]
    for i, item in enumerate(isolation):
        cid, name, bref, ev, sev, desc, *rest = item
        rec = rest[0] if rest else ""
        links = rest[1] if len(rest) > 1 else []
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L3, category=INTEG,
            severity=_sev(sev), authority=ARCH,
            evidence_type=_ev(ev), checker_class=_E2C[ev],
            expected_verdict="PASS", source_document="R4-001",
            baseline_ref=bref, description=desc, recommendation=rec,
            traceability=links,
            tags=["behavioral", "isolation"],
        ))

    # =========================================================================
    # L4 — SYSTEM (8 checks)
    # =========================================================================
    system = [
        ("L4-01", "Test_FullSuitePasses", "P0-001 Audit 7",
         "TEST_PASS", "CRITICAL",
         "Full test suite passes with no failures",
         "Fix all failing tests before certification."),
        ("L4-02", "Test_NoSkippedTests", "P0-001 Audit 7",
         "TEST_COUNT", "MINOR",
         "No skipped/xfail tests — all tests must be PASSED",
         "Remove or fix any skipped/xfail test markers."),
        ("L4-03", "Trace_ChainUnbroken", "P0-001 Audit 6",
         "TRACE_CHAIN", "CRITICAL",
         "6-link traceability chain unbroken",
         "Fix broken traceability links in the execution chain."),
        ("L4-04", "Source_NoInvariantViolation", "R4-001",
         "SOURCE_CONTAINS", "CRITICAL",
         "No invariant violation from R4-001 list of 27",
         "Fix any violated invariants from R4-001."),
        ("L4-05", "Source_NoConstraintViolation", "R5-001",
         "SOURCE_CONTAINS", "CRITICAL",
         "No constraint violation from R5-001 list of 30",
         "Fix any violated constraints from R5-001."),
        ("L4-06", "ImportIllegal_NoCycle", "R4-001",
         "IMPORT_ILLEGAL", "CRITICAL",
         "No cycle in dependency DAG",
         "Break any import cycles in the dependency graph."),
        ("L4-07", "Source_BoundariesEnforced", "ADR-006",
         "SOURCE_CONTAINS", "CRITICAL",
         "All boundaries enforced as defined by ADR-006",
         "Fix any boundary violations (only Contracts+Registry access)."),
        ("L4-08", "Source_ChainOrderPreserved", "R4-001",
         "SOURCE_CONTAINS", "CRITICAL",
         "Linear chain order preserved (CH→CM→DR→CE→AC→ES→AR)",
         "Fix any out-of-order dependencies in the chain."),
    ]
    for item in system:
        cid, name, bref, ev, sev, desc, rec = item
        entries.append(CheckMetadata(
            check_id=cid, name=name, level=L4, category=FOUND,
            severity=_sev(sev), authority=SYS,
            evidence_type=_ev(ev), checker_class=_E2C[ev],
            expected_verdict="PASS",
            source_document="P0-001", baseline_ref=bref,
            description=desc, recommendation=rec,
            tags=["system", "integrity"],
        ))

    return entries
