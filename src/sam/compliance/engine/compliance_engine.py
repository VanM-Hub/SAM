"""Compliance engine — orchestrates compliance sessions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..models.check_model import ComplianceCheck
from ..models.evidence import ComplianceEvidence
from ..models.finding import ComplianceFinding
from ..models.report import ComplianceReport, LevelSummary, CategorySummary
from ..models.verdict import ComplianceVerdict, VerdictGrade
from ..models.level import ComplianceLevel
from ..models.category import ComplianceCategory
from ..models.severity import Severity
from ..models.classification import FindingClassification
from ..models.session_identity import SessionIdentity
from ..models.session_state import SessionState
from ..exceptions.compliance_errors import (
    InvalidSessionStateError,
    SessionImmutableError,
    VerdictComputationError,
)
from ..registry.check_registry import ComplianceRegistry
from .runner import ComplianceRunner


class ComplianceEngine:
    """Main compliance engine.

    Orchestrates a compliance session:
    1. INITIATED → validates target
    2. EVIDENCE_COLLECTION → runs checks via runner
    3. ANALYSIS → classifies evidence into findings
    4. PRELIMINARY_VERDICT → computes verdict
    5. FINAL_VERDICT → finalizes
    6. ARCHIVED → session immutable

    Deterministic: same registry + same target produce same results.
    Independent of target runtime (ADR-006 compliance).
    """

    def __init__(self, registry: ComplianceRegistry) -> None:
        if not isinstance(registry, ComplianceRegistry):
            raise TypeError("registry must be a ComplianceRegistry instance")
        self._registry = registry
        self._runner = ComplianceRunner(registry)
        self._state = SessionState.INITIATED
        self._identity: Optional[SessionIdentity] = None
        self._report: Optional[ComplianceReport] = None

    @property
    def state(self) -> SessionState:
        """Get current session state."""
        return self._state

    @property
    def registry(self) -> ComplianceRegistry:
        """Get the compliance check registry."""
        return self._registry

    @property
    def identity(self) -> Optional[SessionIdentity]:
        """Get current session identity, if any."""
        return self._identity

    def get_state(self) -> SessionState:
        """Get current session state (alias for .state)."""
        return self._state

    def get_identity(self) -> Optional[SessionIdentity]:
        """Get current session identity (alias for .identity)."""
        return self._identity

    def run_session(
        self,
        target_runtime: str,
        baseline_commit: str,
        suite_version: str = "P1-001",
    ) -> ComplianceReport:
        """Run a complete compliance session against a target Runtime.

        Progresses through all session states automatically.
        Returns the final ComplianceReport.

        Raises SessionImmutableError if engine is already in a terminal state.
        """
        if self._state in SessionState.immutable_states():
            raise SessionImmutableError(
                self._identity.session_id if self._identity else "unknown"
            )

        session_id = str(uuid.uuid4())
        initiated_at = datetime.now(timezone.utc).isoformat()

        # STATE: INITIATED
        self._identity = SessionIdentity(
            session_id=session_id,
            target_runtime=target_runtime,
            baseline_commit=baseline_commit,
            compliance_suite_version=suite_version,
            initiated_at=initiated_at,
        )
        self._state = SessionState.INITIATED

        # STATE: EVIDENCE_COLLECTION
        self._state = SessionState.EVIDENCE_COLLECTION
        all_evidence = self._run_evidence_collection()

        # STATE: ANALYSIS
        self._state = SessionState.ANALYSIS
        all_findings = self._run_analysis()

        # STATE: PRELIMINARY_VERDICT
        self._state = SessionState.PRELIMINARY_VERDICT
        verdict = self._compute_verdict(all_findings)

        # STATE: FINAL_VERDICT
        self._state = SessionState.FINAL_VERDICT
        completed_at = datetime.now(timezone.utc).isoformat()

        # Build report
        self._report = self._build_report(
            session_id=session_id,
            target_runtime=target_runtime,
            baseline_commit=baseline_commit,
            suite_version=suite_version,
            initiated_at=initiated_at,
            completed_at=completed_at,
            evidence=all_evidence,
            findings=all_findings,
            verdict=verdict,
        )

        # Update identity with final values
        self._identity = SessionIdentity(
            session_id=session_id,
            target_runtime=target_runtime,
            baseline_commit=baseline_commit,
            compliance_suite_version=suite_version,
            initiated_at=initiated_at,
            completed_at=completed_at,
            verdict=verdict.grade,
            evidence_count=len(all_evidence),
            finding_count=len(all_findings),
        )

        # STATE: ARCHIVED
        self._state = SessionState.ARCHIVED

        return self._report

    def _run_evidence_collection(self) -> List[ComplianceEvidence]:
        """Run all registered checks and collect evidence.

        Deterministic: checks executed in sorted-by-ID order.
        """
        return self._runner.run_all()

    def _run_analysis(self) -> List[ComplianceFinding]:
        """Analyze all collected evidence into findings."""
        return self._runner.analyze()

    def _compute_verdict(self, findings: List[ComplianceFinding]) -> ComplianceVerdict:
        """Compute verdict from findings per P1-001 §6.2 algorithm.

        IF any CRITICAL   → D
        ELSE IF any MAJOR  → C
        ELSE IF >3 MINOR   → B
        ELSE               → A
        """
        critical_count = sum(1 for f in findings if f.is_deviating() and f.is_critical())
        major_count = sum(1 for f in findings if f.is_deviating() and f.is_major())
        minor_count = sum(1 for f in findings if f.is_deviating() and f.is_minor())
        info_count = sum(1 for f in findings if f.is_deviating() and f.severity == Severity.INFO)

        return ComplianceVerdict.compute(
            critical_count=critical_count,
            major_count=major_count,
            minor_count=minor_count,
            info_count=info_count,
        )

    def _build_report(
        self,
        session_id: str,
        target_runtime: str,
        baseline_commit: str,
        suite_version: str,
        initiated_at: str,
        completed_at: str,
        evidence: List[ComplianceEvidence],
        findings: List[ComplianceFinding],
        verdict: ComplianceVerdict,
    ) -> ComplianceReport:
        """Build a ComplianceReport from session data."""
        # Parse timestamps for duration calculation
        try:
            start = datetime.fromisoformat(initiated_at)
            end = datetime.fromisoformat(completed_at)
            duration = (end - start).total_seconds()
        except (ValueError, TypeError):
            duration = 0.0

        # Build level summaries
        level_summaries = self._build_level_summaries(evidence)

        # Build category summaries
        category_summaries = self._build_category_summaries(findings)

        # Count totals
        total_checks = self._registry.count()
        total_passed = sum(1 for e in evidence if e.is_passed())
        total_failed = sum(1 for e in evidence if e.is_failed())
        total_skipped = sum(1 for e in evidence if not e.is_passed() and not e.is_failed())
        total_executed = len(evidence)

        return ComplianceReport(
            session_id=session_id,
            runtime_identity=target_runtime,
            timestamp=completed_at,
            baseline_ref=baseline_commit,
            suite_version=suite_version,
            verdict=verdict,
            level_summaries=level_summaries,
            category_summaries=category_summaries,
            findings=list(findings),
            evidence=list(evidence),
            total_checks=total_checks,
            total_executed=total_executed,
            total_passed=total_passed,
            total_failed=total_failed,
            total_skipped=total_skipped,
            duration_seconds=duration,
        )

    def _build_level_summaries(
        self, evidence: List[ComplianceEvidence]
    ) -> Dict[str, LevelSummary]:
        """Build per-level summaries from evidence."""
        summaries: Dict[str, LevelSummary] = {}

        for lvl in ComplianceLevel.all_levels():
            lvl_checks = self._registry.list_by_level(lvl)
            check_ids = {c.check_id for c in lvl_checks}
            lvl_evidence = [e for e in evidence if e.check_id in check_ids]

            total = len(lvl_checks)
            passed = sum(1 for e in lvl_evidence if e.is_passed())
            failed = sum(1 for e in lvl_evidence if e.is_failed())
            skipped = total - passed - failed

            summaries[lvl.value] = LevelSummary(
                level=lvl,
                total_checks=total,
                passed=passed,
                failed=failed,
                skipped=skipped,
            )

        return summaries

    def _build_category_summaries(
        self, findings: List[ComplianceFinding]
    ) -> Dict[str, CategorySummary]:
        """Build per-category summaries from findings."""
        summaries: Dict[str, CategorySummary] = {}

        for cat in ComplianceCategory.all_categories():
            summaries[cat.value] = CategorySummary(category=cat)

        for f in findings:
            if f.is_deviating():
                check = self._registry.find(f.check_id)
                cat_key = check.category.value if check else "Testing"

                if cat_key not in summaries:
                    summaries[cat_key] = CategorySummary(
                        category=ComplianceCategory.from_str(cat_key)
                    )

                summary = summaries[cat_key]
                if f.is_critical():
                    summary = CategorySummary(
                        category=summary.category,
                        critical_count=summary.critical_count + 1,
                        major_count=summary.major_count,
                        minor_count=summary.minor_count,
                        info_count=summary.info_count,
                    )
                elif f.is_major():
                    summary = CategorySummary(
                        category=summary.category,
                        critical_count=summary.critical_count,
                        major_count=summary.major_count + 1,
                        minor_count=summary.minor_count,
                        info_count=summary.info_count,
                    )
                elif f.is_minor():
                    summary = CategorySummary(
                        category=summary.category,
                        critical_count=summary.critical_count,
                        major_count=summary.major_count,
                        minor_count=summary.minor_count + 1,
                        info_count=summary.info_count,
                    )
                else:
                    summary = CategorySummary(
                        category=summary.category,
                        critical_count=summary.critical_count,
                        major_count=summary.major_count,
                        minor_count=summary.minor_count,
                        info_count=summary.info_count + 1,
                    )
                summaries[cat_key] = summary

        return summaries

    def reset(self) -> None:
        """Reset the engine to INITIATED state for a new session."""
        self._state = SessionState.INITIATED
        self._identity = None
        self._report = None
        self._runner.clear_evidence()

    def is_terminal(self) -> bool:
        """Return True if the engine is in a terminal state."""
        return self._state in SessionState.immutable_states()
