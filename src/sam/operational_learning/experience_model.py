"""Experience Model - WP-03 (MISSION-4.3 / IP-4.3-001).

Model domain standar untuk seluruh pengalaman operasional. Immutable,
evidence terhubung, context tersimpan.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class ExperienceStatus:
    RECORDED = "recorded"
    VERIFIED = "verified"
    VALIDATED = "validated"
    ARCHIVED = "archived"

    _VALID = (RECORDED, VERIFIED, VALIDATED, ARCHIVED)

    @classmethod
    def valid(cls, status: str) -> bool:
        return status in cls._VALID


class ExperienceClassification:
    INVESTIGATION = "investigation"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    RECOMMENDATION = "recommendation"
    FEEDBACK = "feedback"

    _VALID = (
        INVESTIGATION,
        EXECUTION,
        VERIFICATION,
        RECOMMENDATION,
        FEEDBACK,
    )

    @classmethod
    def valid(cls, classification: str) -> bool:
        return classification in cls._VALID


@dataclass(frozen=True)
class ExperienceEvidenceRef:
    """Referensi evidence yang terhubung dengan experience."""

    evidence_id: str
    source_type: str = ""
    source_id: str = ""

    def as_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
        }


@dataclass(frozen=True)
class ExperienceContext:
    """Konteks pengalaman operasional."""

    environment: str = ""
    operator: str = ""
    target_ids: Tuple[str, ...] = field(default_factory=tuple)
    start_time: str = ""
    end_time: str = ""

    def as_dict(self) -> dict:
        return {
            "environment": self.environment,
            "operator": self.operator,
            "target_ids": list(self.target_ids),
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


@dataclass(frozen=True)
class ExperienceMetadata:
    """Metadata experience."""

    created_at: str = field(default_factory=_now_utc)
    created_by: str = "operational_learning"
    source: str = ""
    classification: str = ""
    version: int = 1

    def as_dict(self) -> dict:
        return {
            "created_at": self.created_at,
            "created_by": self.created_by,
            "source": self.source,
            "classification": self.classification,
            "version": self.version,
        }


@dataclass(frozen=True)
class Experience:
    """Pengalaman operasional (immutable)."""

    experience_id: str
    summary: str
    details: Tuple[str, ...] = field(default_factory=tuple)
    status: str = ExperienceStatus.RECORDED
    classification: str = ""
    evidence: Tuple[ExperienceEvidenceRef, ...] = field(default_factory=tuple)
    context: ExperienceContext = field(default_factory=ExperienceContext)
    outcome: str = ""
    tags: Tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    @classmethod
    def create(
        cls,
        *,
        summary: str,
        classification: str,
        evidence: Tuple[ExperienceEvidenceRef, ...] = (),
        context: Optional[ExperienceContext] = None,
        outcome: str = "",
        details: Tuple[str, ...] = (),
        tags: Tuple[str, ...] = (),
        experience_id: Optional[str] = None,
    ) -> "Experience":
        if not ExperienceClassification.valid(classification):
            raise ValueError(f"Invalid classification: {classification!r}")
        return cls(
            experience_id=experience_id or uuid.uuid4().hex,
            summary=summary,
            details=details,
            status=ExperienceStatus.RECORDED,
            classification=classification,
            evidence=evidence,
            context=context or ExperienceContext(),
            outcome=outcome,
            tags=tags,
        )

    def as_dict(self) -> dict:
        return {
            "experience_id": self.experience_id,
            "summary": self.summary,
            "details": list(self.details),
            "status": self.status,
            "classification": self.classification,
            "evidence": [e.as_dict() for e in self.evidence],
            "context": self.context.as_dict(),
            "outcome": self.outcome,
            "tags": list(self.tags),
            "created_at": self.created_at,
        }
