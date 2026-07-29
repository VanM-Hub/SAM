"""
OP-302 — Decision Context Builder

Menggabungkan berbagai DTO source menjadi DecisionContext.
Immutable output. Tidak memanggil penyedia eksternal.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ── DTO Sources ───────────────────────────────────────────────────

@dataclass(frozen=True)
class ObservationSource:
    summary: str = ""
    count: int = 0
    latest_key_events: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"summary": self.summary, "count": self.count, "latest_key_events": list(self.latest_key_events)}


@dataclass(frozen=True)
class FindingsSource:
    summary: str = ""
    total_findings: int = 0
    critical_findings: int = 0
    top_findings: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "total_findings": self.total_findings,
            "critical_findings": self.critical_findings,
            "top_findings": list(self.top_findings),
        }


@dataclass(frozen=True)
class RecommendationSource:
    summary: str = ""
    confidence: float = 0.0
    alternatives: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"summary": self.summary, "confidence": self.confidence, "alternatives": list(self.alternatives)}


@dataclass(frozen=True)
class MissionSource:
    id: str = ""
    status: str = ""
    progress: float = 0.0
    phase: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "status": self.status, "progress": self.progress, "phase": self.phase}


@dataclass(frozen=True)
class TimelineSource:
    summary: str = ""
    recent_entries: Tuple[str, ...] = ()
    total_entries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"summary": self.summary, "recent_entries": list(self.recent_entries), "total_entries": self.total_entries}


@dataclass(frozen=True)
class TrustSource:
    level: float = 0.0
    total_decisions: int = 0
    success_rate: float = 0.0
    last_trust_event: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "total_decisions": self.total_decisions, "success_rate": self.success_rate, "last_trust_event": self.last_trust_event}


@dataclass(frozen=True)
class HealthSource:
    overall: str = "unknown"
    healthy_components: int = 0
    total_components: int = 0
    alerts: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"overall": self.overall, "healthy_components": self.healthy_components, "total_components": self.total_components, "alerts": list(self.alerts)}


@dataclass(frozen=True)
class ActiveApprovalSource:
    count: int = 0
    pending_ids: Tuple[str, ...] = ()
    pending_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"count": self.count, "pending_ids": list(self.pending_ids), "pending_summary": self.pending_summary}


@dataclass(frozen=True)
class SessionSource:
    id: str = ""
    state: str = ""
    total_reasonings: int = 0
    context_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "state": self.state, "total_reasonings": self.total_reasonings, "context_summary": self.context_summary}


# ── Output ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DecisionContext:
    operator_question: str
    observation: ObservationSource
    findings: FindingsSource
    recommendation: RecommendationSource
    mission: MissionSource
    timeline: TimelineSource
    trust: TrustSource
    health: HealthSource
    active_approvals: ActiveApprovalSource
    current_session: SessionSource
    evidence_ids: Tuple[str, ...] = ()
    token_estimate: int = 0
    assembled_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operator_question": self.operator_question,
            "observation": self.observation.to_dict(),
            "findings": self.findings.to_dict(),
            "recommendation": self.recommendation.to_dict(),
            "mission": self.mission.to_dict(),
            "timeline": self.timeline.to_dict(),
            "trust": self.trust.to_dict(),
            "health": self.health.to_dict(),
            "active_approvals": self.active_approvals.to_dict(),
            "current_session": self.current_session.to_dict(),
            "evidence_ids": list(self.evidence_ids),
            "token_estimate": self.token_estimate,
            "assembled_at": self.assembled_at,
        }


class DecisionContextBuilder:
    """
    Membangun DecisionContext dari berbagai DTO source.

    Output immutable. Tidak memanggil penyedia layanan.
    """

    MAX_SUMMARY_LENGTH = 2000

    def build(
        self,
        operator_question: str,
        observation: Optional[ObservationSource] = None,
        findings: Optional[FindingsSource] = None,
        recommendation: Optional[RecommendationSource] = None,
        mission: Optional[MissionSource] = None,
        timeline: Optional[TimelineSource] = None,
        trust: Optional[TrustSource] = None,
        health: Optional[HealthSource] = None,
        active_approvals: Optional[ActiveApprovalSource] = None,
        current_session: Optional[SessionSource] = None,
        evidence_ids: Optional[Tuple[str, ...]] = None,
    ) -> DecisionContext:
        ctx = DecisionContext(
            operator_question=self._truncate(operator_question, 500),
            observation=observation or ObservationSource(),
            findings=findings or FindingsSource(),
            recommendation=recommendation or RecommendationSource(),
            mission=mission or MissionSource(),
            timeline=timeline or TimelineSource(),
            trust=trust or TrustSource(),
            health=health or HealthSource(),
            active_approvals=active_approvals or ActiveApprovalSource(),
            current_session=current_session or SessionSource(),
            evidence_ids=tuple(sorted(set(evidence_ids or ()))),
            token_estimate=self._estimate_tokens(
                operator_question, observation, findings, recommendation,
                mission, timeline, trust, health, active_approvals, current_session,
            ),
            assembled_at=datetime.now().isoformat(timespec="seconds"),
        )
        return ctx

    def _truncate(self, text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."

    def _estimate_tokens(self, *sources: Any) -> int:
        total = 0
        for s in sources:
            if s is not None:
                text = str(s.to_dict() if hasattr(s, "to_dict") else s)
                total += len(text) // 4  # rough estimate: 4 chars ≈ 1 token
        return total + 10  # buffer
