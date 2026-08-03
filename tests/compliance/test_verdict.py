"""Tests for ComplianceVerdict and verdict algorithm."""

from sam.compliance import ComplianceVerdict, VerdictGrade


class TestVerdictGrades:
    """VerdictGrade enum."""

    def test_all_grades_exist(self):
        assert VerdictGrade.A_CERTIFIED.value == "A"
        assert VerdictGrade.B_MINOR_FINDING.value == "B"
        assert VerdictGrade.C_MAJOR_FINDING.value == "C"
        assert VerdictGrade.D_NOT_COMPLIANT.value == "D"

    def test_labels(self):
        assert VerdictGrade.A_CERTIFIED.label == "Certified"
        assert VerdictGrade.B_MINOR_FINDING.label == "Minor Finding"
        assert VerdictGrade.C_MAJOR_FINDING.label == "Major Finding"
        assert VerdictGrade.D_NOT_COMPLIANT.label == "Not Compliant"

    def test_from_str(self):
        assert VerdictGrade.from_str("A") == VerdictGrade.A_CERTIFIED
        assert VerdictGrade.from_str("D") == VerdictGrade.D_NOT_COMPLIANT


class TestVerdictAlgorithm:
    """Verdict computation algorithm per P1-001 §6.2."""

    def test_zero_findings_a(self):
        v = ComplianceVerdict.compute(0, 0, 0)
        assert v.grade == VerdictGrade.A_CERTIFIED
        assert v.is_certified()

    def test_critical_d(self):
        v = ComplianceVerdict.compute(1, 0, 0)
        assert v.grade == VerdictGrade.D_NOT_COMPLIANT
        assert not v.is_certified()

    def test_major_c(self):
        v = ComplianceVerdict.compute(0, 1, 0)
        assert v.grade == VerdictGrade.C_MAJOR_FINDING

    def test_major_and_minor_c(self):
        """MAJOR always dominates to C, regardless of MINOR count."""
        v = ComplianceVerdict.compute(0, 1, 10)
        assert v.grade == VerdictGrade.C_MAJOR_FINDING

    def test_minor_b(self):
        v = ComplianceVerdict.compute(0, 0, 4)
        assert v.grade == VerdictGrade.B_MINOR_FINDING

    def test_minor_few_a(self):
        v = ComplianceVerdict.compute(0, 0, 3)
        assert v.grade == VerdictGrade.A_CERTIFIED

    def test_minor_exactly_3_is_a(self):
        """3 MINOR → A (threshold is >3 for B)."""
        v = ComplianceVerdict.compute(0, 0, 3)
        assert v.grade == VerdictGrade.A_CERTIFIED

    def test_minor_4_is_b(self):
        """4 MINOR → B."""
        v = ComplianceVerdict.compute(0, 0, 4)
        assert v.grade == VerdictGrade.B_MINOR_FINDING

    def test_critical_dominates_all(self):
        v = ComplianceVerdict.compute(1, 5, 10, 20)
        assert v.grade == VerdictGrade.D_NOT_COMPLIANT

    def test_major_dominates_minor(self):
        v = ComplianceVerdict.compute(0, 1, 10, 5)
        assert v.grade == VerdictGrade.C_MAJOR_FINDING

    def test_info_doesnt_affect(self):
        v = ComplianceVerdict.compute(0, 0, 0, 100)
        assert v.grade == VerdictGrade.A_CERTIFIED


class TestVerdictTotals:
    """Verdict total calculations."""

    def test_total_findings(self):
        v = ComplianceVerdict.compute(1, 2, 3, 4)
        assert v.total_findings == 10

    def test_counts(self):
        v = ComplianceVerdict.compute(2, 3, 5, 1)
        assert v.critical_count == 2
        assert v.major_count == 3
        assert v.minor_count == 5
        assert v.info_count == 1


class TestVerdictToDict:
    """Verdict serialization."""

    def test_to_dict(self):
        v = ComplianceVerdict.compute(0, 1, 2, 3)
        d = v.to_dict()
        assert d["grade"] == "C"
        assert d["label"] == "Major Finding"
        assert d["critical_count"] == 0
        assert d["major_count"] == 1
        assert d["minor_count"] == 2
        assert d["info_count"] == 3
        assert d["total_findings"] == 6


class TestVerdictFrozen:
    """Verdict is immutable."""

    def test_verdict_is_frozen(self):
        v = ComplianceVerdict.compute(0, 0, 0)
        try:
            v.grade = VerdictGrade.D_NOT_COMPLIANT  # type: ignore
            assert False, "Should raise"
        except Exception:
            pass
