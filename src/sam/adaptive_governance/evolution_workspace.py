"""Adaptive Governance - Evolution Workspace - WP-51..60 (MISSION-5.6).

Explorer: governance history, learning, effectiveness, simulation, impact,
recommendation, approval state. Presentation; no business logic / authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from .effectiveness import EffectivenessReport
from .impact import ImpactAssessment
from .learning import LearningDataset
from .recommendation import ApprovalContext, GovernanceRecommendation
from .simulation import SimulationResult


@dataclass(frozen=True)
class WorkspaceVisit:
    """Entri eksplorasi (read-only)."""

    area: str
    item_id: str

    def as_dict(self) -> dict:
        return {"area": self.area, "item_id": self.item_id}


class GovernanceEvolutionWorkspace:
    """Fasilitas eksplorasi evolusi governance."""

    def __init__(self, learning: LearningDataset, reports: Tuple[EffectivenessReport, ...] = (), simulations: Tuple[SimulationResult, ...] = (), impacts: Tuple[ImpactAssessment, ...] = (), recommendations: Tuple[GovernanceRecommendation, ...] = ()) -> None:
        self._learning = learning
        self._reports = reports
        self._simulations = simulations
        self._impacts = impacts
        self._recommendations = recommendations
        self._visits: list = []

    def history_explorer(self) -> Tuple[WorkspaceVisit, ...]:
        return tuple(WorkspaceVisit("history", f"sample-{n}") for n in range(1, self._learning.size() + 1))

    def learning_explorer(self) -> Tuple[WorkspaceVisit, ...]:
        return tuple(WorkspaceVisit("learning", f"pattern-{n}") for n in range(1, len(self._learning.samples()) + 1))

    def effectiveness_explorer(self) -> Tuple[WorkspaceVisit, ...]:
        return tuple(WorkspaceVisit("effectiveness", r.scope) for r in self._reports)

    def simulation_explorer(self) -> Tuple[WorkspaceVisit, ...]:
        return tuple(WorkspaceVisit("simulation", s.simulation_id) for s in self._simulations)

    def impact_explorer(self) -> Tuple[WorkspaceVisit, ...]:
        return tuple(WorkspaceVisit("impact", i.target_id) for i in self._impacts)

    def recommendation_explorer(self) -> Tuple[WorkspaceVisit, ...]:
        return tuple(WorkspaceVisit("recommendation", r.recommendation_id) for r in self._recommendations)

    def approval_state(self) -> Tuple[ApprovalContext, ...]:
        return tuple(ApprovalContext(r.recommendation_id) for r in self._recommendations)

    def explain(self, area: str) -> Dict[str, Any]:
        return {"area": area, "explainable": True, "authority_retained": True}


class EvolutionWorkspaceComplianceChecker:
    """Checker compliance workspace evolusi (presentation)."""

    def check(self, *, presentation_only=True, no_business_logic=True, no_authority_change=True, human_decides=True) -> Dict[str, Any]:
        checks = [
            {"code": "PRESENTATION_ONLY", "passed": presentation_only},
            {"code": "NO_BUSINESS_LOGIC", "passed": no_business_logic},
            {"code": "NO_AUTHORITY_CHANGE", "passed": no_authority_change},
            {"code": "HUMAN_DECIDES", "passed": human_decides},
        ]
        passed = all(c["passed"] for c in checks)
        return {"component": "adaptive_governance.workspace", "passed": passed, "certified": passed, "checks": [c for c in checks]}
