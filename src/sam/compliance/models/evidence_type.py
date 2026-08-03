"""Evidence type enumeration per P1-001 §4.1."""

from enum import Enum


class EvidenceType(Enum):
    """Evidence types for compliance checks."""

    FILE_EXISTS = "FILE_EXISTS"
    FILE_ABSENT = "FILE_ABSENT"
    SOURCE_CONTAINS = "SOURCE_CONTAINS"
    SOURCE_ABSENT = "SOURCE_ABSENT"
    TEST_PASS = "TEST_PASS"
    TEST_COUNT = "TEST_COUNT"
    IMPORT_LEGAL = "IMPORT_LEGAL"
    IMPORT_ILLEGAL = "IMPORT_ILLEGAL"
    LIFECYCLE_VALID = "LIFECYCLE_VALID"
    TRACE_CHAIN = "TRACE_CHAIN"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_str(cls, value: str):
        for et in cls:
            if et.value == value:
                return et
        raise ValueError("Unknown evidence type: %s" % value)
