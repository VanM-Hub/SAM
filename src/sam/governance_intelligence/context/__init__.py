"""WP-16 - Context Resolution Engine (IP-3.1-002).

Resolves governance context across domains. Inputs:

    Mission, Workflow, Runtime, Policy, Evidence, Observation

Output:

    GovernanceContext

Contains: active mission, workflow stage, active policies, runtime state,
readiness, evidence availability, architectural references.

Deterministic. Read-only. Feeds the Cross-Reference (WP-17) and Explainability
layers (WP-19). Every field is derived from the injected repositories via
exact/matching lookups - no LLM, no vector search.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)


@dataclass(frozen=True)
class GovernanceContext:
    """Immutable, cross-domain view of the current governance state."""

    active_mission: str
    workflow_stage: str
    active_policies: List[str]
    runtime_state: str
    readiness: str
    evidence_availability: Dict[str, int]
    architectural_references: List[str]

    def public_dict(self) -> dict:
        return {
            "active_mission": self.active_mission,
            "workflow_stage": self.workflow_stage,
            "active_policies": list(self.active_policies),
            "runtime_state": self.runtime_state,
            "readiness": self.readiness,
            "evidence_availability": dict(self.evidence_availability),
            "architectural_references": list(self.architectural_references),
        }


class ContextResolutionEngine:
    """WP-16 implementation. Composes context from read-only repositories."""

    def __init__(
        self,
        mission: MissionRepository,
        workflow: RuntimeRepository,
        runtime: RuntimeRepository,
        policy: PolicyRepository,
        evidence: EvidenceRepository,
        adr: ADRRepository,
    ) -> None:
        self._mission = mission
        self._workflow = workflow
        self._runtime = runtime
        self._policy = policy
        self._evidence = evidence
        self._adr = adr

    def resolve(self) -> GovernanceContext:
        mission = self._active_mission()
        policies = self._active_policies()
        ev = self._evidence_availability()
        return GovernanceContext(
            active_mission=mission,
            workflow_stage=self._workflow_stage(),
            active_policies=policies,
            runtime_state=self._runtime_state(),
            readiness=self._readiness(ev),
            evidence_availability=ev,
            architectural_references=self._arch_refs(),
        )

    # --- internal deterministic derivation --------------------------------
    def _active_mission(self) -> str:
        for it in self._mission.all():
            if it.section.lower() == "mission":
                return it.title or "Mission"
            if it.key.startswith("mission.") and "objective" in it.key:
                return "Mission active"
        return "Mission"

    def _workflow_stage(self) -> str:
        for it in self._workflow.all():
            meta = it.metadata
            stage = meta.get("stage") or meta.get("current_stage")
            if stage:
                return str(stage)
        return "Unknown"

    def _active_policies(self) -> List[str]:
        out: List[str] = []
        for it in self._policy.all():
            if it.metadata.get("status", "Active") in ("Active", "Enforced"):
                out.append(it.key)
        return out

    def _runtime_state(self) -> str:
        for it in self._runtime.all():
            state = it.metadata.get("state") or it.metadata.get("status")
            if state:
                return str(state)
        return "Unknown"

    def _evidence_availability(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for it in self._evidence.all():
            kind = it.kind or it.metadata.get("domain", "evidence")
            counts[kind] = counts.get(kind, 0) + 1
        return counts

    def _readiness(self, ev: Dict[str, int]) -> str:
        total = sum(ev.values())
        if total == 0:
            return "LOW"
        if total >= 10:
            return "HIGH"
        if total >= 4:
            return "MEDIUM"
        return "LOW"

    def _arch_refs(self) -> List[str]:
        out: List[str] = []
        for it in self._adr.accepted():
            if it.key not in out:
                out.append(it.key)
        return out
