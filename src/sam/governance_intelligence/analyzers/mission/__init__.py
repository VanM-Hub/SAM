"""analyzers.mission — WP-07 (IP-3.1-001).

MissionAnalyzer consumes the Mission + related repositories and issues:

  MissionSummary     : condensed, traceable mission description.
  MissionIntent      : the declared goal/intent.
  MissionConstraint  : constraints/limits the mission must respect.
  MissionReadiness   : readiness assessment (evidence-backed).

Outputs are immutable DTO. No AI — deterministic projection of the knowledge
index into the analyzer's facets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import MissionRepository


@dataclass(frozen=True)
class MissionSummary:
    mission: str
    version: str = ""
    status: str = ""
    objective: str = ""
    scope: str = ""
    lifecycle: str = ""
    items: List[KnowledgeItem] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {
            "mission": self.mission,
            "version": self.version,
            "status": self.status,
            "objective": self.objective,
            "scope": self.scope,
            "lifecycle": self.lifecycle,
            "items": [i.public_dict() for i in self.items],
        }


@dataclass(frozen=True)
class MissionIntent:
    declaration: str
    confidence: float
    items: List[KnowledgeItem] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {
            "declaration": self.declaration,
            "confidence": self.confidence,
            "items": [i.public_dict() for i in self.items],
        }


@dataclass(frozen=True)
class MissionConstraint:
    declared: bool
    constraints: List[str] = field(default_factory=list)
    items: List[KnowledgeItem] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {
            "declared": self.declared,
            "constraints": list(self.constraints),
            "items": [i.public_dict() for i in self.items],
        }


@dataclass(frozen=True)
class MissionReadiness:
    ready: bool
    missing: List[str] = field(default_factory=list)
    evidence_backed: bool = False
    items: List[KnowledgeItem] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {
            "ready": self.ready,
            "missing": list(self.missing),
            "evidence_backed": self.evidence_backed,
            "items": [i.public_dict() for i in self.items],
        }


class MissionAnalyzer:
    """WP-07 implementation. Read-only, deterministic."""

    def __init__(self, repo: MissionRepository) -> None:
        self._repo = repo

    def _facet(self, label: str) -> List[KnowledgeItem]:
        return [it for it in self._repo.all() if it.metadata.get("facet") == label]

    def summarize(self) -> MissionSummary:
        mission = " ".join(it.content for it in self._facet("Mission"))
        objective = " ".join(it.content for it in self._facet("Objective"))
        scope = " ".join(it.content for it in self._facet("Scope"))
        lifecycle = " ".join(it.content for it in self._facet("Lifecycle"))
        meta = {}
        for it in self._repo.all():
            if it.title:  # capture status/version from metadata if present
                meta[it.title] = it.content
        return MissionSummary(
            mission=mission.strip(),
            objective=objective.strip(),
            scope=scope.strip(),
            lifecycle=lifecycle.strip(),
            items=self._repo.all(),
        )

    def intent(self) -> MissionIntent:
        objs = self._facet("Objective")
        declaration = " ".join(it.content for it in objs).strip()
        return MissionIntent(
            declaration=declaration,
            confidence=1.0 if declaration else 0.0,
            items=objs,
        )

    def constraints(self) -> MissionConstraint:
        # Collect constraints from any item whose section mentions constraint/limit.
        cons = [
            it
            for it in self._repo.all()
            if any(k in (it.section + " " + it.content).lower() for k in ("constraint", "must not", "limit", "batas"))
        ]
        return MissionConstraint(
            declared=bool(cons),
            constraints=[it.title or it.section for it in cons],
            items=cons,
        )

    def readiness(self) -> MissionReadiness:
        objective = self._facet("Objective")
        scope = self._facet("Scope")
        missing = []
        if not objective:
            missing.append("objective")
        if not scope:
            missing.append("scope")
        ready = not missing and bool(self._facet("Mission"))
        return MissionReadiness(
            ready=ready,
            missing=missing,
            evidence_backed=bool(objective and scope),
            items=self._repo.all(),
        )
