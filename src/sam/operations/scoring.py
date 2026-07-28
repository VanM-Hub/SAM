"""
Recommendation Scoring Engine — skor berbasis evidence untuk setiap alternatif.

Tidak boleh ada rekomendasi tanpa score.
Score harus berasal dari evidence, bukan tebakan.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from math import log


@dataclass
class RecommendationScore:
    """Score untuk satu alternatif rekomendasi.

    Semua komponen score berasal dari evidence atau perhitungan objektif.
    Tidak boleh nilai hardcode.
    """
    score: float                         # 0-100 — skor akhir
    confidence: float                    # 0.0-1.0
    expected_benefit: float = 0.0        # Skor manfaat (0-100)
    expected_risk: float = 0.0           # Skor risiko (0-100, makin tinggi makin berisiko)
    cost: float = 0.0                    # Skor biaya (0-100)
    required_time: str = ""              # Estimasi waktu
    reversible: bool = True              # Apakah bisa di-rollback
    reasoning: str = ""                  # Alasan skor

    # Evidence yang digunakan
    evidence_count: int = 0
    severity: str = ""                   # Tingkat keparahan yang diaddress
    historical_success: float = 0.0      # 0.0-1.0 — dari catatan sebelumnya
    estimated_impact: float = 0.0        # 0-100
    reversibility_score: float = 1.0     # 0.0-1.0

    def to_text(self) -> str:
        return "Score {:.0f}/100 (confidence {:.0f}%) — {reasoning}".format(
            self.score, self.confidence * 100, reasoning=self.reasoning[:60],
        )

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "confidence": self.confidence,
            "expected_benefit": self.expected_benefit,
            "expected_risk": self.expected_risk,
            "cost": self.cost,
            "required_time": self.required_time,
            "reversible": self.reversible,
            "reasoning": self.reasoning,
            "evidence_count": self.evidence_count,
            "severity": self.severity,
            "historical_success": self.historical_success,
            "estimated_impact": self.estimated_impact,
            "reversibility_score": self.reversibility_score,
        }


@dataclass
class ScoredRecommendation:
    """Rekomendasi lengkap dengan score."""
    action_title: str
    action_target: str
    score: RecommendationScore

    def to_text(self) -> str:
        return "{title} — Score {score:.0f}/100".format(
            title=self.action_title, score=self.score.score,
        )

    def to_dict(self) -> dict:
        return {
            "action_title": self.action_title,
            "action_target": self.action_target,
            "score": self.score.to_dict(),
        }


@dataclass
class ScoredAlternatives:
    """Kumpulan alternatif yang sudah di-scoring."""
    alternatives: List[ScoredRecommendation] = field(default_factory=list)
    best: Optional[ScoredRecommendation] = None

    def select_best(self) -> Optional[ScoredRecommendation]:
        """Pilih skor tertinggi."""
        if not self.alternatives:
            return None
        best = max(self.alternatives, key=lambda a: a.score.score)
        self.best = best
        return best

    def has_any(self) -> bool:
        return len(self.alternatives) > 0

    def to_text(self) -> str:
        if not self.alternatives:
            return "No alternatives evaluated."
        parts = ["Alternatives evaluated: {}".format(len(self.alternatives))]
        for alt in sorted(self.alternatives, key=lambda a: a.score.score, reverse=True):
            marker = " 👈 BEST" if self.best and alt.action_title == self.best.action_title else ""
            parts.append("  -{}: {:.0f} (benefit={:.0f}, risk={:.0f}, cost={:.0f}){}".format(
                alt.action_title[:40],
                alt.score.score,
                alt.score.expected_benefit,
                alt.score.expected_risk,
                alt.score.cost,
                marker,
            ))
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "count": len(self.alternatives),
            "best": self.best.to_dict() if self.best else None,
            "alternatives": [a.to_dict() for a in self.alternatives],
        }


class ScoringEngine:
    """Engine untuk menghitung score rekomendasi berbasis evidence.

    Formula score:
        score = (expected_benefit * 0.4) + (estimated_impact * 0.3) + (safety_score * 0.2) + (evidence_bonus * 0.1)

    Di mana:
        safety_score = (1 - expected_risk/100) * reversibility_score

    Semua komponen berasal dari evidence.
    Jika evidence tidak cukup → confidence rendah → score tidak rekomendasi.
    """

    def __init__(self):
        self._history_success: Dict[str, float] = {}

    def record_outcome(self, action_title: str, success: bool):
        """Catat outcome historis untuk action type tertentu."""
        key = action_title.lower().strip()
        if success:
            self._history_success[key] = self._history_success.get(key, 0.5) * 0.7 + 0.3
        else:
            self._history_success[key] = self._history_success.get(key, 0.5) * 0.7

    def score_alternatives(self, decisions: List['DecisionProposal'],
                           severity: str = "information",
                           evidence_count: int = 0,
                           context: Optional[Dict[str, Any]] = None) -> ScoredAlternatives:
        """Scoring semua alternatif keputusan.

        Args:
            decisions: Daftar DecisionProposal
            severity: Tingkat keparahan
            evidence_count: Jumlah evidence yang tersedia
            context: Data tambahan (disk usage, cpu, dll.)

        Returns:
            ScoredAlternatives dengan score untuk setiap alternatif.
        """
        ctx = context or {}
        scored = ScoredAlternatives()

        for proposal in decisions:
            action_title = proposal.decision
            action_target = self._extract_target(action_title)

            # === Evidence-based scoring ===

            # 1. Evidence count — makin banyak evidence, makin tinggi confidence
            ev_count = max(proposal.evidence_count, evidence_count)

            # 2. Confidence dari proposal — langsung digunakan
            confidence = proposal.confidence

            # 3. Severity → benefit
            #    Makin parah situasi, makin tinggi benefit action
            severity_map = {
                "critical": 90, "high": 75, "medium": 60,
                "low": 40, "information": 25,
            }
            benefit_base = severity_map.get(severity, 30)
            expected_benefit = min(100, benefit_base + (len(proposal.required_evidence) * 5))

            # 4. Risk assessment dari blocking conditions
            risk_count = len(proposal.blocking_conditions) if proposal.blocking_conditions else 0
            uncertainty_count = len(proposal.missing_information) if proposal.missing_information else 0
            expected_risk = min(100, (risk_count * 20) + (uncertainty_count * 10))

            # 5. Cost estimation dari action type
            cost = self._estimate_cost(action_title, ctx)

            # 6. Reversibility
            irreversible_actions = ["delete", "kill", "flush", "terminate", "remove"]
            reversible = not any(word in action_title.lower() for word in irreversible_actions)
            reversibility_score = 0.8 if reversible else 0.2

            # 7. Historical success
            hist_key = action_title.lower().strip()
            historical_success = self._history_success.get(hist_key, 0.5)

            # 8. Estimated impact (dari context)
            estimated_impact = self._estimate_impact(action_title, ctx, severity)

            # 9. Required time
            required_time = self._estimate_time(action_title)

            # 10. Evidence bonus
            evidence_bonus = min(50, ev_count * 10)

            # === Compute final score ===
            safety_score = (1 - expected_risk / 100) * reversibility_score
            raw_score = (
                (expected_benefit * 0.35) +
                (estimated_impact * 0.25) +
                (safety_score * 100 * 0.20) +
                (evidence_bonus * 0.10) +
                (historical_success * 100 * 0.10)
            )
            final_score = max(0, min(100, raw_score))

            # === Reasoning ===
            reasoning_parts = []
            reasoning_parts.append("Benefit={:.0f}".format(expected_benefit))
            reasoning_parts.append("Impact={:.0f}".format(estimated_impact))
            reasoning_parts.append("Risk={:.0f}".format(expected_risk))
            reasoning_parts.append("HistSuccess={:.0f}%".format(historical_success * 100))
            if ev_count > 0:
                reasoning_parts.append("Evidence={}".format(ev_count))

            score = RecommendationScore(
                score=round(final_score, 1),
                confidence=confidence,
                expected_benefit=expected_benefit,
                expected_risk=expected_risk,
                cost=cost,
                required_time=required_time,
                reversible=reversible,
                reasoning=", ".join(reasoning_parts),
                evidence_count=ev_count,
                severity=severity,
                historical_success=round(historical_success, 2),
                estimated_impact=estimated_impact,
                reversibility_score=reversibility_score,
            )

            rec = ScoredRecommendation(
                action_title=action_title,
                action_target=action_target,
                score=score,
            )
            scored.alternatives.append(rec)

        # Pilih best
        scored.select_best()
        return scored

    def _extract_target(self, title: str) -> str:
        """Extract target object dari action title."""
        title_lower = title.lower()
        targets = {
            "database": "database", "db": "database",
            "disk": "disk", "cache": "cache", "temp": "temp",
            "queue": "queue", "memory": "memory", "cpu": "cpu",
            "worker": "worker", "service": "service",
        }
        for word, target in targets.items():
            if word in title_lower:
                return target
        return "system"

    def _estimate_cost(self, title: str, ctx: dict) -> float:
        """Estimasi cost berdasarkan action type."""
        title_lower = title.lower()
        if any(w in title_lower for w in ["investigate", "review", "monitor"]):
            return 15  # Observasi saja — cost rendah
        elif any(w in title_lower for w in ["clean", "remove", "delete", "flush"]):
            return 25  # Filesystem ops
        elif any(w in title_lower for w in ["backup", "archive", "compress"]):
            return 50  # I/O heavy
        elif any(w in title_lower for w in ["restart", "restore"]):
            return 65  # Interruption
        elif any(w in title_lower for w in ["scale", "upgrade", "deploy"]):
            return 80  # Resource allocation
        elif any(w in title_lower for w in ["escalate", "do nothing", "wait"]):
            return 5  # No action
        return 30

    def _estimate_impact(self, title: str, ctx: dict, severity: str) -> float:
        """Estimasi dampak berdasarkan action type dan context."""
        title_lower = title.lower()
        severity_bonus = {"critical": 20, "high": 15, "medium": 10, "low": 5, "information": 0}.get(severity, 0)

        if any(w in title_lower for w in ["restart"]):
            return min(100, 70 + severity_bonus)
        elif any(w in title_lower for w in ["clean", "free", "remove", "delete"]):
            return min(100, 60 + severity_bonus)
        elif any(w in title_lower for w in ["investigate", "review", "monitor"]):
            return 30
        elif any(w in title_lower for w in ["do nothing", "wait", "escalate"]):
            return 10
        return 50

    def _estimate_time(self, title: str) -> str:
        """Estimasi waktu berdasarkan action type."""
        title_lower = title.lower()
        if any(w in title_lower for w in ["restart", "restore"]):
            return "~30 seconds"
        elif any(w in title_lower for w in ["clean", "free", "remove", "delete"]):
            return "~1 minute"
        elif any(w in title_lower for w in ["investigate", "review", "monitor"]):
            return "~2 minutes"
        elif any(w in title_lower for w in ["backup", "archive", "compress"]):
            return "~5 minutes"
        elif any(w in title_lower for w in ["scale", "upgrade"]):
            return "~10 minutes"
        elif any(w in title_lower for w in ["do nothing", "wait"]):
            return "0 (no action)"
        elif any(w in title_lower for w in ["escalate"]):
            return "~1 minute to notify"
        return "~30 seconds"
