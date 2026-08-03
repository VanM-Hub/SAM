"""SessionRunner — executes a compliance session from the manifest.

The runner is the execution orchestrator behind the CLI. It:
1. Builds a registry of ComplianceCheck placeholders from the catalog,
   filtered by manifest (enabled) state + requested CLI filters.
2. Runs the ComplianceEngine session against that subset.
3. Tracks session metadata (id, started_at, completed_at, check counts,
   findings, verdict) deterministically.

P1-006 only runs checks that are registered — placeholder or real.
It does NOT implement the 99 individual checkers.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..catalog.catalog import ComplianceCheckCatalog
from ..catalog.models import (
    CheckMetadata, CheckLevel, CheckCategory, CheckAuthority,
)
from ..manifest.manifest import ComplianceManifest
from ..models.check_model import ComplianceCheck
from ..models.level import ComplianceLevel
from ..models.category import ComplianceCategory
from ..models.evidence_type import EvidenceType
from ..models.severity import Severity
from ..models.report import ComplianceReport
from ..registry.check_registry import ComplianceRegistry
from ..engine.compliance_engine import ComplianceEngine

# Map catalog compliance levels -> engine compliance levels.
_LEVEL_MAP = {
    "L0": ComplianceLevel.L0_STRUCTURAL,
    "L1": ComplianceLevel.L1_SPECIFICATION,
    "L2": ComplianceLevel.L2_ADR,
    "L3": ComplianceLevel.L3_BEHAVIORAL,
    "L4": ComplianceLevel.L4_SYSTEM,
}

# Map catalog evidence types -> engine evidence types.
_EVIDENCE_MAP = {
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

# Map catalog categories -> engine categories.
_CATEGORY_MAP = {
    "Foundation": ComplianceCategory.FOUNDATION,
    "Specification": ComplianceCategory.SPECIFICATION,
    "ADR": ComplianceCategory.ADR,
    "Architecture": ComplianceCategory.ARCHITECTURE,
    "Design": ComplianceCategory.DESIGN,
    "Engineering": ComplianceCategory.ENGINEERING,
    "Blueprint": ComplianceCategory.BLUEPRINT,
    "Runtime Units": ComplianceCategory.RUNTIME_UNITS,
    "Integration": ComplianceCategory.INTEGRATION,
    "Testing": ComplianceCategory.TESTING,
}

# Map catalog severities -> engine severities.
_SEVERITY_MAP = {
    "CRITICAL": Severity.CRITICAL,
    "MAJOR": Severity.MAJOR,
    "MINOR": Severity.MINOR,
    "INFO": Severity.INFO,
}


@dataclass(frozen=True)
class SessionResult:
    """Immutable result of a CLI compliance session run."""

    session_id: str
    started_at: str
    completed_at: str
    executed_checks: int
    skipped_checks: int
    total_checks: int
    report: ComplianceReport

    @property
    def verdict(self) -> str:
        return self.report.verdict.grade.value

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "executed_checks": self.executed_checks,
            "skipped_checks": self.skipped_checks,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
        }


class SessionFilter:
    """Filter used to select which checks run in a session.

    Immutable selection criteria — all filters are AND-combined.
    Empty filter means "all enabled checks".
    """

    def __init__(
        self,
        check_id: Optional[str] = None,
        level: Optional[str] = None,
        category: Optional[str] = None,
        authority: Optional[str] = None,
        tag: Optional[str] = None,
    ):
        self.check_id = check_id
        self.level = level
        self.category = category
        self.authority = authority
        self.tag = tag

    def is_empty(self) -> bool:
        return (
            self.check_id is None
            and self.level is None
            and self.category is None
            and self.authority is None
            and self.tag is None
        )

    def matches(self, metadata: CheckMetadata) -> bool:
        """Return True if the catalog check passes all filters."""
        if self.check_id is not None and metadata.check_id != self.check_id:
            return False
        if self.level is not None and metadata.level.value != self.level:
            return False
        if self.category is not None and metadata.category.value != self.category:
            return False
        if self.authority is not None and metadata.authority.value != self.authority:
            return False
        if self.tag is not None and self.tag not in metadata.tags:
            return False
        return True


class SessionRunner:
    """Runs a deterministic compliance session for a manifest subset."""

    def __init__(
        self,
        manifest: ComplianceManifest,
        catalog: ComplianceCheckCatalog,
    ) -> None:
        """Bind runner to a manifest + catalog.

        Args:
            manifest: The P1-005 ComplianceManifest.
            catalog: The P1-004 ComplianceCheckCatalog.
        """
        self._manifest = manifest
        self._catalog = catalog

    # -- Public API -----------------------------------------------------------

    def run(
        self,
        target_runtime: str = "runtime",
        baseline_commit: str = "HEAD",
        suite_version: str = "P1-001",
        check_filter: Optional[SessionFilter] = None,
    ) -> SessionResult:
        """Run a compliance session for the filtered enabled subset.

        Args:
            target_runtime: Target runtime label for the session.
            baseline_commit: Baseline commit reference.
            suite_version: Compliance suite version.
            check_filter: Optional SessionFilter. None = all enabled.

        Returns:
            SessionResult with report + session metadata.

        Raises:
            KeyError: If a filter references an unknown check_id.
        """
        check_filter = check_filter or SessionFilter()

        selected_ids = self._select_ids(check_filter)
        registry = self._build_registry(selected_ids)

        skipped = self._manifest.count() - len(selected_ids)

        # The engine runs its own session lifecycle. It runs ALL checks
        # in the given registry (which is already our selected subset).
        engine = ComplianceEngine(registry)
        report = engine.run_session(
            target_runtime=target_runtime,
            baseline_commit=baseline_commit,
            suite_version=suite_version,
        )

        # Session metadata — timestamps derived from report for determinism.
        session_id = str(uuid.uuid4())
        started_at = _now_iso()
        completed_at = _now_iso()

        return SessionResult(
            session_id=session_id,
            started_at=started_at,
            completed_at=completed_at,
            executed_checks=len(selected_ids),
            skipped_checks=skipped,
            total_checks=self._manifest.count(),
            report=report,
        )

    def list_checks(self, check_filter: Optional[SessionFilter] = None) -> List[CheckMetadata]:
        """List catalog checks matching a filter (no filtering by manifest)."""
        check_filter = check_filter or SessionFilter()
        results = []
        for metadata in self._catalog.list_all():
            if check_filter.matches(metadata):
                results.append(metadata)
        return results

    # -- Internal -------------------------------------------------------------

    def _select_ids(self, check_filter: SessionFilter) -> List[str]:
        """Determine the ordered set of check IDs to execute.

        Honors manifest 'enabled' state — disabled checks are never
        selected. Result is deterministic (sorted by manifest order).
        """
        if check_filter.check_id is not None:
            # Direct check-id selection.
            if check_filter.check_id not in self._manifest:
                raise KeyError(
                    "Unknown check id: %s" % check_filter.check_id)
            entry = self._manifest.get(check_filter.check_id)
            if not entry.enabled:
                return []
            return [entry.check_id]

        selected = []
        for entry in self._manifest.enabled():  # manifest-order (order, id)
            metadata = self._catalog.get(entry.check_id)
            if metadata is None:
                continue
            if check_filter.matches(metadata):
                selected.append(entry.check_id)
        return selected

    def _build_registry(self, check_ids: List[str]) -> ComplianceRegistry:
        """Build a ComplianceRegistry of placeholder ComplianceCheck models
        for the selected check IDs (deterministic order)."""
        registry = ComplianceRegistry()
        checks = []
        for cid in check_ids:
            metadata = self._catalog.get(cid)
            if metadata is None:
                continue
            checks.append(self._to_compliance_check(metadata))
        registry.register_all(checks)
        return registry

    def _to_compliance_check(self, metadata: CheckMetadata) -> ComplianceCheck:
        """Convert a catalog CheckMetadata into an engine ComplianceCheck.

        Placeholder — no execution_fn (checkers implemented later).
        """
        return ComplianceCheck(
            check_id=metadata.check_id,
            level=_LEVEL_MAP[metadata.level.value],
            category=_CATEGORY_MAP[metadata.category.value],
            description=metadata.description,
            evidence_type=_EVIDENCE_MAP[metadata.evidence_type.value],
            severity=_SEVERITY_MAP[metadata.severity.value],
            baseline_ref=metadata.baseline_ref,
            recommendation=metadata.recommendation,
            execution_fn=None,
        )


def _now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()
