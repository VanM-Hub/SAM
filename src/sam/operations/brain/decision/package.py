"""
OP-305 — Decision Package Builder

Menggabungkan seluruh hasil menjadi DecisionPackage.
Immutable. Berisi summary, findings, evidence, alternatives, recommendation,
approval requirement, estimated impact, estimated confidence, risk summary, next steps.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class DecisionPackage:
    package_id: str
    operator_question: str
    session_id: str
    summary: str
    findings: Tuple[str, ...]
    evidence_summary: str
    alternatives: Tuple[Any, ...]  # DecisionAlternative objects
    selected_alternative: str
    recommendation: str
    requires_approval: bool
    estimated_impact: str
    estimated_confidence: float
    risk_summary: str
    evaluation_score: float
    next_steps: Tuple[str, ...]
    created_at: str
    metadata: Tuple[Tuple[str, str], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "operator_question": self.operator_question,
            "session_id": self.session_id,
            "summary": self.summary,
            "findings": list(self.findings),
            "evidence_summary": self.evidence_summary,
            "alternatives": [a.to_dict() if hasattr(a, "to_dict") else {"name": str(a)} for a in self.alternatives],
            "selected_alternative": self.selected_alternative,
            "recommendation": self.recommendation,
            "requires_approval": self.requires_approval,
            "estimated_impact": self.estimated_impact,
            "estimated_confidence": self.estimated_confidence,
            "risk_summary": self.risk_summary,
            "evaluation_score": self.evaluation_score,
            "next_steps": list(self.next_steps),
            "created_at": self.created_at,
            "metadata": list(self.metadata),
        }


class DecisionPackageBuilder:
    """
    Membangun DecisionPackage dari context, evaluation, dan alternatives.
    Output immutable.
    """

    def build(
        self,
        operator_question: str,
        session_id: str,
        context: Any,
        evaluation: Any,
        alternatives: Tuple[Any, ...],
        selected_alternative: str,
        evidence_summary: str = "",
        findings: Optional[Tuple[str, ...]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> DecisionPackage:
        alt_names = tuple(
            f"{a.name}: {a.description}" for a in alternatives if hasattr(a, "description")
        )

        # Summary
        summary = self._build_summary(context, evaluation, selected_alternative)

        # Next steps
        next_steps = self._build_next_steps(alternatives, selected_alternative, evaluation)

        # Risk summary
        risk_summary = self._build_risk_summary(evaluation)

        # Recommendation
        rec_text = self._build_recommendation(alternatives, selected_alternative, evaluation)

        # Approval requirement
        selected = next(
            (a for a in alternatives if getattr(a, "name", "") == selected_alternative),
            None,
        )
        requires_approval = getattr(selected, "requires_approval", False)

        # Impact & confidence
        impact = getattr(selected, "estimated_impact", "medium") if selected else "medium"
        confidence = getattr(evaluation, "score", 0.5) if evaluation else 0.5
        score = getattr(evaluation, "score", 0.0) if evaluation else 0.0

        pkg = DecisionPackage(
            package_id=f"dp-{datetime.now().timestamp():.0f}",
            operator_question=operator_question,
            session_id=session_id,
            summary=summary,
            findings=findings or self._extract_findings(context),
            evidence_summary=evidence_summary or self._extract_evidence_summary(context),
            alternatives=alternatives,
            selected_alternative=selected_alternative,
            recommendation=rec_text,
            requires_approval=requires_approval,
            estimated_impact=impact,
            estimated_confidence=round(confidence, 2),
            risk_summary=risk_summary,
            evaluation_score=round(score, 2),
            next_steps=next_steps,
            created_at=datetime.now().isoformat(timespec="seconds"),
            metadata=tuple(sorted((metadata or {}).items())),
        )
        return pkg

    def _build_summary(self, context: Any, evaluation: Any, selected: str) -> str:
        parts = ["Decision Package"]
        if context and hasattr(context, "operator_question"):
            parts.append(f"Question: {context.operator_question[:100]}")
        if evaluation and hasattr(evaluation, "score"):
            parts.append(f"Score: {evaluation.score}")
        parts.append(f"Selected: {selected}")
        return " | ".join(parts)

    def _build_next_steps(
        self, alternatives: Tuple[Any, ...], selected: str, evaluation: Any
    ) -> Tuple[str, ...]:
        steps = ["Review decision package", "Verify evidence and alternatives"]
        risk = getattr(evaluation, "risk_level", "medium") if evaluation else "medium"
        if risk in ("high", "critical") or selected == "aggressive":
            steps.append("Escalate for human approval")
        else:
            steps.append("Proceed with selected alternative")
            steps.append("Monitor outcome after execution")
        return tuple(steps)

    def _build_risk_summary(self, evaluation: Any) -> str:
        if evaluation is None:
            return "Risk not evaluated"
        parts = []
        if hasattr(evaluation, "risk_level"):
            parts.append(f"Risk: {evaluation.risk_level}")
        if hasattr(evaluation, "operational_impact"):
            parts.append(f"Impact: {evaluation.operational_impact}")
        if hasattr(evaluation, "reversibility"):
            parts.append(f"Reversibility: {evaluation.reversibility}")
        return " | ".join(parts) if parts else "No risk assessment available"

    def _build_recommendation(
        self, alternatives: Tuple[Any, ...], selected: str, evaluation: Any
    ) -> str:
        sel = next(
            (a for a in alternatives if getattr(a, "name", "") == selected),
            None,
        )
        if sel:
            desc = getattr(sel, "description", "")
            pros = getattr(sel, "pros", ())
            return f"{desc} Pros: {'; '.join(pros[:3])}" if pros else desc
        return f"Selected alternative: {selected}"

    def _extract_findings(self, context: Any) -> Tuple[str, ...]:
        if context and hasattr(context, "findings"):
            f = getattr(context, "findings", None)
            if f:
                return f.top_findings
        return ()

    def _extract_evidence_summary(self, context: Any) -> str:
        if context and hasattr(context, "evidence_ids"):
            ids = getattr(context, "evidence_ids", ())
            return f"Based on {len(ids)} evidence items"
        return "No evidence summary available"
