"""Compliance category enumeration (10 categories)."""

from enum import Enum


class ComplianceCategory(Enum):
    """10 compliance categories per P1-001 §3."""

    FOUNDATION = "Foundation"
    SPECIFICATION = "Specification"
    ADR = "ADR"
    ARCHITECTURE = "Architecture"
    DESIGN = "Design"
    ENGINEERING = "Engineering"
    BLUEPRINT = "Blueprint"
    RUNTIME_UNITS = "Runtime Units"
    INTEGRATION = "Integration"
    TESTING = "Testing"

    @classmethod
    def from_str(cls, value: str):
        for cat in cls:
            if cat.value == value:
                return cat
        raise ValueError("Unknown category: %s" % value)

    @classmethod
    def all_categories(cls):
        return list(cls)

    @classmethod
    def count(cls) -> int:
        return len(cls)
