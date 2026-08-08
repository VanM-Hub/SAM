"""analyzers.runtime — WP-09 (IP-3.1-001).

RuntimeAnalyzer issues a read-only assessment of a runtime capability:

  health            : whether the capability is declared healthy.
  dependency        : declared dependency.
  capability        : the capability name.
  readiness         : readiness flag (evidence-backed).
  operational_state : textual state (active/standby/etc.).

It NEVER mutates runtime; it only reads the Runtime repository + evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import EvidenceRepository, RuntimeRepository


@dataclass(frozen=True)
class RuntimeAnalysis:
    capability: str = ""
    health: str = ""
    dependency: str = ""
    readiness: bool = False
    operational_state: str = ""
    evidence_backed: bool = False
    items: List[KnowledgeItem] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {
            "capability": self.capability,
            "health": self.health,
            "dependency": self.dependency,
            "readiness": self.readiness,
            "operational_state": self.operational_state,
            "evidence_backed": self.evidence_backed,
            "items": [i.public_dict() for i in self.items],
        }


class RuntimeAnalyzer:
    """WP-09 implementation. Read-only, deterministic."""

    def __init__(self, runtime_repo: RuntimeRepository, evidence_repo: EvidenceRepository) -> None:
        self._runtime = runtime_repo
        self._evidence = evidence_repo

    def analyze(self, capability: str) -> RuntimeAnalysis:
        caps = [
            it
            for it in self._runtime.all()
            if capability.lower() in (it.section + " " + it.title).lower()
        ]
        if not caps:
            return RuntimeAnalysis(capability=capability, health="unknown", readiness=False)

        # Health: 1.0 evidence presence for the capability => healthy.
        backed = any(capability.lower() in (ev.section + " " + ev.key).lower() for ev in self._evidence.all())
        # Dependency: any mention of 'depends'/dependency in content.
        deps = []
        for it in caps:
            low = it.content.lower()
            if "depend" in low:
                deps.append(it.title or it.section)
        state = "operational" if backed else "standby"
        return RuntimeAnalysis(
            capability=capability,
            health="healthy" if backed else "degraded",
            dependency=", ".join(deps),
            readiness=backed,
            operational_state=state,
            evidence_backed=backed,
            items=caps,
        )
