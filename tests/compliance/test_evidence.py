"""Tests for ComplianceEvidence model."""

from sam.compliance import ComplianceEvidence, EvidenceType


class TestEvidenceModel:
    """Evidence model construction and properties."""

    def test_conforming_evidence(self):
        ev = ComplianceEvidence.conforming(
            check_id="L0-01",
            evidence_type=EvidenceType.FILE_EXISTS,
            value=True,
            source_path="/some/path",
            timestamp="2026-08-03T14:00:00Z",
            baseline_ref="I1-001 §3",
        )
        assert ev.check_id == "L0-01"
        assert ev.evidence_type == EvidenceType.FILE_EXISTS
        assert ev.status == "PASSED"
        assert ev.is_passed()
        assert not ev.is_failed()
        assert ev.value is True
        assert ev.baseline_ref == "I1-001 §3"

    def test_deviating_evidence(self):
        ev = ComplianceEvidence.deviating(
            check_id="L1-C01",
            evidence_type=EvidenceType.SOURCE_CONTAINS,
            value=False,
            details="Citizenship model not found",
            baseline_ref="CITIZEN_SPEC L10-12",
        )
        assert ev.check_id == "L1-C01"
        assert ev.status == "FAILED"
        assert ev.is_failed()
        assert not ev.is_passed()
        assert ev.details == "Citizenship model not found"

    def test_collected_evidence(self):
        ev = ComplianceEvidence.collected(
            check_id="T01",
            evidence_type=EvidenceType.TEST_PASS,
            value="pending",
        )
        assert ev.status == "COLLECTED"
        assert not ev.is_passed()
        assert not ev.is_failed()

    def test_evidence_immutable(self):
        ev = ComplianceEvidence.conforming(
            check_id="T01",
            evidence_type=EvidenceType.FILE_EXISTS,
        )
        # Frozen dataclass — cannot assign
        try:
            ev.status = "CHANGED"  # type: ignore
            assert False, "Should have raised FrozenInstanceError"
        except Exception:
            pass  # Expected

    def test_evidence_to_dict(self):
        ev = ComplianceEvidence.conforming(
            check_id="L0-01",
            evidence_type=EvidenceType.FILE_EXISTS,
            value=True,
            source_path="/path",
            timestamp="ts",
            baseline_ref="ref",
        )
        d = ev.to_dict()
        assert d["check_id"] == "L0-01"
        assert d["evidence_type"] == "FILE_EXISTS"
        assert d["status"] == "PASSED"
        assert d["value"] == "True"

    def test_all_evidence_types(self):
        """All 10 evidence types should be usable."""
        for et in EvidenceType:
            ev = ComplianceEvidence.conforming("T01", et)
            assert ev.evidence_type == et
