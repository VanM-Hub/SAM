"""
OP-293 — Prompt Strategy Engine

Memilih template otomatis berdasarkan ReasoningMode.
Tidak menghasilkan prompt sendiri — hanya pemilihan strategi.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class ReasoningMode(Enum):
    QUESTION = "question"
    ANALYSIS = "analysis"
    SUMMARY = "summary"
    MISSION = "mission"
    HEALTH = "health"
    RISK = "risk"
    ROOT_CAUSE = "root_cause"
    RECOMMENDATION = "recommendation"
    VALIDATION = "validation"
    EXPLANATION = "explanation"


# Mapping: ReasoningMode → template name
_MODE_TO_TEMPLATE: Dict[ReasoningMode, str] = {
    ReasoningMode.QUESTION: "explain",
    ReasoningMode.ANALYSIS: "investigate",
    ReasoningMode.SUMMARY: "summarize",
    ReasoningMode.MISSION: "mission",
    ReasoningMode.HEALTH: "health",
    ReasoningMode.RISK: "investigate",
    ReasoningMode.ROOT_CAUSE: "investigate",
    ReasoningMode.RECOMMENDATION: "recommend",
    ReasoningMode.VALIDATION: "compare",
    ReasoningMode.EXPLANATION: "explain",
}

_MODE_TO_DESCRIPTION: Dict[ReasoningMode, str] = {
    ReasoningMode.QUESTION: "Answer an open question",
    ReasoningMode.ANALYSIS: "Deep analysis of situation",
    ReasoningMode.SUMMARY: "Concise summary",
    ReasoningMode.MISSION: "Mission status evaluation",
    ReasoningMode.HEALTH: "System health check",
    ReasoningMode.RISK: "Risk assessment and identification",
    ReasoningMode.ROOT_CAUSE: "Root cause analysis",
    ReasoningMode.RECOMMENDATION: "Action recommendations",
    ReasoningMode.VALIDATION: "Compare and validate",
    ReasoningMode.EXPLANATION: "Explain reasoning or result",
}


@dataclass(frozen=True)
class PromptStrategy:
    mode: ReasoningMode
    template_name: str
    description: str
    requires_evidence: bool
    priority: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "template_name": self.template_name,
            "description": self.description,
            "requires_evidence": self.requires_evidence,
            "priority": self.priority,
        }


class StrategyEngine:
    """
    Memilih PromptStrategy berdasarkan ReasoningMode.

    Strategy:
    - Mode → template name (via mapping)
    - Tidak menghasilkan prompt — hanya routing
    - Deterministic
    """

    @classmethod
    def get_strategy(cls, mode: ReasoningMode) -> PromptStrategy:
        template = _MODE_TO_TEMPLATE.get(mode, "explain")
        desc = _MODE_TO_DESCRIPTION.get(mode, "Generic reasoning")
        requires = mode in (ReasoningMode.RECOMMENDATION,
                            ReasoningMode.MISSION,
                            ReasoningMode.HEALTH,
                            ReasoningMode.RISK)
        priority = cls._resolve_priority(mode)
        return PromptStrategy(
            mode=mode,
            template_name=template,
            description=desc,
            requires_evidence=requires,
            priority=priority,
        )

    @classmethod
    def resolve_mode(cls, question: str) -> ReasoningMode:
        """
        Resolve mode otomatis dari pertanyaan operator.
        Keyword-matching sederhana, bukan NLP.
        """
        q = question.lower()
        if any(kw in q for kw in ("mission", "goal", "objective", "progress")):
            return ReasoningMode.MISSION
        if any(kw in q for kw in ("health", "status", "alive", "running")):
            return ReasoningMode.HEALTH
        if any(kw in q for kw in ("risk", "danger", "threat", "critical")):
            return ReasoningMode.RISK
        if any(kw in q for kw in ("root cause", "why", "cause", "reason")):
            return ReasoningMode.ROOT_CAUSE
        if any(kw in q for kw in ("recommend", "suggest", "best", "action")):
            return ReasoningMode.RECOMMENDATION
        if any(kw in q for kw in ("explain", "how", "describe")):
            return ReasoningMode.EXPLANATION
        if any(kw in q for kw in ("validate", "verify", "check", "confirm")):
            return ReasoningMode.VALIDATION
        if any(kw in q for kw in ("summarize", "summary", "overview")):
            return ReasoningMode.SUMMARY
        if any(kw in q for kw in ("analyze", "investigate", "look")):
            return ReasoningMode.ANALYSIS
        return ReasoningMode.QUESTION

    @classmethod
    def list_strategies(cls) -> Tuple[PromptStrategy, ...]:
        return tuple(
            cls.get_strategy(mode) for mode in ReasoningMode
        )

    @staticmethod
    def _resolve_priority(mode: ReasoningMode) -> int:
        priority_map = {
            ReasoningMode.HEALTH: 10,
            ReasoningMode.RISK: 9,
            ReasoningMode.ROOT_CAUSE: 8,
            ReasoningMode.MISSION: 7,
            ReasoningMode.RECOMMENDATION: 6,
            ReasoningMode.VALIDATION: 5,
            ReasoningMode.ANALYSIS: 4,
            ReasoningMode.EXPLANATION: 3,
            ReasoningMode.QUESTION: 2,
            ReasoningMode.SUMMARY: 1,
        }
        return priority_map.get(mode, 0)
