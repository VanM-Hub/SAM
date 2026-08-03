"""Session identity model per P1-001 §7.2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..models.verdict import VerdictGrade


@dataclass(frozen=True)
class SessionIdentity:
    """Immutable compliance session identity.

    Per P1-001 §7.2 Session Identity specification.
    """

    session_id: str
    """UUID-formatted unique session identifier."""

    target_runtime: str
    """Path or identity of the Runtime being checked."""

    baseline_commit: str
    """Commit hash of the baseline Reference Runtime."""

    compliance_suite_version: str = "P1-001"
    """Version of the compliance suite definition."""

    initiated_at: str = ""
    """ISO-format timestamp of session initiation."""

    completed_at: str = ""
    """ISO-format timestamp of session completion."""

    verdict: Optional[VerdictGrade] = None
    """Final verdict grade, if session is complete."""

    evidence_count: int = 0
    """Total evidence items collected."""

    finding_count: int = 0
    """Total findings produced."""

    def is_complete(self) -> bool:
        return self.verdict is not None

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "target_runtime": self.target_runtime,
            "baseline_commit": self.baseline_commit,
            "compliance_suite_version": self.compliance_suite_version,
            "initiated_at": self.initiated_at,
            "completed_at": self.completed_at,
            "verdict": self.verdict.value if self.verdict else None,
            "evidence_count": self.evidence_count,
            "finding_count": self.finding_count,
        }
