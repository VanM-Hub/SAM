"""Reasoning Context Model - WP-31 (MISSION-5.1 / IP-5.1-004).

Model context untuk reasoning pipeline. Immutable setelah reasoning request
dibuat. Merepresentasikan identity, request, objective, state, evidence,
experience, constraints, provenance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ReasoningContext:
    """Context lengkap untuk satu reasoning request (immutable)."""

    request_id: str
    objective: str = ""
    conversation_id: str = ""
    operational_state: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    governance_state: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    citizen_state: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)
    experience_refs: Tuple[str, ...] = field(default_factory=tuple)
    constraints: Tuple[str, ...] = field(default_factory=tuple)
    provenance: Tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    @property
    def has_provenance(self) -> bool:
        return bool(self.provenance) or bool(self.evidence_refs) or bool(self.experience_refs)

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "objective": self.objective,
            "conversation_id": self.conversation_id,
            "operational_state": dict(self.operational_state),
            "governance_state": dict(self.governance_state),
            "citizen_state": dict(self.citizen_state),
            "evidence_refs": list(self.evidence_refs),
            "experience_refs": list(self.experience_refs),
            "constraints": list(self.constraints),
            "provenance": list(self.provenance),
            "has_provenance": self.has_provenance,
            "created_at": self.created_at,
        }
