"""analyzers.workflow — WP-08 (IP-3.1-001).

WorkflowAnalyzer reasons about workflow state from the Governance
repository. Emits:

  current_stage     : where the workflow currently is.
  next_stage        : the next step.
  blocking_policy   : which policy blocks proceeding.
  waiting_approval  : which approvals are outstanding.
  missing_evidence  : what evidence is required but absent.

Deterministic — derives from indexed workflow/policy/approval items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import PolicyRepository, QueryOnlyRepository


@dataclass(frozen=True)
class WorkflowAnalysis:
    current_stage: str = ""
    next_stage: str = ""
    blocking_policy: str = ""
    waiting_approval: str = ""
    missing_evidence: List[str] = field(default_factory=list)
    items: List[KnowledgeItem] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {
            "current_stage": self.current_stage,
            "next_stage": self.next_stage,
            "blocking_policy": self.blocking_policy,
            "waiting_approval": self.waiting_approval,
            "missing_evidence": list(self.missing_evidence),
            "items": [i.public_dict() for i in self.items],
        }


class WorkflowAnalyzer:
    """WP-08 implementation. Read-only, deterministic."""

    def __init__(self, workflow_repo: QueryOnlyRepository, policy_repo: PolicyRepository) -> None:
        self._workflow = workflow_repo
        self._policy = policy_repo

    def analyze(self, current: str, required_approvals: List[str]) -> WorkflowAnalysis:
        # Derive stages from workflow facet items in order.
        stages = [it for it in self._workflow.all() if it.metadata.get("facet") == "Workflow"]
        current_idx = next((i for i, it in enumerate(stages) if current.lower() in it.section.lower()), None)
        next_stage = ""
        if current_idx is not None and current_idx + 1 < len(stages):
            next_stage = stages[current_idx + 1].section

        # Identify blocking policy: any policy item requiring something not met.
        blocking = ""
        for it in self._policy.all():
            low = (it.section + " " + it.content).lower()
            if "must" in low or "required" in low or "only" in low:
                blocking = it.section or it.title
                break

        # Waiting approval: approvals listed in required_approvals not present as satisfied.
        waiting = ""
        approvals = [it for it in self._workflow.all() if it.metadata.get("facet") == "Approval"]
        for req in required_approvals:
            if not any(req.lower() in (a.section + " " + a.title).lower() for a in approvals):
                waiting = req
                break

        missing = [d for d in required_approvals if d not in [a.section for a in approvals]]
        return WorkflowAnalysis(
            current_stage=current,
            next_stage=next_stage,
            blocking_policy=blocking,
            waiting_approval=waiting,
            missing_evidence=missing,
            items=stages + approvals,
        )
