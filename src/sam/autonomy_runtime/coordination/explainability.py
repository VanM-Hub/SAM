# Coordination Explainability - WP-38
# IP-3.2-004 (AO-3.2-001 / ED-3.2-004)
#
# Menjelaskan MENGAPA koordinasi antarruntime & transisi lifecycle diusulkan.
# Explanation berbasis model & evidence - bukan aksi. Membantu runtime dan
# governance memahami alasan di balik setiap proposal koordinasi/lifecycle.

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from sam.autonomy_runtime.coordination.engine import CoordinationProposal
from sam.autonomy_runtime.coordination.dependency import DependencyCoordinationPlan
from sam.autonomy_runtime.coordination.models import RuntimeTopology
from sam.autonomy_runtime.lifecycle.planner import LifecyclePlan


@dataclass(frozen=True)
class CoordinationExplanationItem:
    """Penjelasan satu aspek koordinasi/lifecycle (immutable)."""

    subject: str
    what: str
    why: str
    evidence: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "what": self.what,
            "why": self.why,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class CoordinationExplanation:
    """Penjelasan komprehensif keputusan koordinasi & lifecycle (immutable)."""

    explanation_id: str
    basis: str
    coordination_items: Tuple[CoordinationExplanationItem, ...] = ()
    lifecycle_items: Tuple[CoordinationExplanationItem, ...] = ()
    is_proposal_only: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "basis": self.basis,
            "coordination_items": [i.as_dict() for i in self.coordination_items],
            "lifecycle_items": [i.as_dict() for i in self.lifecycle_items],
            "is_proposal_only": self.is_proposal_only,
            "metadata": dict(self.metadata),
        }

    def coordination_count(self) -> int:
        return len(self.coordination_items)

    def lifecycle_count(self) -> int:
        return len(self.lifecycle_items)


class CoordinationExplainer:
    """Menjelaskan keputusan koordinasi & lifecycle (deterministik)."""

    def explain_coordination(
        self,
        topology: RuntimeTopology,
        proposal: CoordinationProposal,
        dep_plan: Optional[DependencyCoordinationPlan] = None,
        explanation_id: str = "",
    ) -> CoordinationExplanation:
        items: list = []
        # koordinasi
        for runtime_id, action in proposal.steps:
            items.append(
                CoordinationExplanationItem(
                    subject=runtime_id,
                    what=action,
                    why="coordination action proposed from runtime topology",
                    evidence=(runtime_id, action),
                )
            )
        # dependency blockers
        if dep_plan:
            for b in dep_plan.blockers:
                items.append(
                    CoordinationExplanationItem(
                        subject=b.runtime_id,
                        what="dependency blocker",
                        why="prerequisite {} not ready".format(b.missing_prereq),
                        evidence=(b.missing_prereq,),
                    )
                )
        explanation_id = explanation_id or self._stable_id(topology.topology_id)
        return CoordinationExplanation(
            explanation_id=explanation_id,
            basis="coordination proposal derived from runtime topology model",
            coordination_items=tuple(items),
            is_proposal_only=True,
            metadata={"deterministic": True},
        )

    def explain_lifecycle(
        self,
        plan: LifecyclePlan,
        explanation_id: str = "",
    ) -> CoordinationExplanation:
        items = []
        for tr in plan.transitions:
            items.append(
                CoordinationExplanationItem(
                    subject=plan.runtime_id,
                    what="propose transition {} -> {}".format(
                        tr.from_stage, tr.to_stage
                    ),
                    why=tr.reason,
                    evidence=(plan.health_trend,),
                )
            )
        for r in plan.readiness:
            items.append(
                CoordinationExplanationItem(
                    subject=r.runtime_id,
                    what="readiness {} -> {}".format(r.from_stage, r.to_stage),
                    why=r.reason,
                    evidence=(str(r.ready),),
                )
            )
        explanation_id = explanation_id or self._stable_id(plan.runtime_id)
        return CoordinationExplanation(
            explanation_id=explanation_id,
            basis="lifecycle proposal derived from lifecycle analysis",
            lifecycle_items=tuple(items),
            is_proposal_only=True,
            metadata={"deterministic": True},
        )

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "ex-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
