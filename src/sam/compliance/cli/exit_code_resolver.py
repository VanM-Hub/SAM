"""ExitCodeResolver — maps verdict grade to a process exit code.

Per P1-006:
    0 = Verdict A (Certified)
    1 = Verdict B (Minor finding)
    2 = Verdict C (Major finding)
    3 = Verdict D (Not compliant)

Fully deterministic — no state, pure function on grade.
"""

from __future__ import annotations

from ..models.verdict import VerdictGrade


class ExitCodeResolver:
    """Resolves a VerdictGrade to an exit code."""

    # Verdict grade -> exit code
    EXIT_CODES = {
        VerdictGrade.A_CERTIFIED: 0,
        VerdictGrade.B_MINOR_FINDING: 1,
        VerdictGrade.C_MAJOR_FINDING: 2,
        VerdictGrade.D_NOT_COMPLIANT: 3,
    }

    def resolve(self, grade: VerdictGrade) -> int:
        """Return the exit code for a verdict grade.

        Returns 0 for unknown grades (safe default / certified-like).
        """
        return self.EXIT_CODES.get(grade, 0)

    def resolve_str(self, grade_value: str) -> int:
        """Resolve from a grade string ('A'..'D')."""
        try:
            grade = VerdictGrade.from_str(grade_value)
        except ValueError:
            return 0
        return self.resolve(grade)

    @classmethod
    def grade_for_exit_code(cls, code: int) -> str:
        """Inverse: map an exit code back to a grade label."""
        for grade, exit_code in cls.EXIT_CODES.items():
            if exit_code == code:
                return grade.value
        return "?"
