"""explanation.decision — WP-06 (IP-3.1-001).

Turns a Reasoning Tree into an immutable ``DecisionExplanation`` containing:

  decision        : the final judgement/answer
  evidence        : the evidence items that support it
  rationale       : human-readable step-by-step text (deterministic)
  confidence      : aggregated confidence over the tree
  missing evidence: explicitly listed gaps (confidence 0.0 / unmatched nodes)

The explanation adds NO new information — it only restates what the reasoner
already produced (per directive: Bukan LLM; deterministic derivation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.reasoning.engine.reasoner import ReasoningNode, ReasoningTree


@dataclass(frozen=True)
class DecisionExplanation:
    """WP-06 output."""

    decision: str
    rationale: str = ""
    confidence: float = 0.0
    evidence: List[KnowledgeItem] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)

    def public_dict(self) -> dict:
        return {
            "decision": self.decision,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "evidence": [e.public_dict() for e in self.evidence],
            "missing_evidence": list(self.missing_evidence),
        }


def _walk(node: ReasoningNode):
    yield node
    for child in node.children:
        yield from _walk(child)


def build_explanation(tree: ReasoningTree) -> DecisionExplanation:
    """Derive a DecisionExplanation from a ReasoningTree (deterministic)."""
    nodes = list(_walk(tree.root))
    evidence: List[KnowledgeItem] = []
    missing: List[str] = []
    seen: set = set()
    for n in nodes:
        if n.knowledge is not None:
            if n.knowledge.id not in seen:
                seen.add(n.knowledge.id)
                evidence.append(n.knowledge)
            if n.confidence < 1.0:
                missing.append(n.knowledge.key)
        elif not n.matched and len(n.children) == 0:
            missing.append(n.label)

    # rationale: each matched branch heading + any unmatched leaf
    lines = ["Tree roots:"]
    for branch in tree.root.children:
        status = "satisfied" if branch.matched else "not satisfied"
        conf = f" (confidence={branch.confidence:.1f})" if branch.confidence else " (missing evidence)"
        lines.append(f"- {branch.label}: {status}{conf}")
    rationale = "\n".join(lines)

    confidence = tree.root.confidence if hasattr(tree.root, "confidence") else 0.0

    return DecisionExplanation(
        decision=f"Goal '{tree.goal}' validated with confidence {confidence:.1f}.",
        rationale=rationale,
        confidence=confidence,
        evidence=evidence,
        missing_evidence=list(dict.fromkeys(missing)),
    )


def explanation_summary(explanation: DecisionExplanation) -> str:
    """Short one-line summary for gateway/report layers."""
    ev = len(explanation.evidence)
    miss = len(explanation.missing_evidence)
    return (
        f"{explanation.decision} | evidence={ev}, "
        f"missing={miss}, confidence={explanation.confidence:.1f}"
    )
