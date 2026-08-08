"""WP-22 (simulation) - What-If reasoning simulation (IP-3.1-002).

`what_if()` is a pure reasoning SIMULATION. It must NEVER change governance.

It answers questions such as "what changes if a given evidence is not
available?" by re-running the resolution/reasoning chain over a modified,
in-memory snapshot of evidence - never touching the real repositories or
governance artifacts. Output is a simulated outcome only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import EvidenceRepository


@dataclass(frozen=True)
class SimulationResult:
    """Immutable what-if outcome (WP-22 simulation)."""

    scenario: str
    removed_evidence: List[str]
    simulated_evidence_count: int
    outcome: str
    governance_unchanged: bool = True  # always True by design

    def public_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "removed_evidence": list(self.removed_evidence),
            "simulated_evidence_count": self.simulated_evidence_count,
            "outcome": self.outcome,
            "governance_unchanged": self.governance_unchanged,
        }


class WhatIfSimulator:
    """WP-22 simulation engine. Read-only; never mutates governance."""

    def __init__(self, evidence: EvidenceRepository) -> None:
        self._evidence = evidence

    def simulate_missing(self, column: str) -> SimulationResult:
        """Simulate the effect of one evidence column/key being unavailable.

        The real repository is untouched; we compute an in-memory projection
        (minus the matching items) and classify the outcome deterministically.
        """
        removed: List[str] = []
        remaining = 0
        column_low = column.lower()
        for it in self._evidence.all():
            hit = (
                column_low in it.key.lower()
                or column_low in it.section.lower()
                or column_low in it.kind.lower()
            )
            if hit:
                removed.append(it.key)
            else:
                remaining += 1

        if not removed:
            outcome = "NO_IMPACT:evidence column not present, governance unchanged"
        else:
            # Impact classification based on how much key evidence is removed.
            total = remaining + len(removed)
            ratio = (len(removed) / total) if total else 0.0
            if ratio >= 0.5:
                outcome = "HIGH_IMPACT:majority of evidence unavailable, decision basis weakened"
            elif ratio >= 0.2:
                outcome = "MODERATE_IMPACT:significant evidence unavailable, some claims unsupported"
            else:
                outcome = "LOW_IMPACT:minor evidence unavailable, basis still resolvable"

        return SimulationResult(
            scenario=f"evidence '{column}' unavailable",
            removed_evidence=removed,
            simulated_evidence_count=remaining,
            outcome=outcome,
            governance_unchanged=True,
        )
