"""
OP-306 — Approval Preparation

Mempersiapkan ApprovalRequest dari DecisionPackage.
Belum submit — hanya prepare.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class ApprovalRequestDTO:
    package_id: str
    title: str
    description: str
    alternative_name: str
    risk_level: str
    impact: str
    confidence: float
    evidence_count: int
    evidence_ids: Tuple[str, ...]
    recommendation: str
    requires_approval: bool
    prepared_at: str
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "title": self.title,
            "description": self.description,
            "alternative_name": self.alternative_name,
            "risk_level": self.risk_level,
            "impact": self.impact,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "evidence_ids": list(self.evidence_ids),
            "recommendation": self.recommendation,
            "requires_approval": self.requires_approval,
            "prepared_at": self.prepared_at,
            "reason": self.reason,
        }


class ApprovalRequestBuilder:
    """
    Membangun ApprovalRequestDTO dari DecisionPackage.
    Belum submit — hanya mempersiapkan data approval.
    """

    def build(self, package: Any) -> ApprovalRequestDTO:
        if package is None:
            raise ValueError("Cannot build approval request from None package")

        alternatives = getattr(package, "alternatives", ())
        selected_alt = getattr(package, "selected_alternative", "")
        selected = next(
            (a for a in alternatives if getattr(a, "name", "") == selected_alt),
            None,
        )

        alt_name = getattr(selected, "label", selected_alt) if selected else selected_alt
        risk = getattr(selected, "risk_level", getattr(package, "risk_summary", "medium")) if selected else getattr(package, "risk_summary", "medium")
        impact = getattr(selected, "estimated_impact", getattr(package, "estimated_impact", "medium")) if selected else getattr(package, "estimated_impact", "medium")
        confidence = getattr(package, "estimated_confidence", 0.0)

        # Collect evidence IDs from alternatives
        evidence_ids: List[str] = []
        for alt in alternatives:
            eids = getattr(alt, "evidence_basis", ())
            for eid in eids:
                if eid and eid not in evidence_ids:
                    evidence_ids.append(eid)

        reason = self._build_reason(risk, impact, confidence, selected_alt)

        return ApprovalRequestDTO(
            package_id=getattr(package, "package_id", ""),
            title=f"Approval: {alt_name}",
            description=getattr(package, "summary", "")[:200],
            alternative_name=alt_name,
            risk_level=self._normalize_label(risk),
            impact=self._normalize_label(impact),
            confidence=confidence,
            evidence_count=len(evidence_ids),
            evidence_ids=tuple(evidence_ids),
            recommendation=getattr(package, "recommendation", "")[:500],
            requires_approval=getattr(package, "requires_approval", False),
            prepared_at=datetime.now().isoformat(timespec="seconds"),
            reason=reason,
        )

    def _build_reason(self, risk: str, impact: str, confidence: float, alt: str) -> str:
        parts = []
        risk_label = self._normalize_label(risk)
        impact_label = self._normalize_label(impact)

        if risk_label in ("high", "critical"):
            parts.append(f"Risk level is {risk_label}")
        if impact_label in ("high", "critical"):
            parts.append(f"Impact is {impact_label}")
        if alt == "aggressive":
            parts.append("Aggressive alternative selected")
        if confidence < 0.5:
            parts.append(f"Low confidence ({confidence:.0%})")
        return "; ".join(parts) if parts else "Standard approval request"

    def _normalize_label(self, raw: str) -> str:
        raw_lower = raw.lower()
        if raw_lower in ("low", "medium", "high", "critical", "immediate", "irreversible", "fully_reversible", "reversible", "hard_to_reverse"):
            return raw_lower
        return raw_lower
