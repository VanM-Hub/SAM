"""Session state enumeration for compliance lifecycle per P1-001 §7."""

from enum import Enum


class SessionState(Enum):
    """Compliance session lifecycle states per P1-001 §7.1."""

    INITIATED = "INITIATED"
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    ANALYSIS = "ANALYSIS"
    PRELIMINARY_VERDICT = "PRELIMINARY_VERDICT"
    REVIEW = "REVIEW"
    FINAL_VERDICT = "FINAL_VERDICT"
    ARCHIVED = "ARCHIVED"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, value: str):
        for ss in cls:
            if ss.value == value:
                return ss
        raise ValueError("Unknown session state: %s" % value)

    @classmethod
    def terminal_states(cls):
        return {cls.ARCHIVED}

    @classmethod
    def immutable_states(cls):
        return {cls.FINAL_VERDICT, cls.ARCHIVED}

    @classmethod
    def active_states(cls):
        return {s for s in cls if s not in cls.immutable_states() and s != cls.INITIATED}
