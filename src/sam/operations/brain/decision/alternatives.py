"""
OP-304 — Alternative Generator

Menghasilkan alternatif keputusan berdasarkan evidence.
Minimal 4 alternatif: Do Nothing, Recommended, Conservative, Aggressive.
Semua evidence-based. Tidak invent data.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class DecisionAlternative:
    name: str  # do_nothing, recommended, conservative, aggressive
    label: str
    description: str
    evidence_basis: Tuple[str, ...]  # Evidence IDs yang mendukung
    estimated_impact: str  # low, medium, high, critical
    estimated_confidence: float  # 0.0 - 1.0
    risk_level: str  # low, medium, high, critical
    pros: Tuple[str, ...] = ()
    cons: Tuple[str, ...] = ()
    requires_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "evidence_basis": list(self.evidence_basis),
            "estimated_impact": self.estimated_impact,
            "estimated_confidence": self.estimated_confidence,
            "risk_level": self.risk_level,
            "pros": list(self.pros),
            "cons": list(self.cons),
            "requires_approval": self.requires_approval,
        }


class AlternativeGenerator:
    """
    Menghasilkan minimal 4 alternatif keputusan.
    Tidak invent data — semua berdasarkan evidence yang diberikan.
    """

    MIN_ALTERNATIVES = 4
    ALTERNATIVE_NAMES = ("do_nothing", "recommended", "conservative", "aggressive")

    def generate(
        self,
        context: Any,
        evaluation: Any,
        evidence_ids: Optional[Tuple[str, ...]] = None,
        evidence_summaries: Optional[Dict[str, str]] = None,
    ) -> Tuple[DecisionAlternative, ...]:
        eids = evidence_ids or ()
        e_summaries = evidence_summaries or {}

        return (
            self._build_do_nothing(eids, e_summaries, context, evaluation),
            self._build_recommended(eids, e_summaries, context, evaluation),
            self._build_conservative(eids, e_summaries, context, evaluation),
            self._build_aggressive(eids, e_summaries, context, evaluation),
        )

    def _build_do_nothing(
        self,
        eids: Tuple[str, ...],
        summaries: Dict[str, str],
        context: Any,
        evaluation: Any,
    ) -> DecisionAlternative:
        risk = self._infer_risk(evaluation, "do_nothing")
        impact = self._infer_impact(evaluation, "do_nothing")
        # risk is a label; map to numeric risk score for confidence calculation
        risk_score = self._risk_label_to_score(risk)
        confidence = round(max(0.0, 1.0 - risk_score), 2)

        return DecisionAlternative(
            name="do_nothing",
            label="Do Nothing",
            description="No action taken. Continue monitoring current state.",
            evidence_basis=eids[:2] if len(eids) >= 2 else eids,
            estimated_impact=impact,
            estimated_confidence=round(confidence, 2),
            risk_level=risk,
            pros=("Zero execution risk", "Fully reversible", "No resource cost"),
            cons=("No progress on issue", "Problem may persist or worsen"),
            requires_approval=False,
        )

    def _build_recommended(
        self,
        eids: Tuple[str, ...],
        summaries: Dict[str, str],
        context: Any,
        evaluation: Any,
    ) -> DecisionAlternative:
        risk = self._infer_risk(evaluation, "recommended")
        impact = self._infer_impact(evaluation, "recommended")
        confidence = self._get_confidence(evaluation)

        return DecisionAlternative(
            name="recommended",
            label="Recommended",
            description="Balanced action based on evidence and evaluation.",
            evidence_basis=eids,
            estimated_impact=impact,
            estimated_confidence=round(confidence, 2),
            risk_level=risk,
            pros=("Evidence-backed", "Balanced risk/reward", "Highest confidence"),
            cons=("May still require approval", "Resources needed"),
            requires_approval=risk in ("high", "critical") or impact in ("high", "critical"),
        )

    def _build_conservative(
        self,
        eids: Tuple[str, ...],
        summaries: Dict[str, str],
        context: Any,
        evaluation: Any,
    ) -> DecisionAlternative:
        risk = "low"
        impact = "low"
        confidence = 0.7

        return DecisionAlternative(
            name="conservative",
            label="Conservative",
            description="Minimal, low-risk action. Prioritizes stability over speed.",
            evidence_basis=eids[:2] if len(eids) >= 2 else eids,
            estimated_impact=impact,
            estimated_confidence=confidence,
            risk_level=risk,
            pros=("Lowest risk", "Minimal disruption", "Easy to reverse"),
            cons=("Slow progress", "May not fully resolve issue"),
            requires_approval=False,
        )

    def _build_aggressive(
        self,
        eids: Tuple[str, ...],
        summaries: Dict[str, str],
        context: Any,
        evaluation: Any,
    ) -> DecisionAlternative:
        risk = self._infer_risk(evaluation, "aggressive")
        impact = self._infer_impact(evaluation, "aggressive")
        conf = self._get_confidence(evaluation)
        confidence = max(0.3, round(conf - 0.2, 2))

        return DecisionAlternative(
            name="aggressive",
            label="Aggressive",
            description="Maximum intervention. Fastest possible resolution.",
            evidence_basis=eids,
            estimated_impact=impact,
            estimated_confidence=round(confidence, 2),
            risk_level=risk,
            pros=("Fastest resolution", "Comprehensive fix", "Maximum impact"),
            cons=("Highest risk", "May be irreversible", "Requires approval"),
            requires_approval=True,
        )

    def _infer_risk(self, evaluation: Any, alt_name: str) -> str:
        if evaluation is None:
            return "medium"
        if not hasattr(evaluation, "risk_level"):
            return "medium"
        base_risk = getattr(evaluation, "risk_level", "medium")
        mapping = {
            "do_nothing": {"low": "low", "medium": "low", "high": "medium", "critical": "medium"},
            "recommended": {"low": "low", "medium": "medium", "high": "high", "critical": "critical"},
            "conservative": {"low": "low", "medium": "low", "high": "medium", "critical": "medium"},
            "aggressive": {"low": "medium", "medium": "high", "high": "critical", "critical": "critical"},
        }
        result = mapping.get(alt_name, {}).get(base_risk, "medium")
        # end _infer_risk
        return result

    def _risk_label_to_score(self, label: str) -> float:
        mapping = {"low": 0.1, "medium": 0.4, "high": 0.7, "critical": 0.9}
        return mapping.get(label, 0.5)

    def _infer_impact(self, evaluation: Any, alt_name: str) -> str:
        if evaluation is None:
            return "medium"
        if not hasattr(evaluation, "operational_impact"):
            return "medium"
        base = getattr(evaluation, "operational_impact", "medium")
        mapping = {
            "do_nothing": {"low": "low", "medium": "low", "high": "medium", "critical": "medium"},
            "recommended": {"low": "low", "medium": "medium", "high": "high", "critical": "critical"},
            "conservative": {"low": "low", "medium": "low", "high": "medium", "critical": "medium"},
            "aggressive": {"low": "medium", "medium": "high", "high": "critical", "critical": "critical"},
        }
        return mapping.get(alt_name, {}).get(base, "medium")

    def _get_confidence(self, evaluation: Any) -> float:
        if evaluation is None:
            return 0.5
        return getattr(evaluation, "confidence", 0.5)
