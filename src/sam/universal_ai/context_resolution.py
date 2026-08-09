"""Context Resolution - WP-35 (MISSION-5.1 / IP-5.1-004).

Engine untuk menentukan context yang relevan terhadap reasoning request.
Deterministik dan explainable. Jika context tidak cukup, nyatakan missing
information daripada mengarang context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .evidence_context import EvidenceContextProvider
from .experience_context import ExperienceContextProvider, ExperienceEntry
from .operational_context import OperationalContext
from .reasoning_context_model import ReasoningContext


@dataclass(frozen=True)
class MissingInfo:
    """Informasi yang tidak cukup tersedia."""

    field_name: str
    reason: str

    def as_dict(self) -> dict:
        return {"field_name": self.field_name, "reason": self.reason}


@dataclass(frozen=True)
class ResolvedReasoningContext:
    """Context yang sudah di-resolve untuk reasoning."""

    base: ReasoningContext
    operational: OperationalContext
    evidence_used: Tuple[str, ...] = field(default_factory=tuple)
    experiences: Tuple[ExperienceEntry, ...] = field(default_factory=tuple)
    missing: Tuple[MissingInfo, ...] = field(default_factory=tuple)

    @property
    def complete(self) -> bool:
        return not self.missing

    def as_dict(self) -> dict:
        return {
            "base": self.base.as_dict(),
            "operational": self.operational.as_dict(),
            "evidence_used": list(self.evidence_used),
            "experiences": [e.as_dict() for e in self.experiences],
            "missing": [m.as_dict() for m in self.missing],
            "complete": self.complete,
        }


class ContextResolutionEngine:
    """Menentukan context relevan dan mendeteksi informasi yang hilang."""

    def __init__(
        self,
        evidence: EvidenceContextProvider,
        experience: ExperienceContextProvider,
    ) -> None:
        self._evidence = evidence
        self._experience = experience

    def resolve(
        self, context: ReasoningContext, operational: OperationalContext
    ) -> ResolvedReasoningContext:
        evidence_used = self._evidence.filter_provenance(context.evidence_refs)

        experiences: Tuple[ExperienceEntry, ...] = ()
        if context.experience_refs:
            experiences = self._experience.retrieve(context.experience_refs)
        elif context.objective:
            experiences = self._experience.discover_similar("investigation")

        missing: list = []
        if not context.objective:
            missing.append(MissingInfo("objective", "objective is required"))
        if context.evidence_refs and not evidence_used:
            missing.append(MissingInfo("evidence", "no evidence with valid source reference"))

        return ResolvedReasoningContext(
            base=context,
            operational=operational,
            evidence_used=evidence_used,
            experiences=experiences,
            missing=tuple(missing),
        )
