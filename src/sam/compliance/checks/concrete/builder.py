"""Assemble concrete checkers from the catalog + manifest (P1-008).

Builds a deterministic mapping {check_id: BaseComplianceCheck instance}
for all 99 checks. Each checker class reads the BaselineSnapshot
(P1-007) from the CheckContext; per-check parameters (which sub-dir,
which symbol, which predicate) are supplied by the builder from the
catalog metadata so no checker hardcodes a path or authority.

Python 3.8 compatible.
"""

from __future__ import annotations

from typing import Dict, Optional

from ...catalog.catalog import ComplianceCheckCatalog
from ...catalog.models import CheckMetadata
from ...manifest.manifest import ComplianceManifest
from ...models.level import ComplianceLevel
from ...models.category import ComplianceCategory
from ...models.severity import Severity
from ...models.evidence_type import EvidenceType
from ..base.base_check import BaseComplianceCheck

# Batch check modules
from . import l0_structural as _l0
from . import source_required as _src

# -- L1 required symbols (derived from P1-004 catalog descriptions) -----------
# Each L1 check verifies at least one of these concrete artifacts exists
# in the source tree. Symbols are extracted from the catalog description
# (the 'via X' artifact naming) — no checker hardcodes a path or authority.
_L1_SYMBOLS = {
    "L1-AP01": ("DecisionPolicy",),
    "L1-AP02": ("decide",),
    "L1-AP03": ("decision_reason",),
    "L1-AP04": ("DecisionState",),
    "L1-AP05": ("ApprovalState",),
    "L1-AP06": ("approval_id",),
    "L1-AU01": ("AuditIdentity",),
    "L1-AU02": ("AuditRecord", "frozen"),
    "L1-AU03": ("AuditRecordState",),
    "L1-AU04": ("TraceabilityValidator",),
    "L1-AU05": ("exception", "Error"),
    "L1-AU06": ("verify",),
    "L1-AU07": ("validate_no_feedback",),
    "L1-C01": ("Certification",),
    "L1-C02": ("accept_citizen",),
    "L1-C03": ("CertificationService",),
    "L1-C04": ("is_valid",),
    "L1-C05": ("health", "identity"),
    "L1-CA01": ("CapabilityDescriptor",),
    "L1-CA02": ("CapabilityType",),
    "L1-CA03": ("CapabilityState",),
    "L1-CA04": ("CertificationValidator",),
    "L1-CA05": ("preserve_semantics",),
    "L1-CA06": ("can_transition",),
    "L1-CO01": ("@dataclass", "frozen"),
    "L1-CO02": ("NegotiatorService",),
    "L1-CO03": ("CompatibilityValidator",),
    "L1-CO04": ("Input", "Output"),
    "L1-CO05": ("Idempotency",),
    "L1-EX01": ("OrderingValidator",),
    "L1-EX02": ("ExecutionState",),
    "L1-EX03": ("IdempotencyValidator",),
    "L1-EX04": ("exception",),
    "L1-EX05": ("ApprovalGateValidator",),
    "L1-EX06": ("SchedulerInterface",),
    "L1-R01": ("register",),
    "L1-R02": ("RegistryKey",),
    "L1-R03": ("discover",),
    "L1-R04": ("_match", "compat"),
    "L1-R05": ("version", "sort"),
}

# -- Enum maps (catalog string -> engine enum) -------------------------------

_LV = {
    "L0": ComplianceLevel.L0_STRUCTURAL,
    "L1": ComplianceLevel.L1_SPECIFICATION,
    "L2": ComplianceLevel.L2_ADR,
    "L3": ComplianceLevel.L3_BEHAVIORAL,
    "L4": ComplianceLevel.L4_SYSTEM,
}

_CAT = {
    "Foundation": ComplianceCategory.FOUNDATION,
    "Specification": ComplianceCategory.SPECIFICATION,
    "ADR": ComplianceCategory.ADR,
    "Architecture": ComplianceCategory.ARCHITECTURE,
    "Engineering": ComplianceCategory.ENGINEERING,
    "Blueprint": ComplianceCategory.BLUEPRINT,
    "Runtime Units": ComplianceCategory.RUNTIME_UNITS,
    "Integration": ComplianceCategory.INTEGRATION,
    "Testing": ComplianceCategory.TESTING,
    "Design": ComplianceCategory.DESIGN,
}

_SEV = {
    "CRITICAL": Severity.CRITICAL,
    "MAJOR": Severity.MAJOR,
    "MINOR": Severity.MINOR,
    "INFO": Severity.INFO,
}

_EV = {
    "FILE_EXISTS": EvidenceType.FILE_EXISTS,
    "FILE_ABSENT": EvidenceType.FILE_ABSENT,
    "SOURCE_CONTAINS": EvidenceType.SOURCE_CONTAINS,
    "SOURCE_ABSENT": EvidenceType.SOURCE_ABSENT,
    "TEST_PASS": EvidenceType.TEST_PASS,
    "TEST_COUNT": EvidenceType.TEST_COUNT,
    "IMPORT_LEGAL": EvidenceType.IMPORT_LEGAL,
    "IMPORT_ILLEGAL": EvidenceType.IMPORT_ILLEGAL,
    "LIFECYCLE_VALID": EvidenceType.LIFECYCLE_VALID,
    "TRACE_CHAIN": EvidenceType.TRACE_CHAIN,
}


def _new(cls, md: CheckMetadata, **extra) -> BaseComplianceCheck:
    """Instantiate a checker from catalog metadata."""
    return cls(
        check_id=md.check_id,
        level=_LV[md.level.value],
        category=_CAT[md.category.value],
        description=md.description,
        evidence_type=_EV[md.evidence_type.value],
        severity=_SEV[md.severity.value],
        baseline_ref=md.baseline_ref,
        recommendation=md.recommendation,
        **extra,
    )


def _md(catalog: ComplianceCheckCatalog) -> Dict[str, CheckMetadata]:
    return {x.check_id: x for x in catalog.list_all()}


class Builder:
    """Builds concrete checks for a single level batch."""

    def __init__(self, catalog: ComplianceCheckCatalog,
                 manifest: Optional[ComplianceManifest] = None) -> None:
        self._catalog = catalog
        self._manifest = manifest

    @property
    def catalog(self) -> ComplianceCheckCatalog:
        return self._catalog

    def build_all(self) -> Dict[str, BaseComplianceCheck]:
        checks: Dict[str, BaseComplianceCheck] = {}
        checks.update(self.build_l0())
        checks.update(self.build_l1())
        return checks

    # -- L0 (12 checks) ------------------------------------------------------

    def build_l0(self) -> Dict[str, BaseComplianceCheck]:
        m = _md(self._catalog)
        out: Dict[str, BaseComplianceCheck] = {}

        out["L0-01"] = _new(_l0.RuntimeUnitCountCheck, m["L0-01"])
        out["L0-02"] = _new(_l0.RuntimeUnitCountCheck, m["L0-02"])

        _SUB = {
            "L0-03": "models", "L0-04": "interfaces", "L0-05": "services",
            "L0-06": "lifecycle", "L0-07": "validation", "L0-08": "exceptions",
        }
        for cid, sub in _SUB.items():
            out[cid] = _new(_l0.RuntimeUnitSkeletonCheck, m[cid], sub=sub)
        # L0-09: state/ only required for units with state content.
        out["L0-09"] = _new(_l0.RuntimeUnitStateCheck, m["L0-09"])

        out["L0-10"] = _new(_l0.RuntimeInitPresenceCheck, m["L0-10"])
        out["L0-11"] = _new(_l0.RuntimeNoExtraTopLevelCheck, m["L0-11"])
        out["L0-12"] = _new(_l0.TestMirrorCheck, m["L0-12"])
        return out

    def build_l1(self) -> Dict[str, BaseComplianceCheck]:
        m = _md(self._catalog)
        out: Dict[str, BaseComplianceCheck] = {}
        for cid, symbols in _L1_SYMBOLS.items():
            out[cid] = _new(_src.SourceSymbolPresenceCheck, m[cid],
                            symbols=symbols)
        return out

    def build_l2(self) -> Dict[str, BaseComplianceCheck]:
        raise NotImplementedError("batch L2 arrives in P1-008 Batch 3")

    def build_l3(self) -> Dict[str, BaseComplianceCheck]:
        raise NotImplementedError("batch L3 arrives in P1-008 Batch 4")

    def build_l4(self) -> Dict[str, BaseComplianceCheck]:
        raise NotImplementedError("batch L4 arrives in P1-008 Batch 5")
