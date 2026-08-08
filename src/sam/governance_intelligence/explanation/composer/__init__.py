"""WP-19 - Explanation Composer (IP-3.1-002).

Turns a reasoning tree into a clear, fixed-structure explanation.

The output MUST have a fixed structure:

    Summary
    Evidence
    Governance Basis
    Architectural Basis
    Confidence
    Missing Information

Free-form narration without this structure is NOT allowed. This module
composes the fixed fields deterministically from the reasoning tree and the
evidence/context it references.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sam.governance_intelligence.reasoning.evidence import EvidenceChain
from sam.governance_intelligence.reasoning.engine.reasoner import ReasoningNode, ReasoningTree


@dataclass(frozen=True)
class StructuredExplanation:
    """Fixed-structure explanation (WP-19 output)."""

    summary: str
    evidence: List[str]
    governance_basis: List[str]
    architectural_basis: List[str]
    confidence: float
    missing_information: List[str]

    def public_dict(self) -> dict:
        return {
            "summary": self.summary,
            "evidence": list(self.evidence),
            "governance_basis": list(self.governance_basis),
            "architectural_basis": list(self.architectural_basis),
            "confidence": self.confidence,
            "missing_information": list(self.missing_information),
        }


class ExplanationComposer:
    """WP-19 implementation. Composes fixed-structure explanations."""

    def compose(
        self,
        tree: ReasoningTree,
        chain: Optional[EvidenceChain] = None,
        governance_basis: Optional[List[str]] = None,
        architectural_basis: Optional[List[str]] = None,
    ) -> StructuredExplanation:
        summary = self._summary(tree)
        evidence = self._evidence(tree, chain)
        gov = governance_basis if governance_basis is not None else self._governance(tree)
        arch = architectural_basis if architectural_basis is not None else []
        confidence = self._confidence(tree, chain)
        missing = self._missing(tree, chain)
        return StructuredExplanation(
            summary=summary,
            evidence=evidence,
            governance_basis=gov,
            architectural_basis=arch,
            confidence=confidence,
            missing_information=missing,
        )

    # --- deterministic derivation -----------------------------------------
    def _summary(self, tree: ReasoningTree) -> str:
        return f"Decision reached for: {tree.goal}"

    def _evidence(self, tree: ReasoningTree, chain: Optional[EvidenceChain]) -> List[str]:
        keys: List[str] = []
        if chain is not None:
            for it in chain.evidence:
                if it.key not in keys:
                    keys.append(it.key)
        if not keys:
            # deterministic fallback: matched node labels from the tree
            keys = self._matched_labels(tree.root)
        return keys

    def _governance(self, tree: ReasoningTree) -> List[str]:
        # governance basis = the deterministic rules (branch labels) applied
        return self._branch_labels(tree.root)

    def _confidence(self, tree: ReasoningTree, chain: Optional[EvidenceChain]) -> float:
        if chain is not None and chain.evidence:
            return 1.0
        return float(getattr(tree, "confidence", None) or tree.root.confidence or 0.0)

    def _missing(self, tree: ReasoningTree, chain: Optional[EvidenceChain]) -> List[str]:
        missing: List[str] = []
        if chain is not None and not chain.evidence:
            missing.append("no direct evidence matched")
        # branches that did not match represent missing governance support
        for branch in tree.root.children:
            if not branch.matched:
                missing.append(f"rule '{branch.label}' has no matching governance item")
        return missing

    @staticmethod
    def _matched_labels(node: ReasoningNode) -> List[str]:
        out: List[str] = []
        if node.matched and node.knowledge is not None and node.knowledge.key not in out:
            out.append(node.knowledge.key)
        for child in node.children:
            for k in ExplanationComposer._matched_labels(child):
                if k not in out:
                    out.append(k)
        return out

    @staticmethod
    def _branch_labels(node: ReasoningNode) -> List[str]:
        """Collect ancestor branch labels (the applied rule names)."""
        out: List[str] = []
        for child in node.children:
            if child.label and child.label not in out:
                out.append(child.label)
        return out
