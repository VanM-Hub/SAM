"""ComplianceReport model per P1-001 §6.4."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..models.verdict import ComplianceVerdict, VerdictGrade
from ..models.finding import ComplianceFinding
from ..models.evidence import ComplianceEvidence
from ..models.level import ComplianceLevel
from ..models.category import ComplianceCategory


@dataclass(frozen=True)
class LevelSummary:
    """Summary of checks at one compliance level."""

    level: ComplianceLevel
    total_checks: int
    passed: int
    failed: int
    skipped: int

    @property
    def is_pass(self) -> bool:
        return self.failed == 0


@dataclass(frozen=True)
class CategorySummary:
    """Summary of findings for one category."""

    category: ComplianceCategory
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    info_count: int = 0

    @property
    def total_findings(self) -> int:
        return self.critical_count + self.major_count + self.minor_count + self.info_count


@dataclass(frozen=True)
class ComplianceReport:
    """Immutable compliance report model.

    Produced after a complete compliance session.
    Per P1-001 §6.4 Report Format.
    """

    session_id: str
    """Unique session identifier."""

    runtime_identity: str
    """Identity/path of the Runtime being checked."""

    timestamp: str
    """ISO-format timestamp of report generation."""

    baseline_ref: str
    """Baseline commit hash reference."""

    suite_version: str
    """Version of the compliance suite (P1-001)."""

    verdict: ComplianceVerdict
    """Overall verdict."""

    level_summaries: Dict[str, LevelSummary] = field(default_factory=dict)
    """Summaries per compliance level, keyed by level value (e.g. 'L0')."""

    category_summaries: Dict[str, CategorySummary] = field(default_factory=dict)
    """Summaries per category, keyed by category value."""

    findings: List[ComplianceFinding] = field(default_factory=list)
    """All findings from this session."""

    evidence: List[ComplianceEvidence] = field(default_factory=list)
    """All evidence collected in this session."""

    total_checks: int = 0
    total_executed: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    duration_seconds: float = 0.0

    @property
    def verdict_label(self) -> str:
        return self.verdict.label

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @property
    def total_evidence(self) -> int:
        return len(self.evidence)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "runtime_identity": self.runtime_identity,
            "timestamp": self.timestamp,
            "baseline_ref": self.baseline_ref,
            "suite_version": self.suite_version,
            "verdict": self.verdict.to_dict(),
            "total_checks": self.total_checks,
            "total_executed": self.total_executed,
            "total_passed": self.total_passed,
            "total_failed": self.total_failed,
            "total_skipped": self.total_skipped,
            "duration_seconds": self.duration_seconds,
        }
