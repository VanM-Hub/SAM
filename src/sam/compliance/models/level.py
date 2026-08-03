"""Compliance level enumeration (L0 through L4)."""

from enum import Enum


class ComplianceLevel(Enum):
    """Compliance levels, cumulative: each level includes all lower levels."""

    L0_STRUCTURAL = "L0"
    L1_SPECIFICATION = "L1"
    L2_ADR = "L2"
    L3_BEHAVIORAL = "L3"
    L4_SYSTEM = "L4"

    @property
    def numeric(self) -> int:
        return int(self.value[1])

    @classmethod
    def from_str(cls, value: str):
        for lvl in cls:
            if lvl.value == value:
                return lvl
        raise ValueError("Unknown level: %s" % value)

    @classmethod
    def all_levels(cls):
        return list(cls)

    @classmethod
    def count(cls) -> int:
        return len(cls)
