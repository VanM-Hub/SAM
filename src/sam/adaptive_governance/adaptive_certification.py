"""Adaptive Governance - Certification - WP-61..70 (MISSION-5.6).

Rangkaian sertifikasi Adaptive Governance: learning, effectiveness,
simulation, impact, recommendation, approval/authority boundary, regression,
production readiness, mission.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class AdaptiveCertStatus(str, Enum):
    """Status certification adaptive governance."""

    CERTIFIED = "CERTIFIED"
    CONDITIONALLY_CERTIFIED = "CONDITIONALLY_CERTIFIED"
    NOT_CERTIFIED = "NOT_CERTIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class AdaptiveCertEvidence:
    """Bukti certification adaptive governance."""

    name: str
    passed: bool

    def as_dict(self) -> dict:
        return {"name": self.name, "passed": self.passed}


class AdaptiveGovernanceCertification:
    """Sertifikasi Adaptive Governance (WP-61..70)."""

    def __init__(self) -> None:
        self._evidences: list = []

    def _add(self, name: str, flags: list) -> None:
        for idx, passed in enumerate(flags):
            self._evidences.append(AdaptiveCertEvidence(name=f"{name}#{idx + 1}", passed=bool(passed)))

    def learning_certification(self, *, learn_only=True, evidence_based=True) -> None:
        self._add("adaptive_learning", [learn_only, evidence_based])

    def effectiveness_certification(self, *, analyze_only=True, evidence_based=True) -> None:
        self._add("adaptive_effectiveness", [analyze_only, evidence_based])

    def simulation_certification(self, *, simulate_only=True, no_apply=True) -> None:
        self._add("adaptive_simulation", [simulate_only, no_apply])

    def impact_certification(self, *, assess_only=True, acceptable=True) -> None:
        self._add("adaptive_impact", [assess_only, acceptable])

    def recommendation_certification(self, *, recommend_only=True, human_decides=True) -> None:
        self._add("adaptive_recommendation", [recommend_only, human_decides])

    def approval_boundary(self, *, human_approval=True, authority_retained=True) -> None:
        self._add("adaptive_approval", [human_approval, authority_retained])

    def authority_boundary(self, *, no_authority_change=True, no_auto_apply=True) -> None:
        self._add("adaptive_authority", [no_authority_change, no_auto_apply])

    def regression_verification(self, *, regression=True, compliance=True) -> None:
        self._add("adaptive_regression", [regression, compliance])

    def production_readiness(self, *, ready=True, monitored=True) -> None:
        self._add("adaptive_production", [ready, monitored])

    def mission_certification(self, *, integrated=True, architecture_accepted=True) -> None:
        self._add("adaptive_mission", [integrated, architecture_accepted])

    def certify(self) -> Dict[str, Any]:
        total = len(self._evidences)
        passed = sum(1 for e in self._evidences if e.passed)
        if total == 0:
            status = AdaptiveCertStatus.INSUFFICIENT_EVIDENCE
        elif passed == total:
            status = AdaptiveCertStatus.CERTIFIED
        elif passed >= max(1, total - 2):
            status = AdaptiveCertStatus.CONDITIONALLY_CERTIFIED
        else:
            status = AdaptiveCertStatus.NOT_CERTIFIED
        return {
            "component": "adaptive_governance.mission_5_6",
            "passed": status == AdaptiveCertStatus.CERTIFIED,
            "certified": status == AdaptiveCertStatus.CERTIFIED,
            "status": status.value,
            "passed_count": passed,
            "total_count": total,
        }
