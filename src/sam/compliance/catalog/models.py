"""Check Metadata model for P1-004 Compliance Check Catalog.

Defines CheckMetadata — the canonical record for each of the
99 compliance checks from P1-001, and CheckAuthority enum.

Python 3.8 compatible — frozen dataclass with Dict from typing.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, Optional, List


class CheckLevel(Enum):
    """Compliance level: L0 (Structural) through L4 (System)."""
    L0_STRUCTURAL = "L0"
    L1_SPECIFICATION = "L1"
    L2_ADR = "L2"
    L3_BEHAVIORAL = "L3"
    L4_SYSTEM = "L4"


class CheckCategory(Enum):
    """Compliance category from P1-001 §3.1."""
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


class CheckSeverity(Enum):
    """Severity levels from P1-001 §5.2."""
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFO = "INFO"


class EvidenceType(Enum):
    """Evidence types from P1-001 §4.1."""
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


class CheckAuthority(Enum):
    """Authority source — what document authorises this check."""
    CONSTITUTION = "CONSTITUTION"
    GOVERNANCE = "GOVERNANCE"
    SPECIFICATION = "Specification"
    ADR = "ADR"
    ARCHITECTURE = "Architecture"
    ENGINEERING = "Engineering"
    BLUEPRINT = "Blueprint"
    CERTIFICATION = "Certification"
    SYSTEM = "System"


class CheckerClass(Enum):
    """Checker class from P1-003 framework."""
    FILE_EXISTS = "FileExistsCheck"
    FILE_ABSENT = "FileAbsentCheck"
    SOURCE_CONTAINS = "SourceContainsCheck"
    SOURCE_ABSENT = "SourceAbsentCheck"
    IMPORT_LEGAL = "ImportLegalCheck"
    IMPORT_ILLEGAL = "ImportIllegalCheck"
    LIFECYCLE = "LifecycleCheck"
    TRACEABILITY = "TraceabilityCheck"
    TEST_RESULTS = "TestResultsCheck"
    COMPOSITE = "CompositeComplianceCheck"


@dataclass(frozen=True)
class CheckMetadata:
    """Canonical metadata for a single P1-001 compliance check.

    Every field required — no defaults except expected_verdict
    (derived from check semantics).

    This is the source of truth record. All 99 checks have a
    CheckMetadata in the catalog.
    """

    # --- Identity ---
    check_id: str
    """Unique check ID (e.g., L0-01, L1-C01)."""

    name: str
    """Human-readable name for the check."""

    # --- Classification ---
    level: CheckLevel
    """Compliance level (L0-L4)."""

    category: CheckCategory
    """Compliance category (10 categories from P1-001 §3.1)."""

    severity: CheckSeverity
    """Default severity on failure."""

    # --- Authority ---
    authority: CheckAuthority
    """What document/system authorises this check."""

    # --- Evidence ---
    evidence_type: EvidenceType
    """Expected evidence type for this check."""

    # --- Implementation ---
    checker_class: CheckerClass
    """P1-003 checker class that implements this check."""

    expected_verdict: str
    """Expected verdict for a compliant runtime (usually 'PASS')."""

    # --- Traceability ---
    source_document: str
    """Primary source document that defines the requirement."""

    baseline_ref: str
    """Specific baseline section/line reference."""

    # --- Documentation ---
    description: str
    """Full description of what the check verifies."""

    traceability: List[str] = field(default_factory=list)
    """Upstream and downstream check IDs for chain tracing."""

    recommendation: str = ""
    """Recommended fix if check fails."""

    # --- Metadata ---
    tags: List[str] = field(default_factory=list)
    """Searchable tags for filtering."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to plain dict for JSON/factory compatibility."""
        return {
            "check_id": self.check_id,
            "name": self.name,
            "level": self.level.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "authority": self.authority.value,
            "evidence_type": self.evidence_type.value,
            "checker_class": self.checker_class.value,
            "expected_verdict": self.expected_verdict,
            "source_document": self.source_document,
            "baseline_ref": self.baseline_ref,
            "traceability": list(self.traceability),
            "description": self.description,
            "recommendation": self.recommendation,
            "tags": list(self.tags),
        }

    def __repr__(self) -> str:
        return "CheckMetadata(check_id=%r, level=%s, category=%s)" % (
            self.check_id, self.level.value, self.category.value)
