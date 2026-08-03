"""Test CheckEvidenceBuilder — CheckResult to ComplianceEvidence conversion."""

from __future__ import annotations

from sam.compliance.checks.base import CheckResult
from sam.compliance.checks.evidence import CheckEvidenceBuilder
from sam.compliance.models.evidence import ComplianceEvidence
from sam.compliance.models.evidence_type import EvidenceType


class TestEvidenceBuilder:
    """Tests for CheckEvidenceBuilder."""

    def test_build_conforming(self):
        result = CheckResult.success(details="all good", evidence={"key": "val"})
        ev = CheckEvidenceBuilder.build(
            check_id="T-001",
            evidence_type=EvidenceType.FILE_EXISTS,
            result=result,
            source_path="src/file.py",
            baseline_ref="P1-001",
        )
        assert isinstance(ev, ComplianceEvidence)
        assert ev.is_passed()
        assert ev.check_id == "T-001"
        assert ev.source_path == "src/file.py"
        assert ev.baseline_ref == "P1-001"
        assert "all good" in ev.details

    def test_build_deviating(self):
        result = CheckResult.failure(details="something broke", evidence={"err": 123})
        ev = CheckEvidenceBuilder.build(
            check_id="T-002",
            evidence_type=EvidenceType.FILE_EXISTS,
            result=result,
        )
        assert ev.is_failed()
        assert "something broke" in ev.details
        assert ev.value == {"err": 123}

    def test_build_deterministic(self):
        """Same input → same output structure."""
        result1 = CheckResult.success(details="ok")
        result2 = CheckResult.success(details="ok")

        ev1 = CheckEvidenceBuilder.build("T-001", EvidenceType.FILE_EXISTS, result1)
        ev2 = CheckEvidenceBuilder.build("T-001", EvidenceType.FILE_EXISTS, result2)

        assert ev1.status == ev2.status
        assert ev1.details == ev2.details
        # Timestamps differ, so check fields individually
        assert ev1.check_id == ev2.check_id
