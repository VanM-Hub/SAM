"""Additive CLI integration for P1-008 concrete checkers.

P1-006 defines SessionRunner; the STOP condition forbids modifying it.
This module provides an additive subclass, BaselineBackedSessionRunner,
that wires the 99 concrete BaseComplianceCheck checkers (assembled by
the Builder) into the engine by overriding only _to_compliance_check.

The override returns an engine ComplianceCheck whose execution_fn runs
the concrete checker against the P1-007 baseline snapshot + repo root,
mapping the CheckResult to ComplianceEvidence. Nothing in P1-006 is
edited; the base SessionRunner.run path is reused unchanged.
"""

from __future__ import annotations

from typing import Dict, Optional

from sam.compliance.catalog.catalog import ComplianceCheckCatalog
from sam.compliance.catalog.models import CheckMetadata
from sam.compliance.cli import session_runner as _sr
from sam.compliance.cli.session_runner import SessionRunner
from sam.compliance.models.check_model import ComplianceCheck
from sam.compliance.models.evidence import ComplianceEvidence
from sam.compliance.models.evidence_type import EvidenceType
from sam.compliance.models.category import ComplianceCategory
from sam.compliance.models.level import ComplianceLevel
from sam.compliance.models.severity import Severity
from sam.compliance.checks.base.check_context import CheckContext
from sam.compliance.checks.base.check_result import CheckResult
from ._shared import BaselineResolver
from .builder import Builder

# Reuse P1-006 mapping tables (read-only, no modification).
_LEVEL_MAP = _sr._LEVEL_MAP
_CATEGORY_MAP = _sr._CATEGORY_MAP
_EVIDENCE_MAP = _sr._EVIDENCE_MAP
_SEVERITY_MAP = _sr._SEVERITY_MAP


def _repo_root() -> str:
    """Return the SAM repo root (deterministic, from package location)."""
    from sam.compliance.baseline.loader import BaselineLoader
    return str(BaselineLoader()._root)


class BaselineBackedSessionRunner(SessionRunner):
    """SessionRunner that executes the 99 concrete P1-008 checkers.

    Reuses the base class's run()/list_checks()/filtering lifecycle but
    replaces placeholder check construction with real baseline-backed
    checkers. The P1-007 baseline snapshot is loaded once and shared
    across all checkers for determinism and performance.
    """

    def __init__(
        self,
        manifest=None,
        catalog: Optional[ComplianceCheckCatalog] = None,
    ) -> None:
        catalog = catalog if catalog is not None else ComplianceCheckCatalog()
        if manifest is None:
            from sam.compliance.manifest.loader import ManifestLoader
            manifest = ManifestLoader(catalog).load()
        super().__init__(manifest, catalog)
        self._builder = Builder(catalog)
        self._concrete: Dict[str, object] = self._builder.build_all()
        self._root = _repo_root()
        self._snapshot = None
        self._resolver = BaselineResolver()

    def _load_baseline(self):
        """Load (and cache) the P1-007 baseline snapshot."""
        if self._snapshot is None:
            from sam.compliance.baseline.loader import BaselineLoader
            self._snapshot = BaselineLoader().load()
        return self._snapshot

    def _to_compliance_check(self, metadata: CheckMetadata):
        """Build an engine ComplianceCheck backed by a concrete checker.

        execution_fn takes no args (engine contract) and returns
        ComplianceEvidence by running the concrete checker against the
        shared baseline context. Falls back to the placeholder when the
        check id has no concrete checker.
        """
        concrete = self._concrete.get(metadata.check_id)
        if concrete is None:
            return super()._to_compliance_check(metadata)

        root = self._root
        snapshot = self._load_baseline()
        evidence_type = _EVIDENCE_MAP[metadata.evidence_type.value]

        def _exec():
            ctx = CheckContext(
                target_path=root,
                options={"baseline": snapshot, "baseline_root": root},
                check_id=metadata.check_id,
            )
            try:
                result = concrete.execute(ctx)
            except Exception as exc:  # defensive: never crash the run
                return ComplianceEvidence.deviating(
                    check_id=metadata.check_id,
                    evidence_type=evidence_type,
                    value=str(exc),
                    source_path="",
                    timestamp=_now(),
                    baseline_ref=concrete.baseline_ref,
                    details="Execution error: %s" % str(exc),
                )
            return _map_result(metadata, concrete, evidence_type,
                               result, source_path="")

        return ComplianceCheck(
            check_id=metadata.check_id,
            level=_LEVEL_MAP[metadata.level.value],
            category=_CATEGORY_MAP[metadata.category.value],
            description=metadata.description,
            evidence_type=evidence_type,
            severity=_SEVERITY_MAP[metadata.severity.value],
            baseline_ref=metadata.baseline_ref,
            recommendation=metadata.recommendation,
            execution_fn=_exec,
        )


def _map_result(metadata, concrete, evidence_type, result,
                source_path="") -> ComplianceEvidence:
    """Map a concrete CheckResult to engine ComplianceEvidence."""
    ts = _now()
    if result.passed:
        return ComplianceEvidence.conforming(
            check_id=metadata.check_id,
            evidence_type=evidence_type,
            value=True,
            source_path=source_path,
            timestamp=ts,
            baseline_ref=concrete.baseline_ref,
            details=result.details,
        )
    return ComplianceEvidence.deviating(
        check_id=metadata.check_id,
        evidence_type=evidence_type,
        value=result.details,
        source_path=source_path,
        timestamp=ts,
        baseline_ref=concrete.baseline_ref,
        details=result.details,
    )


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
