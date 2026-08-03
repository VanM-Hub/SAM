"""Compliance runner — executes registered checks and collects evidence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..models.check_model import ComplianceCheck
from ..models.evidence import ComplianceEvidence
from ..models.finding import ComplianceFinding
from ..models.level import ComplianceLevel
from ..models.category import ComplianceCategory
from ..models.severity import Severity
from ..models.classification import FindingClassification
from ..models.evidence_type import EvidenceType
from ..exceptions.compliance_errors import CheckExecutionError
from ..registry.check_registry import ComplianceRegistry


class ComplianceRunner:
    """Runs compliance checks and collects evidence.

    Executes registered checks and transforms evidence into findings.
    Deterministic: same checks + same execution functions produce same results.
    """

    def __init__(self, registry: ComplianceRegistry) -> None:
        if not isinstance(registry, ComplianceRegistry):
            raise TypeError("registry must be a ComplianceRegistry instance")
        self._registry = registry
        self._evidence: List[ComplianceEvidence] = []
        self._findings: List[ComplianceFinding] = []

    @property
    def evidence(self) -> List[ComplianceEvidence]:
        """Return all collected evidence, ordered by collection time."""
        return list(self._evidence)

    @property
    def findings(self) -> List[ComplianceFinding]:
        """Return all findings, ordered by production time."""
        return list(self._findings)

    def run_check(self, check: ComplianceCheck) -> ComplianceEvidence:
        """Execute a single check and return evidence.

        If the check has no execution function, returns INCONCLUSIVE evidence.
        If execution fails, returns FAILED evidence with error details.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        if not check.is_executable():
            evidence = ComplianceEvidence.collected(
                check_id=check.check_id,
                evidence_type=check.evidence_type,
                value=None,
                source_path="",
                timestamp=timestamp,
                baseline_ref=check.baseline_ref,
                details="Check has no execution function (placeholder)",
            )
            self._evidence.append(evidence)
            return evidence

        try:
            result = check.execute()
            evidence = self._normalize_evidence(check, result, timestamp)
            self._evidence.append(evidence)
            return evidence
        except Exception as e:
            evidence = ComplianceEvidence.deviating(
                check_id=check.check_id,
                evidence_type=check.evidence_type,
                value=str(e),
                source_path="",
                timestamp=timestamp,
                baseline_ref=check.baseline_ref,
                details="Execution error: %s" % str(e),
            )
            self._evidence.append(evidence)
            return evidence

    def run_all(self) -> List[ComplianceEvidence]:
        """Run all registered checks and collect all evidence.

        Checks are executed in deterministic sorted-by-ID order.
        """
        self._evidence = []
        checks = self._registry.list_all()

        for check in checks:
            self.run_check(check)

        return list(self._evidence)

    def run_by_level(self, level: ComplianceLevel) -> List[ComplianceEvidence]:
        """Run all checks at a specific level."""
        checks = self._registry.list_by_level(level)
        evidence_list = []

        for check in checks:
            ev = self.run_check(check)
            evidence_list.append(ev)

        return evidence_list

    def run_by_category(self, category: ComplianceCategory) -> List[ComplianceEvidence]:
        """Run all checks for a specific category."""
        checks = self._registry.list_by_category(category)
        evidence_list = []

        for check in checks:
            ev = self.run_check(check)
            evidence_list.append(ev)

        return evidence_list

    def analyze(self) -> List[ComplianceFinding]:
        """Analyze collected evidence and produce findings.

        Per P1-001 §5.1:
        - PASSED evidence → CONFORMITY finding
        - FAILED evidence → DEVIATION finding
        - COLLECTED/inconclusive evidence → INCONCLUSIVE finding
        - Checks with no execution fn → NOT_APPLICABLE
        """
        self._findings = []
        processed_ids = set()

        for evidence in self._evidence:
            check = self._registry.find(evidence.check_id)
            processed_ids.add(evidence.check_id)

            default_severity = check.severity if check else Severity.INFO

            if evidence.is_passed():
                finding = ComplianceFinding.conforming(
                    check_id=evidence.check_id,
                    severity=Severity.INFO,
                    evidence=evidence,
                    baseline_ref=evidence.baseline_ref,
                )
            elif evidence.is_failed():
                finding = ComplianceFinding.deviating(
                    check_id=evidence.check_id,
                    severity=default_severity,
                    description="Check %s failed" % evidence.check_id,
                    evidence=evidence,
                    recommendation=check.recommendation if check else "",
                    baseline_ref=evidence.baseline_ref,
                )
            else:
                # COLLECTED status → check had no execution function
                finding = ComplianceFinding.inconclusive(
                    check_id=evidence.check_id,
                    severity=Severity.INFO,
                    description="Check %s: no execution function (placeholder)" % evidence.check_id,
                    baseline_ref=evidence.baseline_ref,
                )

            self._findings.append(finding)

        # Add NOT_APPLICABLE findings for checks that weren't executed at all
        all_checks = self._registry.list_all()
        for check in all_checks:
            if check.check_id not in processed_ids:
                finding = ComplianceFinding.not_applicable(
                    check_id=check.check_id,
                    severity=Severity.INFO,
                    description="Check %s was not executed" % check.check_id,
                    baseline_ref=check.baseline_ref,
                )
                self._findings.append(finding)

        # Sort findings deterministically by check_id
        self._findings.sort(key=lambda f: f.check_id)
        return list(self._findings)

    def clear_evidence(self) -> None:
        """Clear all collected evidence and findings."""
        self._evidence = []
        self._findings = []

    @staticmethod
    def _normalize_evidence(
        check: ComplianceCheck, result, timestamp: str
    ) -> ComplianceEvidence:
        """Normalize a raw check result into a ComplianceEvidence object.

        Accepts:
        - ComplianceEvidence: returned directly
        - bool: True → PASSED, False → FAILED
        - None: INCONCLUSIVE
        - str: treated as details
        """
        if isinstance(result, ComplianceEvidence):
            return result

        if isinstance(result, bool):
            if result:
                return ComplianceEvidence.conforming(
                    check_id=check.check_id,
                    evidence_type=check.evidence_type,
                    value=result,
                    timestamp=timestamp,
                    baseline_ref=check.baseline_ref,
                )
            else:
                return ComplianceEvidence.deviating(
                    check_id=check.check_id,
                    evidence_type=check.evidence_type,
                    value=result,
                    timestamp=timestamp,
                    baseline_ref=check.baseline_ref,
                )

        # Non-bool, non-evidence result: treat as inconclusive with value
        return ComplianceEvidence.collected(
            check_id=check.check_id,
            evidence_type=check.evidence_type,
            value=result,
            timestamp=timestamp,
            baseline_ref=check.baseline_ref,
            details="Unexpected result type: %s" % type(result).__name__,
        )
