"""
Guardian Evidence Chain.

Builds the chain of evidence from Observation to DecisionInput.
DTO only. Rule-based.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .justification import EvidenceReference


@dataclass(frozen=True)
class EvidenceChain:
    chain_id: str = ""; complete: bool = False
    steps: List[EvidenceReference] = field(default_factory=list)
    missing_steps: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str, Any]:
        return {"chain_id":self.chain_id,"complete":self.complete,
                "steps":[s.to_dict() for s in self.steps],"missing_steps":list(self.missing_steps)}


class EvidenceChainBuilder:
    """Builds evidence chain from references."""

    def build(self, references: List[EvidenceReference]) -> EvidenceChain:
        """Build an evidence chain from a list of references."""
        import uuid
        step_types = {r.step for r in references}
        expected_steps = {"observation","transition","situation","assessment","intent","handoff"}
        missing = sorted(expected_steps - step_types)

        return EvidenceChain(
            chain_id=str(uuid.uuid4()),
            complete=len(missing) == 0,
            steps=sorted(references, key=lambda r: r.timestamp),
            missing_steps=missing,
        )
