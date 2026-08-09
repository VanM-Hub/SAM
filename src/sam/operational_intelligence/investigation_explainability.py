"""Investigation Explainability - WP-08 (MISSION-4.2 / IP-4.2-001).

Menjelaskan seluruh proses investigasi beserta evidence yang digunakan.
Seluruh hasil investigasi memiliki penjelasan, evidence chain lengkap,
source attribution tersedia, penjelasan dapat diaudit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .evidence_collection import EvidenceModel
from .investigation_model import Investigation
from .investigation_timeline import InvestigationTimeline


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class SourceAttribution:
    """Atribusi sumber evidence."""

    evidence_id: str
    source_type: str
    source_id: str
    category: str
    collected_at: str

    def as_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "category": self.category,
            "collected_at": self.collected_at,
        }


@dataclass(frozen=True)
class EvidenceChain:
    """Rantai evidence (lengkap, dapat diaudit)."""

    investigation_id: str
    attributions: Tuple[SourceAttribution, ...] = field(default_factory=tuple)
    chain_hash: str = ""

    @property
    def length(self) -> int:
        return len(self.attributions)

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "length": self.length,
            "attributions": [a.as_dict() for a in self.attributions],
            "chain_hash": self.chain_hash,
        }


@dataclass(frozen=True)
class TimelineExplanation:
    """Penjelasan timeline investigasi."""

    investigation_id: str
    summary: str
    event_types: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "summary": self.summary,
            "event_types": list(self.event_types),
        }


@dataclass(frozen=True)
class ObservationSummary:
    """Ringkasan hasil observasi dalam investigasi."""

    investigation_id: str
    observations: int = 0
    critical_findings: Tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "observations": self.observations,
            "critical_findings": list(self.critical_findings),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class InvestigationExplanation:
    """Penjelasan penuh sebuah investigasi (auditable)."""

    investigation_id: str
    generated_at: str
    purpose: str
    evidence_chain: EvidenceChain
    timeline: TimelineExplanation
    observation_summary: ObservationSummary
    notes: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "generated_at": self.generated_at,
            "purpose": self.purpose,
            "evidence_chain": self.evidence_chain.as_dict(),
            "timeline": self.timeline.as_dict(),
            "observation_summary": self.observation_summary.as_dict(),
            "notes": list(self.notes),
        }


class InvestigationExplainer:
    """Menjelaskan investigasi berdasarkan evidence & timeline."""

    def explain(
        self,
        investigation: Investigation,
        evidences: Tuple[EvidenceModel, ...],
        timeline: Optional[InvestigationTimeline],
    ) -> InvestigationExplanation:
        chain = self._build_chain(investigation.investigation_id, evidences)
        purpose = (
            investigation.scope.reason
            if investigation.scope
            else investigation.metadata.purpose
        )
        timeline_expl = self._explain_timeline(
            investigation.investigation_id, timeline
        )
        obs_summary = self._summarize_observations(
            investigation.investigation_id, evidences
        )
        return InvestigationExplanation(
            investigation_id=investigation.investigation_id,
            generated_at=_now_utc(),
            purpose=purpose,
            evidence_chain=chain,
            timeline=timeline_expl,
            observation_summary=obs_summary,
        )

    @staticmethod
    def _build_chain(
        investigation_id: str, evidences: Tuple[EvidenceModel, ...]
    ) -> EvidenceChain:
        attributions = tuple(
            SourceAttribution(
                evidence_id=e.evidence_id,
                source_type=e.source.source_type,
                source_id=e.source.source_id,
                category=e.category,
                collected_at=e.collected_at,
            )
            for e in evidences
        )
        import hashlib

        h = hashlib.sha256()
        for a in attributions:
            h.update(a.evidence_id.encode("utf-8"))
        return EvidenceChain(
            investigation_id=investigation_id,
            attributions=attributions,
            chain_hash=h.hexdigest(),
        )

    @staticmethod
    def _explain_timeline(
        investigation_id: str, timeline: Optional[InvestigationTimeline]
    ) -> TimelineExplanation:
        if timeline is None:
            return TimelineExplanation(
                investigation_id=investigation_id,
                summary="No timeline recorded.",
            )
        types = tuple(
            dict.fromkeys(e.event_type for e in timeline.events)
        )
        return TimelineExplanation(
            investigation_id=investigation_id,
            summary=(
                f"{len(timeline.events)} events across "
                f"{len(types)} phases."
            ),
            event_types=types,
        )

    @staticmethod
    def _summarize_observations(
        investigation_id: str, evidences: Tuple[EvidenceModel, ...]
    ) -> ObservationSummary:
        critical = tuple(
            e.evidence_id
            for e in evidences
            if e.category in ("runtime_observation", "provider_observation")
            and any(
                k == "health" and str(v) in ("critical", "degraded")
                for k, v in e.data
            )
        )
        return ObservationSummary(
            investigation_id=investigation_id,
            observations=len(evidences),
            critical_findings=critical,
            summary=(
                f"{len(evidences)} evidence collected; "
                f"{len(critical)} critical finding(s)."
            ),
        )


class ExplainabilityAPI:
    """Public read-only API penjelasan investigasi."""

    def __init__(self, explainer: InvestigationExplainer) -> None:
        self._explainer = explainer

    def explain_investigation(
        self,
        investigation: Investigation,
        evidences: Tuple[EvidenceModel, ...],
        timeline: Optional[InvestigationTimeline],
    ) -> Dict[str, Any]:
        return self._explainer.explain(
            investigation, evidences, timeline
        ).as_dict()
