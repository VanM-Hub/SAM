"""Reasoning Explainability - WP-16 (MISSION-4.4 / IP-4.4-002).

Menjelaskan proses reasoning beserta evidence yang digunakan dan rantai
penalaran. Read-only, auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .structured_reasoning import StructuredReasoning


@dataclass(frozen=True)
class ReasoningTrace:
    """Trace reasoning (rantai langkah + evidence)."""

    reasoning_id: str
    conclusion: str
    step_chain: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    evidence_chain: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "reasoning_id": self.reasoning_id,
            "conclusion": self.conclusion,
            "step_chain": [list(s) for s in self.step_chain],
            "evidence_chain": list(self.evidence_chain),
        }


class ReasoningExplainer:
    """Menjelaskan reasoning (read-only)."""

    def explain(self, reasoning: StructuredReasoning) -> ReasoningTrace:
        step_chain = tuple(
            (s.kind, s.content) for s in reasoning.steps
        )
        evidence_chain = (
            sorted({e for s in reasoning.steps for e in s.evidence_refs})
        )
        return ReasoningTrace(
            reasoning_id=reasoning.reasoning_id,
            conclusion=reasoning.conclusion,
            step_chain=step_chain,
            evidence_chain=tuple(evidence_chain),
        )


class ReasoningExplainabilityAPI:
    """Public read-only API explainability reasoning."""

    def __init__(self, explainer: ReasoningExplainer) -> None:
        self._explainer = explainer

    def explain(self, reasoning: StructuredReasoning) -> Dict[str, Any]:
        return self._explainer.explain(reasoning).as_dict()
