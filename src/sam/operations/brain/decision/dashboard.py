"""
OP-308 — Decision Dashboard

DTO read-only untuk dashboard decision.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Dashboard Cards ───────────────────────────────────────────────

@dataclass(frozen=True)
class DecisionSummaryCard:
    total_decisions: int
    active_decisions: int
    finished_decisions: int
    failed_decisions: int
    average_score: float
    last_decision_time: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_decisions": self.total_decisions,
            "active_decisions": self.active_decisions,
            "finished_decisions": self.finished_decisions,
            "failed_decisions": self.failed_decisions,
            "average_score": self.average_score,
            "last_decision_time": self.last_decision_time,
        }


@dataclass(frozen=True)
class DecisionRiskCard:
    total_risk_items: int
    critical_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int
    top_risks: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_risk_items": self.total_risk_items,
            "critical_risks": self.critical_risks,
            "high_risks": self.high_risks,
            "medium_risks": self.medium_risks,
            "low_risks": self.low_risks,
            "top_risks": list(self.top_risks),
        }


@dataclass(frozen=True)
class AlternativeCard:
    name: str
    label: str
    estimated_impact: str
    estimated_confidence: float
    risk_level: str
    requires_approval: bool
    is_selected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "estimated_impact": self.estimated_impact,
            "estimated_confidence": self.estimated_confidence,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "is_selected": self.is_selected,
        }


@dataclass(frozen=True)
class ApprovalCard:
    requires_approval: bool
    has_request: bool
    prepared_at: str = ""
    package_id: str = ""
    selected_alternative: str = ""
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requires_approval": self.requires_approval,
            "has_request": self.has_request,
            "prepared_at": self.prepared_at,
            "package_id": self.package_id,
            "selected_alternative": self.selected_alternative,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class EvidenceCard:
    total_evidence: int
    unique_evidence: int
    average_relevance: float
    sources: Tuple[str, ...] = ()
    top_evidence_ids: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_evidence": self.total_evidence,
            "unique_evidence": self.unique_evidence,
            "average_relevance": self.average_relevance,
            "sources": list(self.sources),
            "top_evidence_ids": list(self.top_evidence_ids),
        }


# ── Main Dashboard DTO ────────────────────────────────────────────

@dataclass(frozen=True)
class DecisionDashboard:
    package_id: str
    operator_question: str
    summary: DecisionSummaryCard
    risk: DecisionRiskCard
    alternatives: Tuple[AlternativeCard, ...]
    approval: ApprovalCard
    evidence: EvidenceCard
    evaluation_score: float
    selected_alternative: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "operator_question": self.operator_question,
            "summary": self.summary.to_dict(),
            "risk": self.risk.to_dict(),
            "alternatives": [a.to_dict() for a in self.alternatives],
            "approval": self.approval.to_dict(),
            "evidence": self.evidence.to_dict(),
            "evaluation_score": self.evaluation_score,
            "selected_alternative": self.selected_alternative,
        }


# ── Read-only Service ─────────────────────────────────────────────

class DecisionDashboardService:
    """
    Membaca state decision untuk dashboard.
    Read-only. Tidak memanggil penyedia.
    """

    def __init__(self, session: Any = None, package: Any = None, approval_request: Any = None):
        self._session = session
        self._package = package
        self._approval_request = approval_request

    def get_dashboard(self) -> DecisionDashboard:
        pk = self._package
        session = self._session

        # Summary card
        total = getattr(session, "decision_count", 0) if session else 0
        history = getattr(session, "history", None) if session else None
        if history and hasattr(history, "records"):
            finished = sum(1 for r in history.records if r.state == "FINISHED")
            failed = sum(1 for r in history.records if r.state == "FAILED")
        else:
            finished = 0
            failed = 0

        summary = DecisionSummaryCard(
            total_decisions=total or 0,
            active_decisions=1 if getattr(session, "is_active", False) else 0,
            finished_decisions=finished,
            failed_decisions=failed,
            average_score=getattr(pk, "evaluation_score", 0.0) if pk else 0.0,
        )

        # Risk card
        alt_risk = self._extract_alt_risks(pk)
        risk = DecisionRiskCard(
            total_risk_items=len(alt_risk),
            critical_risks=sum(1 for r in alt_risk if r == "critical"),
            high_risks=sum(1 for r in alt_risk if r == "high"),
            medium_risks=sum(1 for r in alt_risk if r == "medium"),
            low_risks=sum(1 for r in alt_risk if r == "low"),
            top_risks=tuple(f"{r}" for r in alt_risk[:3]),
        )

        # Alternative cards
        alts = getattr(pk, "alternatives", ()) if pk else ()
        selected_name = getattr(pk, "selected_alternative", "") if pk else ""
        alt_cards = tuple(
            AlternativeCard(
                name=getattr(a, "name", ""),
                label=getattr(a, "label", getattr(a, "name", "")),
                estimated_impact=getattr(a, "estimated_impact", "medium"),
                estimated_confidence=getattr(a, "estimated_confidence", 0.5),
                risk_level=getattr(a, "risk_level", "medium"),
                requires_approval=getattr(a, "requires_approval", False),
                is_selected=getattr(a, "name", "") == selected_name,
            )
            for a in alts
        )

        # Approval card
        approval = ApprovalCard(
            requires_approval=getattr(pk, "requires_approval", False) if pk else False,
            has_request=self._approval_request is not None,
            prepared_at=getattr(self._approval_request, "prepared_at", "") if self._approval_request else "",
            package_id=getattr(pk, "package_id", "") if pk else "",
            selected_alternative=selected_name,
            reason=getattr(self._approval_request, "reason", "") if self._approval_request else "",
        )

        # Evidence card
        eids: list[str] = []
        for a in alts:
            eids.extend(getattr(a, "evidence_basis", ()))
        unique_eids = list(dict.fromkeys(eids))

        evidence = EvidenceCard(
            total_evidence=len(eids),
            unique_evidence=len(unique_eids),
            average_relevance=0.5,
            top_evidence_ids=tuple(unique_eids[:5]),
        )

        return DecisionDashboard(
            package_id=getattr(pk, "package_id", "") if pk else "",
            operator_question=getattr(pk, "operator_question", "") if pk else "",
            summary=summary,
            risk=risk,
            alternatives=alt_cards,
            approval=approval,
            evidence=evidence,
            evaluation_score=getattr(pk, "evaluation_score", 0.0) if pk else 0.0,
            selected_alternative=selected_name,
        )

    def _extract_alt_risks(self, pk: Any) -> List[str]:
        alts = getattr(pk, "alternatives", ()) if pk else ()
        risks: List[str] = []
        for a in alts:
            risks.append(getattr(a, "risk_level", "medium"))
        return risks


# ── Helper for dashboard service ──────────────────────────────────

# (Inline state query helper)
def _by_state(self, state: str) -> tuple:
    if hasattr(self, "records"):
        return tuple(r for r in self.records if r.state == state)
    return ()
