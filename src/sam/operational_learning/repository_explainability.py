"""Repository Explainability - WP-08 (MISSION-4.3 / IP-4.3-001).

Menjelaskan asal-usul dan hubungan setiap Experience yang tersimpan.
Evidence chain lengkap, hubungan antar Experience dapat ditelusuri,
explainability dapat diaudit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .experience_model import Experience


@dataclass(frozen=True)
class RepositoryTrace:
    """Trace asal-usul sebuah experience."""

    experience_id: str
    source: str
    created_at: str
    classification: str
    evidence_chain: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "experience_id": self.experience_id,
            "source": self.source,
            "created_at": self.created_at,
            "classification": self.classification,
            "evidence_chain": [list(c) for c in self.evidence_chain],
        }


@dataclass(frozen=True)
class ContextExplanation:
    """Penjelasan konteks experience."""

    experience_id: str
    environment: str
    operator: str
    targets: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "experience_id": self.experience_id,
            "environment": self.environment,
            "operator": self.operator,
            "targets": list(self.targets),
        }


@dataclass(frozen=True)
class ExperienceExplanation:
    """Penjelasan penuh sebuah experience."""

    experience_id: str
    summary: str
    trace: RepositoryTrace
    context: ContextExplanation

    def as_dict(self) -> dict:
        return {
            "experience_id": self.experience_id,
            "summary": self.summary,
            "trace": self.trace.as_dict(),
            "context": self.context.as_dict(),
        }


class RepositoryExplainer:
    """Menjelaskan experience (read-only)."""

    def explain(self, experience: Experience) -> ExperienceExplanation:
        trace = RepositoryTrace(
            experience_id=experience.experience_id,
            source=experience.context.environment,
            created_at=experience.created_at,
            classification=experience.classification,
            evidence_chain=tuple(
                (e.evidence_id, e.source_id) for e in experience.evidence
            ),
        )
        ctx = ContextExplanation(
            experience_id=experience.experience_id,
            environment=experience.context.environment,
            operator=experience.context.operator,
            targets=experience.context.target_ids,
        )
        return ExperienceExplanation(
            experience_id=experience.experience_id,
            summary=experience.summary,
            trace=trace,
            context=ctx,
        )


class ExplainabilityAPI:
    """Public read-only API explainability."""

    def __init__(self, explainer: RepositoryExplainer) -> None:
        self._explainer = explainer

    def explain(self, experience: Experience) -> Dict[str, Any]:
        return self._explainer.explain(experience).as_dict()

    def explain_many(
        self, experiences: Tuple[Experience, ...]
    ) -> Tuple[Dict[str, Any], ...]:
        return tuple(self.explain(e) for e in experiences)
