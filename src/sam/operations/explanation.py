"""
Decision Explanation Engine — mengapa memilih A, bukan B.

Tidak boleh "menurut saya".
Semua explanation harus berbasis evidence.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .decision import DecisionProposal
from .scoring import ScoredAlternatives, RecommendationScore


@dataclass
class AlternativeExplanation:
    """Penjelasan untuk satu alternatif yang tidak dipilih."""
    title: str
    score: float
    not_chosen_reason: str
    evidence_gap: str = ""
    missing_data: List[str] = field(default_factory=list)

    def to_text(self) -> str:
        return "Not chosen: {title} (score {score:.0f})\n  Reason: {reason}".format(
            title=self.title, score=self.score, reason=self.not_chosen_reason[:60],
        )


@dataclass
class DecisionExplanation:
    """Penjelasan lengkap untuk satu keputusan."""
    recommended: str
    reason: str
    confidence: float
    score: float

    # Evidence yang digunakan
    evidence_used: List[str] = field(default_factory=list)
    evidence_count: int = 0

    # Asumsi yang dibuat
    assumptions: List[str] = field(default_factory=list)
    assumption_count: int = 0

    # Ketidakpastian
    uncertainty: str = ""
    missing_information: List[str] = field(default_factory=list)

    # Alternatif yang tidak dipilih
    rejected_alternatives: List[AlternativeExplanation] = field(default_factory=list)

    def to_text(self) -> str:
        lines = [
            "Recommended: {title}".format(title=self.recommended),
            "Because: {reason}".format(reason=self.reason),
            "Confidence: {:.0f}% | Score: {:.0f}/100".format(self.confidence * 100, self.score or 0),
        ]
        if self.evidence_used:
            lines.append("Evidence used ({count}):".format(count=len(self.evidence_used)))
            for e in self.evidence_used[:3]:
                lines.append("  - {e}".format(e=e))
        if self.assumptions:
            lines.append("Assumptions ({count}):".format(count=len(self.assumptions)))
            for a in self.assumptions[:3]:
                lines.append("  - {a}".format(a=a))
        if self.missing_information:
            lines.append("Missing: {m}".format(m="; ".join(self.missing_information[:3])))
        if self.rejected_alternatives:
            lines.append("Rejected alternatives:")
            for r in self.rejected_alternatives:
                lines.append("  - {title}: {reason}".format(
                    title=r.title[:40], reason=r.not_chosen_reason[:60],
                ))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "recommended": self.recommended,
            "reason": self.reason,
            "confidence": self.confidence,
            "score": self.score,
            "evidence_count": len(self.evidence_used),
            "evidence_used": self.evidence_used,
            "assumptions": self.assumptions,
            "uncertainty": self.uncertainty,
            "missing_information": self.missing_information,
            "rejected_alternatives": [r.to_text() for r in self.rejected_alternatives],
        }


class ExplanationEngine:
    """Engine untuk menghasilkan penjelasan keputusan.

    Method utama:
      explain(proposal, scored_alternatives, context) -> DecisionExplanation
    """

    def explain(self, proposal: DecisionProposal,
                scored: Optional[ScoredAlternatives] = None,
                context: Optional[Dict[str, Any]] = None) -> DecisionExplanation:
        """Hasilkan penjelasan untuk satu proposal keputusan.

        Args:
            proposal: Proposal yang dipilih
            scored: Alternatif yang sudah di-scoring (opsional)
            context: Data observasi tambahan

        Returns:
            DecisionExplanation — penjelasan lengkap dengan evidence.
        """
        ctx = context or {}

        # Evidence used — dari proposal
        evidence_used = list(proposal.required_evidence)
        if proposal.reason:
            evidence_used.insert(0, "Observation: {}".format(proposal.reason))

        # Convert context keys
        for key, value in ctx.items():
            if isinstance(value, (int, float)):
                evidence_used.append("{key}={value:.1f}".format(key=key, value=value))
            else:
                evidence_used.append("{key}={value}".format(key=key, value=value))

        # Assumptions
        assumptions = self._build_assumptions(proposal, ctx)

        # Missing information
        missing = list(proposal.missing_information)

        # Rejected alternatives
        rejected = []
        if scored:
            for alt in scored.alternatives:
                alt_title = alt.action_title.lower().strip()
                prop_title = proposal.decision.lower().strip()
                # Skip the selected one
                if alt_title == prop_title:
                    continue
                # Bangun alasan kenapa tidak dipilih
                reason = self._build_rejection_reason(alt, proposal, scored)
                rejected.append(AlternativeExplanation(
                    title=alt.action_title,
                    score=alt.score.score,
                    not_chosen_reason=reason,
                    evidence_gap=self._find_evidence_gap(alt, proposal),
                    missing_data=proposal.missing_information,
                ))

        return DecisionExplanation(
            recommended=proposal.decision,
            reason=proposal.reason,
            confidence=proposal.confidence,
            score=scored.best.score.score if scored and scored.best else 0,
            evidence_used=evidence_used,
            evidence_count=len(evidence_used),
            assumptions=assumptions,
            assumption_count=len(assumptions),
            uncertainty=proposal.uncertainty or "None identified",
            missing_information=missing,
            rejected_alternatives=rejected,
        )

    def _build_assumptions(self, proposal: DecisionProposal,
                            ctx: Dict[str, Any]) -> List[str]:
        """Bangun asumsi berdasarkan evidence dan context."""
        assumptions = []

        # Confidence-based assumptions
        if proposal.confidence < 0.5:
            assumptions.append("Low confidence — action may not resolve issue")
        elif proposal.confidence < 0.8:
            assumptions.append("Moderate confidence — past outcomes consistent")

        # Evidence-based assumptions
        if len(proposal.required_evidence) < 2:
            assumptions.append("Single evidence source — may not capture full picture")

        # Blocking conditions
        if proposal.blocking_conditions:
            assumptions.append("Blocking conditions verified: {}".format(
                "; ".join(proposal.blocking_conditions[:2]),
            ))

        # Context-based
        if ctx.get("severity") in ("critical", "high"):
            assumptions.append("High severity — benefit of action outweighs risk")
        if proposal.decision.lower().startswith("do nothing") or proposal.decision.lower().startswith("wait"):
            assumptions.append("Non-intervention — assumes condition is self-correcting")

        return assumptions or ["No assumptions required — evidence is sufficient"]

    def _build_rejection_reason(self, alt: 'ScoredRecommendation',
                                 proposal: DecisionProposal,
                                 scored: ScoredAlternatives) -> str:
        """Bangun alasan kenapa alternatif tidak dipilih."""
        parts = []
        best = scored.best

        # Score comparison
        if best and alt.score.score < best.score.score:
            score_diff = best.score.score - alt.score.score
            parts.append("Score {:.0f} vs best {:.0f} ({:.0f} point gap)".format(
                alt.score.score, best.score.score, score_diff,
            ))

        # Risk
        if alt.score.expected_risk > best.score.expected_risk:
            parts.append("Higher risk ({:.0f} vs {:.0f})".format(
                alt.score.expected_risk, best.score.expected_risk,
            ))

        # Benefit
        if alt.score.expected_benefit < best.score.expected_benefit:
            parts.append("Lower expected benefit")
            if best:
                parts.append("Compared to best")

        # Irreversible
        if not alt.score.reversible:
            parts.append("Irreversible action — higher risk profile")

        # Evidence
        if alt.score.evidence_count < best.score.evidence_count:
            parts.append("Less supporting evidence")

        return "; ".join(parts) or "Score difference"

    def _find_evidence_gap(self, alt: 'ScoredRecommendation',
                            proposal: DecisionProposal) -> str:
        """Temukan gap evidence antara alternatif dan yang dipilih."""
        if alt.score.evidence_count < len(proposal.required_evidence):
            return "Has {:.0f} evidence sources, expected at least {}".format(
                alt.score.evidence_count, len(proposal.required_evidence),
            )
        if alt.score.historical_success < 0.5:
            return "Historical success rate {:.0f}% is below threshold".format(
                alt.score.historical_success * 100,
            )
        if not alt.score.reversible:
            return "Action is irreversible"
        return ""
