"""Finding classification enumeration."""

from enum import Enum


class FindingClassification(Enum):
    """Finding classifications per P1-001 §5.1."""

    CONFORMITY = "CONFORMITY"
    DEVIATION = "DEVIATION"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, value: str):
        for cls_ in cls:
            if cls_.value == value:
                return cls_
        raise ValueError("Unknown classification: %s" % value)
