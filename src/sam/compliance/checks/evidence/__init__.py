"""CheckEvidenceBuilder — converts CheckResult into ComplianceEvidence.

Bridges the framework's CheckResult with P1-002's ComplianceEvidence model.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ...models.evidence import ComplianceEvidence
from ...models.evidence_type import EvidenceType
from ..base.check_result import CheckResult


class CheckEvidenceBuilder:
    """Converts internal CheckResult to engine's ComplianceEvidence.

    Stateless utility — each method is a pure function.
    """

    @staticmethod
    def build(
        check_id: str,
        evidence_type: EvidenceType,
        result: CheckResult,
        source_path: str = "",
        baseline_ref: str = "",
    ) -> ComplianceEvidence:
        """Build a ComplianceEvidence from a CheckResult.

        Args:
            check_id: The check's identifier.
            evidence_type: Expected evidence type.
            result: The result from BaseComplianceCheck.execute().
            source_path: Path to the checked artifact (optional).
            baseline_ref: Reference to baseline document (optional).

        Returns:
            A ComplianceEvidence with appropriate status.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        if result.passed:
            return ComplianceEvidence.conforming(
                check_id=check_id,
                evidence_type=evidence_type,
                value=result.evidence,
                source_path=source_path,
                timestamp=timestamp,
                baseline_ref=baseline_ref,
                details=result.details,
            )
        else:
            return ComplianceEvidence.deviating(
                check_id=check_id,
                evidence_type=evidence_type,
                value=result.evidence,
                source_path=source_path,
                timestamp=timestamp,
                baseline_ref=baseline_ref,
                details=result.details,
            )
