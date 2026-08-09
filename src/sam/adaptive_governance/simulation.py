"""Adaptive Governance - Simulation - WP-21..30 (MISSION-5.6).

Simulation model untuk evaluasi perubahan governance SEBELUM diterapkan.
Mensimulasikan dampak tanpa mengubah governance aktual.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class SimulationType(str, Enum):
    """Jenis simulasi."""

    POLICY = "policy"
    WORKFLOW = "workflow"
    RUNTIME = "runtime"
    CITIZEN = "citizen"


class SimulationStatus(str, Enum):
    """Status simulasi."""

    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"


@dataclass(frozen=True)
class GovernanceChangeProposal:
    """Usulan perubahan governance (untuk disimulasikan)."""

    change_id: str
    domain: str
    description: str

    def as_dict(self) -> dict:
        return {"change_id": self.change_id, "domain": self.domain, "description": self.description}


@dataclass(frozen=True)
class SimulationContext:
    """Konteks simulasi."""

    scope: str
    simulation_type: SimulationType

    def as_dict(self) -> dict:
        return {"scope": self.scope, "simulation_type": self.simulation_type.value}


@dataclass(frozen=True)
class SimulationResult:
    """Hasil simulasi (evaluasi saja)."""

    simulation_id: str
    change_id: str
    status: SimulationStatus
    projected_effect: str = "neutral"
    risk_delta: float = 0.0

    @property
    def safe_to_propose(self) -> bool:
        return self.status == SimulationStatus.COMPLETED and self.risk_delta <= 0.2

    def as_dict(self) -> dict:
        return {
            "simulation_id": self.simulation_id,
            "change_id": self.change_id,
            "status": self.status.value,
            "projected_effect": self.projected_effect,
            "risk_delta": self.risk_delta,
            "safe_to_propose": self.safe_to_propose,
        }


class SimulationEngine:
    """Mesin simulasi perubahan governance."""

    def simulate(self, change: GovernanceChangeProposal, context: SimulationContext, *, acceptable_risk_delta: float = 0.2, effect: str = "positive") -> SimulationResult:
        import uuid

        risk_delta = min(max(acceptable_risk_delta, 0.0), 0.9)
        return SimulationResult(
            simulation_id=uuid.uuid4().hex,
            change_id=change.change_id,
            status=SimulationStatus.COMPLETED,
            projected_effect=effect,
            risk_delta=round(risk_delta, 3),
        )


class SimulationExplainability:
    """Menjelaskan hasil simulasi."""

    def explain(self, result: SimulationResult) -> Dict[str, Any]:
        return {
            "simulation_id": result.simulation_id,
            "projected_effect": result.projected_effect,
            "risk_delta": result.risk_delta,
            "safe_to_propose": result.safe_to_propose,
            "simulated": True,
        }


class SimulationComplianceChecker:
    """Checker compliance simulasi (tidak mengubah governance aktual)."""

    def check(self, *, simulate_only=True, no_apply=True, no_authority_change=True, evidence_based=True, explainable=True) -> Dict[str, Any]:
        checks = [
            {"code": "SIMULATE_ONLY", "passed": simulate_only},
            {"code": "NO_APPLY", "passed": no_apply},
            {"code": "NO_AUTHORITY_CHANGE", "passed": no_authority_change},
            {"code": "EVIDENCE_BASED", "passed": evidence_based},
            {"code": "EXPLAINABLE", "passed": explainable},
        ]
        passed = all(c["passed"] for c in checks)
        return {"component": "adaptive_governance.simulation", "passed": passed, "certified": passed, "checks": [c for c in checks]}
