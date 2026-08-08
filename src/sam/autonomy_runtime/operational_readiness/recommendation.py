# Readiness Recommendation Engine - WP-45
# IP-3.2-005 (AO-3.2-001 / ED-3.2-005)
#
# Menyusun prioritas proposal operasional dari hasil agregasi & risiko.
# Prinsip: "Recommendation != Authority." Engine boleh menyusun prioritas,
# TIDAK boleh memilih proposal final, TIDAK menjalankan, TIDAK mengubah
# governance. Seluruh rekomendasi tetap membutuhkan mekanisme governance.
# Deterministic.

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.operational_readiness.models import OperationalReadiness
from sam.autonomy_runtime.operational_readiness.risk import OperationalRiskReport


@dataclass(frozen=True)
class RecommendedAction:
    """Satu aksi/rekomendasi berprioritas (immutable, proposal-only)."""

    action_id: str
    category: str  # recovery | coordination | lifecycle | plan | observe
    description: str
    priority: int  # 1 = paling mendesak
    rationale: str = ""
    evidence: Tuple[str, ...] = ()
    is_proposal: bool = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "category": self.category,
            "description": self.description,
            "priority": self.priority,
            "rationale": self.rationale,
            "evidence": list(self.evidence),
            "is_proposal": self.is_proposal,
        }


@dataclass(frozen=True)
class ReadinessRecommendation:
    """Rekomendasi kesiapan operasional (immutable, proposal-only).

    Berisi urutan proposal yang disarankan (bukan keputusan final). Murni
    saran untuk mekanisme governance yang lebih tinggi. Tidak ada aksi yang
    dieksekusi.
    """

    recommendation_id: str
    readiness_id: str
    actions: Tuple[RecommendedAction, ...] = ()
    primary_focus: str = ""
    is_proposal_only: bool = True
    requires_governance: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "readiness_id": self.readiness_id,
            "actions": [a.as_dict() for a in self.actions],
            "primary_focus": self.primary_focus,
            "is_proposal_only": self.is_proposal_only,
            "requires_governance": self.requires_governance,
            "metadata": dict(self.metadata),
        }

    def action_count(self) -> int:
        return len(self.actions)

    def highest_priority(self) -> Optional[RecommendedAction]:
        if not self.actions:
            return None
        return min(self.actions, key=lambda a: a.priority)


class ReadinessRecommender:
    """Menyusun prioritas rekomendasi operasional (deterministik)."""

    def recommend(
        self,
        readiness: OperationalReadiness,
        risk_report: Optional[OperationalRiskReport] = None,
        recommendation_id: str = "",
    ) -> ReadinessRecommendation:
        actions: List[RecommendedAction] = []

        # (1) kategorisasi berdasar dimensi yang tidak siap -> proposal per kategori
        for d in readiness.dimensions:
            if not d.ready:
                category = self._category_for_dimension(d.name)
                actions.append(RecommendedAction(
                    action_id=self._stable_id("a-{}".format(d.name)),
                    category=category,
                    description="{} dimension below readiness".format(d.name),
                    priority=self._priority_for_dimension(d.name, d.score),
                    rationale=d.detail,
                    evidence=tuple(d.contributing_inputs),
                    is_proposal=True,
                ))

        # (2) risiko tertinggi menambah fokus
        if risk_report and risk_report.highest_risk():
            top = risk_report.highest_risk()
            cat = self._category_for_dimension(top.affected_dimension) \
                if top.affected_dimension else "recovery"
            actions.append(RecommendedAction(
                action_id=self._stable_id("r-{}".format(top.name)),
                category=cat,
                description="address operational risk: {}".format(top.name),
                priority=1 if top.is_critical() else 2,
                rationale=top.basis,
                evidence=(top.name,),
                is_proposal=True,
            ))

        # dedupe & urutkan deterministik (priority asc, action_id asc)
        seen: set = set()
        uniq: List[RecommendedAction] = []
        for a in actions:
            key = (a.category, a.description)
            if key in seen:
                continue
            seen.add(key)
            uniq.append(a)
        uniq.sort(key=lambda a: (a.priority, a.action_id))

        # re-index prioritas kontinu 1..n
        for idx, a in enumerate(uniq, start=1):
            uniq[idx - 1] = RecommendedAction(
                action_id=a.action_id, category=a.category, description=a.description,
                priority=idx, rationale=a.rationale, evidence=a.evidence, is_proposal=True,
            )

        primary = uniq[0].category if uniq else "none"
        return ReadinessRecommendation(
            recommendation_id=recommendation_id or self._stable_id(readiness.readiness_id),
            readiness_id=readiness.readiness_id,
            actions=tuple(uniq),
            primary_focus=primary,
            is_proposal_only=True,
            requires_governance=True,
            metadata={"deterministic": True},
        )

    # --- helpers ---

    @staticmethod
    def _category_for_dimension(name: str) -> str:
        return {
            "observe": "observe",
            "diagnose": "plan",
            "plan": "plan",
            "recover": "recovery",
            "coordinate": "coordination",
            "lifecycle": "lifecycle",
            "readiness": "plan",
        }.get(name, "plan")

    @staticmethod
    def _priority_for_dimension(name: str, score: float) -> int:
        # recover & coordinate paling mendesak bila rendah
        if name in ("recover", "coordinate") and score < 0.6:
            return 1
        if score >= 0.6:
            return 3
        return 2

    @staticmethod
    def _stable_id(seed: str) -> str:
        return "rc-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
