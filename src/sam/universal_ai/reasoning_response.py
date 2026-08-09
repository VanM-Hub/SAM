"""Reasoning Response - WP-37 (MISSION-5.1 / IP-5.1-004).

Model universal untuk hasil reasoning. Bisa memuat conclusion, assessment,
recommendation, confidence, evidence refs, provider/model, limitations, missing
info. Tidak mengandung authority grant.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ReasoningResponse:
    """Hasil reasoning universal."""

    request_id: str
    conclusion: str
    confidence: float = 0.0
    assessment: str = ""
    recommendation: str = ""
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)
    context_refs: Tuple[str, ...] = field(default_factory=tuple)
    provider_id: str = ""
    model_id: str = ""
    limitations: Tuple[str, ...] = field(default_factory=tuple)
    missing_information: Tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    @property
    def has_provenance(self) -> bool:
        return bool(self.evidence_refs or self.context_refs or self.provider_id)

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "assessment": self.assessment,
            "recommendation": self.recommendation,
            "evidence_refs": list(self.evidence_refs),
            "context_refs": list(self.context_refs),
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "limitations": list(self.limitations),
            "missing_information": list(self.missing_information),
            "has_provenance": self.has_provenance,
            "created_at": self.created_at,
        }
