"""WP-05 — Governance Reasoner (IP-3.1-001).

Converts Knowledge + Evidence into a Reasoning Tree.

Per directive:

  *  Input  : Knowledge, Evidence.
  *  Output : Reasoning Tree.
  *  Bukan LLM. ("NOT an LLM.")
  *  Rule Engine dahulu. ("Use a rule engine first.")

The Reasoner uses deterministic user-provided rules. Each rule matches
against ``KnowledgeItem`` (normative knowledge / policies / constraints) and
evaluates against available ``EvidenceRepository`` entries. The output tree
records, per node: the matched knowledge, the evidence cited, and a boolean
or confident verdict. Confidence is 1.0 only when evidence resolves;
otherwise 0.0 (explicitly "missing evidence").

No AI, no probabilistic scoring — rules are explicit predicates supplied by
the caller (imported from the domain adapters, not hard-coded here).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import EvidenceRepository, QueryOnlyRepository


# --- DTOs ------------------------------------------------------------------

@dataclass(frozen=True)
class ReasoningNode:
    """A single node in the Reasoning Tree."""

    label: str
    knowledge: Optional[KnowledgeItem] = None
    matched: bool = False
    confidence: float = 0.0
    children: Tuple["ReasoningNode", ...] = ()

    def public_dict(self) -> dict:
        return {
            "label": self.label,
            "knowledge": self.knowledge.key if self.knowledge else None,
            "matched": self.matched,
            "confidence": self.confidence,
            "children": [c.public_dict() for c in self.children],
        }


@dataclass(frozen=True)
class ReasoningTree:
    """Root of a reasoning tree produced by the Governance Reasoner."""

    goal: str
    root: ReasoningNode

    def public_dict(self) -> dict:
        return {"goal": self.goal, "root": self.root.public_dict()}


# --- Rule type --------------------------------------------------------------

# A Rule is a pure predicate: (item, evidence_repo) -> (matched: bool, conf: float)
Rule = Callable[[KnowledgeItem, EvidenceRepository], Tuple[bool, float]]


def keyword_rule(*keywords: str) -> Rule:
    """Build a deterministic rule: matched if ANY keyword appears in the item
    key/section/title/content. Confidence 1.0 if evidence exists on that key."""

    def _rule(item: KnowledgeItem, evidence: EvidenceRepository) -> Tuple[bool, float]:
        hay = (item.key + " " + item.section + " " + item.title + " " + item.content).lower()
        if not any(k in hay for k in keywords):
            return (False, 0.0)
        # confidence = 1.0 only when evidence resolves for this item
        hits = [ev for ev in evidence.all() if item.key in ev.key or item.section in ev.section]
        return (True, 1.0 if hits else 0.0)

    return _rule


# --- Reasoner ---------------------------------------------------------------

class GovernanceReasoner:
    """WP-05 implementation. Builds a reasoning tree from rules."""

    def __init__(self, knowledge_repo: QueryOnlyRepository) -> None:
        self._knowledge = knowledge_repo

    def reason(
        self,
        goal: str,
        rules: Sequence[Tuple[str, Rule]],
        evidence: EvidenceRepository,
        knowledge: Optional[Sequence[KnowledgeItem]] = None,
    ) -> ReasoningTree:
        """Evaluate ``rules`` over ``knowledge`` (default: repo.all()).

        Returns a tree: one branch per rule, with child nodes per matching
        knowledge item. Unmatched rules produce a leaf node with matched=False
        and confidence 0.0 (missing evidence).
        """
        items = list(knowledge) if knowledge is not None else self._knowledge.all()
        children: List[ReasoningNode] = []
        for label, rule in rules:
            branch_children: List[ReasoningNode] = []
            matched_any = False
            best_conf = 0.0
            for it in items:
                matched, conf = rule(it, evidence)
                if matched:
                    matched_any = True
                    best_conf = max(best_conf, conf)
                    branch_children.append(
                        ReasoningNode(label=it.title or it.key, knowledge=it, matched=True, confidence=conf)
                    )
            children.append(
                ReasoningNode(
                    label=label,
                    knowledge=None,
                    matched=matched_any,
                    confidence=best_conf,
                    children=tuple(branch_children),
                )
            )
        return ReasoningTree(
            goal=goal,
            root=ReasoningNode(
                label=goal,
                knowledge=None,
                matched=any(c.matched for c in children),
                confidence=max((c.confidence for c in children), default=0.0),
                children=tuple(children),
            ),
        )
