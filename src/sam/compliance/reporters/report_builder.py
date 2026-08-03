"""Report builder — constructs ComplianceReport objects."""

from __future__ import annotations

from typing import List

from ..models.report import ComplianceReport, LevelSummary, CategorySummary
from ..models.verdict import ComplianceVerdict
from ..models.evidence import ComplianceEvidence
from ..models.finding import ComplianceFinding


class ReportBuilder:
    """Builds ComplianceReport objects from session data."""

    @staticmethod
    def build(
        session_id: str,
        runtime_identity: str,
        timestamp: str,
        baseline_ref: str,
        suite_version: str,
        verdict: ComplianceVerdict,
        level_summaries: dict,
        category_summaries: dict,
        findings: List[ComplianceFinding],
        evidence: List[ComplianceEvidence],
        total_checks: int,
        total_executed: int,
        total_passed: int,
        total_failed: int,
        total_skipped: int,
        duration_seconds: float,
    ) -> ComplianceReport:
        """Build a ComplianceReport from all session data."""
        return ComplianceReport(
            session_id=session_id,
            runtime_identity=runtime_identity,
            timestamp=timestamp,
            baseline_ref=baseline_ref,
            suite_version=suite_version,
            verdict=verdict,
            level_summaries=dict(level_summaries),
            category_summaries=dict(category_summaries),
            findings=list(findings),
            evidence=list(evidence),
            total_checks=total_checks,
            total_executed=total_executed,
            total_passed=total_passed,
            total_failed=total_failed,
            total_skipped=total_skipped,
            duration_seconds=duration_seconds,
        )
