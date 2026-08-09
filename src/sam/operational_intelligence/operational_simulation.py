"""Operational Simulation - WP-22 (MISSION-4.2 / IP-4.2-003).

Simulasi operasional untuk menghasilkan proposal sebelum eksekusi.
Deterministik, read-only (tidak melakukan efek nyata).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, List, Tuple

from .evidence_collection import EvidenceModel


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class SimulationOutcome:
    """Satu hasil simulasi."""

    scenario: str
    metric: str
    projected_value: Any
    note: str = ""

    def as_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "metric": self.metric,
            "projected_value": self.projected_value,
            "note": self.note,
        }


@dataclass(frozen=True)
class SimulationProposal:
    """Proposal hasil simulasi (actionable, evidence-backed)."""

    simulation_id: str
    investigation_id: str
    proposal: str
    outcomes: Tuple[SimulationOutcome, ...] = field(default_factory=tuple)
    generated_at: str = field(default_factory=_now_utc)

    @property
    def is_actionable(self) -> bool:
        return bool(self.proposal) and bool(self.outcomes)

    def as_dict(self) -> dict:
        return {
            "simulation_id": self.simulation_id,
            "investigation_id": self.investigation_id,
            "proposal": self.proposal,
            "outcomes": [o.as_dict() for o in self.outcomes],
            "generated_at": self.generated_at,
            "is_actionable": self.is_actionable,
        }


class OperationalSimulator:
    """Simulator operasional (read-only, model-based)."""

    def __init__(self, model: Callable[[str, Tuple[EvidenceModel, ...]], List[Tuple]]) -> None:
        self._model = model

    def simulate(
        self,
        investigation_id: str,
        scenario: str,
        evidences: Tuple[EvidenceModel, ...],
    ) -> SimulationProposal:
        outcomes = self._model(scenario, evidences) or []
        result = tuple(
            SimulationOutcome(
                scenario=scenario, metric=metric, projected_value=value, note=note
            )
            for metric, value, note in outcomes
        )
        import uuid

        return SimulationProposal(
            simulation_id=uuid.uuid4().hex,
            investigation_id=investigation_id,
            proposal=scenario,
            outcomes=result,
        )
