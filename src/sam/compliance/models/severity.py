"""Severity enumeration for compliance findings."""

from enum import Enum


class Severity(Enum):
    """Finding severity levels per P1-001 §5.2."""

    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFO = "INFO"

    def __repr__(self) -> str:
        return "Severity.%s" % self.name

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, value: str):
        for sev in cls:
            if sev.value == value:
                return sev
        raise ValueError("Unknown severity: %s" % value)
