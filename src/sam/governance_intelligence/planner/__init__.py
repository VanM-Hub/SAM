"""WP-30 - Question Planner (IP-3.1-003).

Given a question, the planner derives a deterministic reasoning STRATEGY:

    Question
      -> Required Knowledge
      -> Required Evidence
      -> Required Runtime
      -> Reasoning Plan

The planner only composes the strategy; it does NOT perform reasoning. The
plan is used by the multi-step pipeline (WP-31) to know which knowledge,
evidence, runtime, and evaluation steps are needed.

Output is deterministic: the same question always yields the same plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ReasoningPlan:
    """Deterministic strategy for answering a question (WP-30)."""

    question: str
    required_knowledge: List[str] = field(default_factory=list)
    required_evidence: List[str] = field(default_factory=list)
    required_runtime: List[str] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {
            "question": self.question,
            "required_knowledge": list(self.required_knowledge),
            "required_evidence": list(self.required_evidence),
            "required_runtime": list(self.required_runtime),
            "reasoning_steps": list(self.reasoning_steps),
        }


# Deterministic category -> requirements mapping. Exact-token based, no LLM.
_TOPIC_TO_REQUIREMENTS = {
    "approval": ["policy", "evidence"],
    "policy": ["policy", "evidence"],
    "workflow": ["policy", "runtime"],
    "mission": ["mission", "evidence"],
    "runtime": ["runtime"],
    "health": ["runtime", "evidence"],
    "readiness": ["runtime", "evidence"],
    "evidence": ["evidence"],
    "adr": ["adr", "evidence"],
}


class QuestionPlanner:
    """WP-30 implementation. Pure strategy composition (no reasoning)."""

    def __init__(self) -> None:
        self._topics = _TOPIC_TO_REQUIREMENTS

    def plan(self, question: str) -> ReasoningPlan:
        q = question.lower()
        # Deterministic topic detection by keyword presence.
        topic = self._detect_topic(q)
        required = self._topics.get(topic, ["knowledge", "evidence"])

        plan = ReasoningPlan(
            question=question,
            required_knowledge=sorted({r for r in required if r in ("policy", "mission", "evidence", "adr")}),
            required_evidence=["evidence"] if "evidence" in required else [],
            required_runtime=["runtime"] if "runtime" in required else [],
            reasoning_steps=self._steps(topic, required),
        )
        return plan

    def _detect_topic(self, q: str) -> str:
        for topic in ("approval", "policy", "workflow", "runtime", "health", "readiness", "evidence", "adr", "mission"):
            if topic in q:
                return topic
        return "general"

    def _steps(self, topic: str, required: List[str]) -> List[str]:
        steps = ["resolve_context"]
        if "mission" in required:
            steps.append("load_mission")
        if "policy" in required:
            steps.append("load_policy")
        if "evidence" in required:
            steps.append("gather_evidence")
        if "runtime" in required:
            steps.append("load_runtime")
        steps.append("reason")
        steps.append("explain")
        steps.append("assess_trust")
        return steps
