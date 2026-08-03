"""Verdict grade enumeration and ComplianceVerdict model per P1-001 §6."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VerdictGrade(Enum):
    """Verdict grades per P1-001 §6.1."""

    A_CERTIFIED = "A"
    B_MINOR_FINDING = "B"
    C_MAJOR_FINDING = "C"
    D_NOT_COMPLIANT = "D"

    @property
    def label(self) -> str:
        mapping = {
            "A": "Certified",
            "B": "Minor Finding",
            "C": "Major Finding",
            "D": "Not Compliant",
        }
        return mapping[self.value]

    @classmethod
    def from_str(cls, value: str):
        for grade in cls:
            if grade.value == value:
                return grade
        raise ValueError("Unknown verdict grade: %s" % value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ComplianceVerdict:
    """Immutable compliance verdict model.

    Calculated from findings per P1-001 §6.2 algorithm.
    """

    grade: VerdictGrade
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    info_count: int = 0

    @property
    def total_findings(self) -> int:
        return self.critical_count + self.major_count + self.minor_count + self.info_count

    @property
    def label(self) -> str:
        return self.grade.label

    def is_certified(self) -> bool:
        return self.grade == VerdictGrade.A_CERTIFIED

    @classmethod
    def compute(cls, critical_count: int, major_count: int,
                minor_count: int, info_count: int = 0) -> ComplianceVerdict:
        """Compute verdict from finding counts per P1-001 §6.2.

        IF any CRITICAL   → D
        ELSE IF any MAJOR  → C
        ELSE IF >3 MINOR   → B
        ELSE               → A
        """
        if critical_count > 0:
            grade = VerdictGrade.D_NOT_COMPLIANT
        elif major_count > 0:
            grade = VerdictGrade.C_MAJOR_FINDING
        elif minor_count > 3:
            grade = VerdictGrade.B_MINOR_FINDING
        else:
            grade = VerdictGrade.A_CERTIFIED

        return cls(
            grade=grade,
            critical_count=critical_count,
            major_count=major_count,
            minor_count=minor_count,
            info_count=info_count,
        )

    def to_dict(self):
        return {
            "grade": self.grade.value,
            "label": self.label,
            "critical_count": self.critical_count,
            "major_count": self.major_count,
            "minor_count": self.minor_count,
            "info_count": self.info_count,
            "total_findings": self.total_findings,
        }
