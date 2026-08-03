"""Exit code tests for the Compliance CLI (P1-006).

Maps verdict grade -> process exit code:
    0 = Verdict A (Certified)
    1 = Verdict B (Minor finding)
    2 = Verdict C (Major finding)
    3 = Verdict D (Not compliant)
"""

import pytest

from sam.compliance.models.verdict import VerdictGrade, ComplianceVerdict
from sam.compliance.cli import ExitCodeResolver


class TestExitCodeMapping:
    @pytest.mark.parametrize("grade,code", [
        (VerdictGrade.A_CERTIFIED, 0),
        (VerdictGrade.B_MINOR_FINDING, 1),
        (VerdictGrade.C_MAJOR_FINDING, 2),
        (VerdictGrade.D_NOT_COMPLIANT, 3),
    ])
    def test_mapping(self, exit_codes, grade, code):
        assert exit_codes.resolve(grade) == code

    def test_resolve_str_a(self, exit_codes):
        assert exit_codes.resolve_str("A") == 0

    def test_resolve_str_d(self, exit_codes):
        assert exit_codes.resolve_str("D") == 3

    def test_resolve_unknown_str_zero(self, exit_codes):
        assert exit_codes.resolve_str("Z") == 0

    def test_inverse_mapping(self, exit_codes):
        assert exit_codes.grade_for_exit_code(0) == "A"
        assert exit_codes.grade_for_exit_code(3) == "D"


class TestVerdictAlgorithms:
    def test_critical_gives_d(self):
        v = ComplianceVerdict.compute(critical_count=1, major_count=0, minor_count=0)
        assert v.grade == VerdictGrade.D_NOT_COMPLIANT

    def test_major_gives_c(self):
        v = ComplianceVerdict.compute(critical_count=0, major_count=1, minor_count=0)
        assert v.grade == VerdictGrade.C_MAJOR_FINDING

    def test_more_than_three_minor_gives_b(self):
        v = ComplianceVerdict.compute(critical_count=0, major_count=0, minor_count=4)
        assert v.grade == VerdictGrade.B_MINOR_FINDING

    def test_clean_gives_a(self):
        v = ComplianceVerdict.compute(critical_count=0, major_count=0, minor_count=0)
        assert v.grade == VerdictGrade.A_CERTIFIED

    def test_three_minor_still_a(self):
        v = ComplianceVerdict.compute(critical_count=0, major_count=0, minor_count=3)
        assert v.grade == VerdictGrade.A_CERTIFIED


class TestCLIExitCodes:
    def test_run_all_exit_0(self, cli):
        code = cli.execute_safe(["run"])
        assert code == 0  # A certified

    def test_run_level_exit_0(self, cli):
        assert cli.execute_safe(["run", "--level", "L0"]) == 0

    def test_list_exit_0(self, cli):
        assert cli.execute_safe(["list"]) == 0

    def test_summary_exit_0(self, cli):
        assert cli.execute_safe(["summary"]) == 0

    def test_info_known_exit_0(self, cli):
        assert cli.execute_safe(["info", "L1-C01"]) == 0

    def test_info_unknown_exit_1(self, cli):
        assert cli.execute_safe(["info", "NOPE"]) == 1

    def test_parse_error_exit_2(self, cli):
        assert cli.execute_safe(["frobnicate"]) == 2

    def test_unknown_command_execute_raises(self, cli):
        from sam.compliance.cli import CommandParseError
        with pytest.raises(CommandParseError):
            cli.execute(["frobnicate"])
