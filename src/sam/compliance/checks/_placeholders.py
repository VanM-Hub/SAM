"""99 placeholder compliance checks from P1-001.

Each check has the correct ID, level, category, description,
evidence_type, severity, and baseline_ref but NO execution_fn.

These are framework structure only — checker implementations
come in a later phase.
"""

from ..models.check_model import ComplianceCheck
from ..models.level import ComplianceLevel
from ..models.category import ComplianceCategory
from ..models.evidence_type import EvidenceType
from ..models.severity import Severity
from ..registry.check_registry import ComplianceRegistry


def register_placeholder_checks(registry: ComplianceRegistry) -> int:
    """Register all 99 placeholder compliance checks from P1-001.

    Each check is defined with its ID, level, category, description,
    evidence type, severity, and baseline reference. No execution_fn
    is attached — these are framework structure only.

    Returns the number of checks registered.
    """
    checks = _build_all_checks()
    registry.register_all(checks)
    return len(checks)


def _build_all_checks():
    """Build all 99 placeholder compliance checks."""
    checks = []

    # --- L0 STRUCTURAL (12 checks) ---
    structural_checks = [
        ("L0-01", "7 unit directories exist", EvidenceType.FILE_EXISTS, Severity.CRITICAL, "I1-001 \u00a73"),
        ("L0-02", "No 8th unit directory", EvidenceType.FILE_ABSENT, Severity.CRITICAL, "I0-001 S1"),
        ("L0-03", "Each unit has models/ subdirectory", EvidenceType.FILE_EXISTS, Severity.CRITICAL, "I1-001 \u00a74"),
        ("L0-04", "Each unit has interfaces/ subdirectory", EvidenceType.FILE_EXISTS, Severity.CRITICAL, "I1-001 \u00a74"),
        ("L0-05", "Each unit has services/ subdirectory", EvidenceType.FILE_EXISTS, Severity.CRITICAL, "I1-001 \u00a74"),
        ("L0-06", "Each unit has lifecycle/ subdirectory", EvidenceType.FILE_EXISTS, Severity.CRITICAL, "I1-001 \u00a74"),
        ("L0-07", "Each unit has validation/ subdirectory", EvidenceType.FILE_EXISTS, Severity.CRITICAL, "I1-001 \u00a74"),
        ("L0-08", "Each unit has exceptions/ subdirectory", EvidenceType.FILE_EXISTS, Severity.CRITICAL, "I1-001 \u00a74"),
        ("L0-09", "Units with enums have state/ subdirectory", EvidenceType.FILE_EXISTS, Severity.MAJOR, "I1-001 \u00a74"),
        ("L0-10", "All __init__.py files present", EvidenceType.FILE_EXISTS, Severity.MAJOR, "I1-001 \u00a75"),
        ("L0-11", "No extra top-level directories in runtime package", EvidenceType.FILE_ABSENT, Severity.CRITICAL, "I1-001 \u00a73"),
        ("L0-12", "Test directory mirrors source structure", EvidenceType.FILE_EXISTS, Severity.MINOR, "I0-001 O12"),
    ]
    for cid, desc, etype, sev, ref in structural_checks:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # --- L1 SPECIFICATION (40 checks) ---
    # Citizen (5)
    citizen = [
        ("L1-C01", "Citizenship = governance relationship", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CITIZEN_SPEC L10-12"),
        ("L1-C02", "Citizens publish Capabilities", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CITIZEN_SPEC L18-20"),
        ("L1-C03", "Citizens obey Contracts", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CITIZEN_SPEC L21-23"),
        ("L1-C04", "Citizens participate in Governance", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CITIZEN_SPEC L24-26"),
        ("L1-C05", "Citizens are auditable", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CITIZEN_SPEC L27-29"),
    ]
    for cid, desc, etype, sev, ref in citizen:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L1_SPECIFICATION,
            category=ComplianceCategory.SPECIFICATION,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # Capability (6)
    capability = [
        ("L1-CA01", "Universal capability language", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CAPABILITY_SPEC"),
        ("L1-CA02", "D/M/S classification", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CAPABILITY_SPEC"),
        ("L1-CA03", "6-state lifecycle", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CAPABILITY_SPEC"),
        ("L1-CA04", "Certification process", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CAPABILITY_SPEC"),
        ("L1-CA05", "Survive implementation replacement", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CAPABILITY_SPEC"),
        ("L1-CA06", "Same-state transition = no-op", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CAPABILITY_SPEC"),
    ]
    for cid, desc, etype, sev, ref in capability:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L1_SPECIFICATION,
            category=ComplianceCategory.SPECIFICATION,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # Registry (5)
    registry_spec = [
        ("L1-R01", "Register Capability on publication", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "REGISTRY_SPEC"),
        ("L1-R02", "Compound key (identity, version)", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "REGISTRY_SPEC"),
        ("L1-R03", "Discover by request", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "REGISTRY_SPEC"),
        ("L1-R04", "Exact-preferred, compatible fallback", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-002"),
        ("L1-R05", "Deterministic tie-break", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-002"),
    ]
    for cid, desc, etype, sev, ref in registry_spec:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L1_SPECIFICATION,
            category=ComplianceCategory.SPECIFICATION,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # Contract (5)
    contract = [
        ("L1-CO01", "Immutable Contracts", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CONTRACT_SPEC"),
        ("L1-CO02", "Version negotiation", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CONTRACT_SPEC"),
        ("L1-CO03", "Compatibility enforcement", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CONTRACT_SPEC"),
        ("L1-CO04", "Fields: Input/Output/Metadata/Constraints/Error", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "CONTRACT_SPEC \u00a72"),
        ("L1-CO05", "Idempotency declared by Contract", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-003"),
    ]
    for cid, desc, etype, sev, ref in contract:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L1_SPECIFICATION,
            category=ComplianceCategory.SPECIFICATION,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # Approval (6)
    approval = [
        ("L1-AP01", "Accountable Decision Framework", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-001"),
        ("L1-AP02", "Deterministic decision", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-001"),
        ("L1-AP03", "Decision explanation", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-001"),
        ("L1-AP04", "6-state decision lifecycle", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "APPROVAL_SPEC"),
        ("L1-AP05", "7-state per-approval lifecycle", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "APPROVAL_SPEC"),
        ("L1-AP06", "Approval \u2192 Execution reference", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "APPROVAL_SPEC"),
    ]
    for cid, desc, etype, sev, ref in approval:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L1_SPECIFICATION,
            category=ComplianceCategory.SPECIFICATION,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # Execution (6)
    execution = [
        ("L1-EX01", "Approval-arrival ordering", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-005"),
        ("L1-EX02", "8-state execution lifecycle", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "EXECUTION_SPEC"),
        ("L1-EX03", "Operation-Defined Idempotency", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-003"),
        ("L1-EX04", "Linear forward failure", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-004"),
        ("L1-EX05", "No execution without approval", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "EXECUTION_SPEC"),
        ("L1-EX06", "Protocol injection pattern", EvidenceType.SOURCE_CONTAINS, Severity.MAJOR, "I0-001 \u00a72.6"),
    ]
    for cid, desc, etype, sev, ref in execution:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L1_SPECIFICATION,
            category=ComplianceCategory.SPECIFICATION,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # Audit (7)
    audit = [
        ("L1-AU01", "7-field immutable identity", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "AUDIT_SPEC L57-69"),
        ("L1-AU02", "Immutable audit record", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "AUDIT_SPEC L72-84"),
        ("L1-AU03", "3-state lifecycle", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "AUDIT_SPEC L87-100"),
        ("L1-AU04", "5-link traceability chain", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "AUDIT_SPEC L106-115"),
        ("L1-AU05", "6 defined failure types", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "AUDIT_SPEC L129-140"),
        ("L1-AU06", "Verification as state transition", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-007"),
        ("L1-AU07", "Observe-only, no influence", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "AUDIT_SPEC L193"),
    ]
    for cid, desc, etype, sev, ref in audit:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L1_SPECIFICATION,
            category=ComplianceCategory.SPECIFICATION,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # --- L2 ADR (17 checks) ---
    adr_checks = [
        ("L2-01", "Single package (no multi-host distribution)", EvidenceType.FILE_ABSENT, Severity.CRITICAL, "ADR-000 Alt A"),
        ("L2-02", "Deterministic decision with reason", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-001 Alt C"),
        ("L2-03", "DecisionPolicy pluggable", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-001 Alt C"),
        ("L2-04", "Exact-preferred resolution", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-002"),
        ("L2-05", "Compatible fallback", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-002"),
        ("L2-06", "Deterministic tie-break (version sort)", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-002"),
        ("L2-07", "Compound key (identity, version)", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-002"),
        ("L2-08", "Contract declares idempotency", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-003 Alt B"),
        ("L2-09", "Execution observes idempotency", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-003 Alt B"),
        ("L2-10", "Failure forward-only", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-004 Alt B"),
        ("L2-11", "Audit as termination", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-004 Alt B"),
        ("L2-12", "Approval-arrival = execution order", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-005 Alt A"),
        ("L2-13", "No priority reordering", EvidenceType.SOURCE_ABSENT, Severity.CRITICAL, "ADR-005 Alt A"),
        ("L2-14", "External boundary = Contracts + Registry", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-006 Alt A"),
        ("L2-15", "No third access mechanism", EvidenceType.SOURCE_ABSENT, Severity.CRITICAL, "ADR-006 Alt A"),
        ("L2-16", "Verification in-unit (not separate)", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-007 Alt B"),
        ("L2-17", "Recorded \u2192 Verified within AR", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-007 Alt B"),
    ]
    for cid, desc, etype, sev, ref in adr_checks:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L2_ADR,
            category=ComplianceCategory.ADR,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # --- L3 BEHAVIORAL (22 checks) ---
    # Determinism (7)
    units = [
        ("CH", "citizen_host"), ("CM", "capability_manager"),
        ("DR", "discovery_resolver"), ("CE", "contract_enforcer"),
        ("AC", "approval_coordinator"), ("ES", "execution_scheduler"),
        ("AR", "audit_recorder"),
    ]
    for i, (code, _name) in enumerate(units):
        cid = "L3-D%02d" % (i + 1)
        checks.append(ComplianceCheck(
            check_id=cid,
            level=ComplianceLevel.L3_BEHAVIORAL,
            category=ComplianceCategory.TESTING,
            description="%s: same input \u2192 same behavior" % code,
            evidence_type=EvidenceType.TEST_PASS,
            severity=Severity.MAJOR,
            baseline_ref="CONSTITUTION VII",
        ))

    # Idempotency (4)
    idem = [
        ("L3-ID01", "CM: same-state transition = no-op", EvidenceType.TEST_PASS, Severity.MAJOR, "ADR-003"),
        ("L3-ID02", "CE: Contract declares idempotency", EvidenceType.TEST_PASS, Severity.MAJOR, "ADR-003"),
        ("L3-ID03", "ES: IDEMPOTENT re-execution \u2192 COMPLETED", EvidenceType.TEST_PASS, Severity.MAJOR, "ADR-003"),
        ("L3-ID04", "ES: NON-IDEMPOTENT re-execution \u2192 Conflict", EvidenceType.TEST_PASS, Severity.MAJOR, "ADR-003"),
    ]
    for cid, desc, etype, sev, ref in idem:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L3_BEHAVIORAL,
            category=ComplianceCategory.TESTING,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # Lifecycle (7)
    lc_units = [
        ("L3-LC01", "CH: lifecycle transitions valid"),
        ("L3-LC02", "CM: 6-state lifecycle transitions valid"),
        ("L3-LC03", "DR: resolver lifecycle valid"),
        ("L3-LC04", "CE: contract state valid"),
        ("L3-LC05", "AC: 6-state decision lifecycle valid"),
        ("L3-LC06", "ES: 8-state execution lifecycle valid"),
        ("L3-LC07", "AR: 3-state audit lifecycle valid"),
    ]
    for cid, desc in lc_units:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L3_BEHAVIORAL,
            category=ComplianceCategory.TESTING,
            description=desc, evidence_type=EvidenceType.TEST_PASS,
            severity=Severity.MAJOR, baseline_ref="Spec lifecycle",
        ))

    # Isolation (4)
    isolation = [
        ("L3-IS01", "No runtime unit imports another runtime unit", EvidenceType.IMPORT_ILLEGAL, Severity.CRITICAL, "R4-001, I1-001 DAG"),
        ("L3-IS02", "No runtime imports presentation layer", EvidenceType.IMPORT_ILLEGAL, Severity.CRITICAL, "I1-001 DAG"),
        ("L3-IS03", "No cross-unit side effects", EvidenceType.TEST_PASS, Severity.MAJOR, "R4-001"),
        ("L3-IS04", "Each unit independently testable", EvidenceType.TEST_PASS, Severity.MAJOR, "R4-001"),
    ]
    for cid, desc, etype, sev, ref in isolation:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L3_BEHAVIORAL,
            category=ComplianceCategory.INTEGRATION,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    # --- L4 SYSTEM (8 checks) ---
    system = [
        ("L4-01", "Full test suite passes", EvidenceType.TEST_PASS, Severity.CRITICAL, "P0-001 Audit 7"),
        ("L4-02", "No skipped/xfail tests", EvidenceType.TEST_COUNT, Severity.MINOR, "P0-001 Audit 7"),
        ("L4-03", "6-link traceability chain unbroken", EvidenceType.TRACE_CHAIN, Severity.CRITICAL, "P0-001 Audit 6"),
        ("L4-04", "No invariant violation", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "R4-001"),
        ("L4-05", "No constraint violation", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "R5-001"),
        ("L4-06", "No cycle in dependency DAG", EvidenceType.IMPORT_ILLEGAL, Severity.CRITICAL, "R4-001"),
        ("L4-07", "All boundaries enforced", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "ADR-006"),
        ("L4-08", "Linear chain order preserved", EvidenceType.SOURCE_CONTAINS, Severity.CRITICAL, "R4-001"),
    ]
    for cid, desc, etype, sev, ref in system:
        checks.append(ComplianceCheck(
            check_id=cid, level=ComplianceLevel.L4_SYSTEM,
            category=ComplianceCategory.FOUNDATION,
            description=desc, evidence_type=etype, severity=sev,
            baseline_ref=ref,
        ))

    return checks
