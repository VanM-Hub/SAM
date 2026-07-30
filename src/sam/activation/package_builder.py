"""Package Builder — membangun ActivationPackage."""
from typing import Any, Dict, List, Optional
from sam.activation.activation_package import ActivationPackage
from sam.activation.activation_sequence import ActivationSequence
from sam.activation.activation_strategy import ActivationStrategy


class PackageBuilder:
    """Membangun ActivationPackage dari sequence + strategy."""

    def build(self, sequence: ActivationSequence,
              strategy: ActivationStrategy,
              plan_ref: str = "") -> ActivationPackage:
        return ActivationPackage(
            package_id=f"pkg_{sequence.sequence_id}",
            plan_ref=plan_ref,
            strategy_ref=strategy.strategy_id,
            sequence_ref=sequence.sequence_id,
            candidate_refs=[s.candidate_ref for s in sequence.steps],
            total_candidates=len(sequence.steps),
            estimated_duration=sequence.duration_estimate,
            confidence=strategy.confidence,
            status="built",
        )
