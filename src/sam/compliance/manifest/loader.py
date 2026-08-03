"""ManifestLoader — builds a ComplianceManifest from the catalog.

Loads the complete manifest: every catalog check (P1-004) becomes
exactly one ManifestEntry with deterministic default execution
configuration. The loader is the single place that maps catalog
metadata into execution entries.

Dependencies between checks are execution-order constraints. They are
NOT auto-derived from catalog traceability links: catalog traceability
documents symmetric relationships between checks (chains), while
manifest dependencies are directed execution prerequisites.
Auto-deriving from traceability would introduce legitimate cycles
(e.g. L0-01 <-> L0-02). Dependencies are therefore declared in the
manifest (via overrides or a persisted manifest), keeping the
execution graph acyclic by construction.
"""

from typing import List, Optional

from ..catalog.catalog import ComplianceCheckCatalog
from ..catalog.models import CheckerClass, EvidenceType
from .entry import ManifestEntry
from .manifest import ComplianceManifest

# Default mapping: catalog evidence type -> P1-003 checker class.
_EVIDENCE_TO_CHECKER = {
    EvidenceType.FILE_EXISTS: CheckerClass.FILE_EXISTS,
    EvidenceType.FILE_ABSENT: CheckerClass.FILE_ABSENT,
    EvidenceType.SOURCE_CONTAINS: CheckerClass.SOURCE_CONTAINS,
    EvidenceType.SOURCE_ABSENT: CheckerClass.SOURCE_ABSENT,
    EvidenceType.IMPORT_LEGAL: CheckerClass.IMPORT_LEGAL,
    EvidenceType.IMPORT_ILLEGAL: CheckerClass.IMPORT_ILLEGAL,
    EvidenceType.LIFECYCLE_VALID: CheckerClass.LIFECYCLE,
    EvidenceType.TRACE_CHAIN: CheckerClass.TRACEABILITY,
    EvidenceType.TEST_PASS: CheckerClass.TEST_RESULTS,
    EvidenceType.TEST_COUNT: CheckerClass.TEST_RESULTS,
}


class ManifestLoader:
    """Builds the canonical ComplianceManifest from a catalog."""

    def __init__(self, catalog: ComplianceCheckCatalog):
        """Bind loader to a catalog.

        Args:
            catalog: The P1-004 ComplianceCheckCatalog.
        """
        self._catalog = catalog

    def load(
        self,
        overrides: Optional[dict] = None,
    ) -> ComplianceManifest:
        """Build the full manifest.

        Args:
            overrides: Optional dict of {check_id: {field: value}} to
                       customize specific entries (e.g.
                       {'L2-02': {'enabled': False}}).

        Returns:
            A ComplianceManifest containing all 99 catalog checks.
        """
        overrides = overrides or {}
        entries: List[ManifestEntry] = []

        for check in self._catalog.list_all():
            entry = self._build_entry(check.check_id)
            ovr = overrides.get(check.check_id)
            if ovr:
                entry = self._apply_override(entry, ovr)
            entries.append(entry)

        # Assign deterministic execution_order = position in sorted catalog
        entries.sort(key=lambda e: e.check_id)
        for idx, entry in enumerate(entries):
            entries[idx] = ManifestEntry(
                check_id=entry.check_id,
                enabled=entry.enabled,
                execution_order=idx,
                checker_class=entry.checker_class,
                configuration=dict(entry.configuration),
                timeout=entry.timeout,
                retry_policy=entry.retry_policy,
                severity=entry.severity,
                dependencies=list(entry.dependencies),
                tags=list(entry.tags),
            )

        return ComplianceManifest(entries)

    # -- Internal -------------------------------------------------------------

    def _build_entry(self, check_id: str) -> ManifestEntry:
        """Build a single default ManifestEntry from a catalog check."""
        check = self._catalog[check_id]
        checker = _EVIDENCE_TO_CHECKER.get(
            check.evidence_type, CheckerClass.SOURCE_CONTAINS)

        # Dependencies are execution prerequisites — declared in the
        # manifest, NOT auto-derived from catalog traceability links
        # (which document symmetric chains and would create cycles).
        dependencies: List[str] = []

        return ManifestEntry(
            check_id=check.check_id,
            enabled=True,
            execution_order=0,
            checker_class=checker.value,
            configuration={},
            timeout=None,
            retry_policy="none",
            severity=check.severity,
            dependencies=dependencies,
            tags=list(check.tags),
        )

    def _apply_override(self, entry: ManifestEntry, ovr: dict) -> ManifestEntry:
        """Safely apply a partial override to an entry."""
        enabled = ovr.get("enabled", entry.enabled)
        execution_order = ovr.get("execution_order", entry.execution_order)
        checker_class = ovr.get("checker_class", entry.checker_class)
        configuration = ovr.get("configuration", dict(entry.configuration))
        timeout = ovr.get("timeout", entry.timeout)
        retry_policy = ovr.get("retry_policy", entry.retry_policy)
        dependencies = ovr.get("dependencies", list(entry.dependencies))
        tags = ovr.get("tags", list(entry.tags))
        return ManifestEntry(
            check_id=entry.check_id,
            enabled=bool(enabled),
            execution_order=int(execution_order),
            checker_class=str(checker_class),
            configuration=dict(configuration),
            timeout=timeout,
            retry_policy=str(retry_policy),
            severity=entry.severity,
            dependencies=list(dependencies),
            tags=list(tags),
        )
