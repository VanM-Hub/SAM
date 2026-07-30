"""Activation Builder — menghasilkan kandidat aktivasi dari konteks."""

from typing import Any, Dict, List

from sam.activation.activation_context import ActivationContext
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_request import ActivationRequest


class ActivationBuilder:
    """Builder — menghasilkan ActivationCandidate dari ActivationContext.

    Hanya generate kandidat. Tidak memilih/mengurutkan.
    """

    GOAL_TYPES = [
        "immediate", "scheduled", "conditional",
        "manual", "batch",
    ]

    def build(self, ctx: ActivationContext, request: ActivationRequest) -> List[ActivationCandidate]:
        candidates: List[ActivationCandidate] = []
        base_name = f"act_{ctx.context_id}"

        # Immediate candidate — selalu ada
        candidates.append(ActivationCandidate(
            candidate_id=f"{base_name}_imm",
            name="Immediate Activation",
            candidate_type="immediate",
            confidence=0.9,
            context_id=ctx.context_id,
            priority_score=1.0 if ctx.environment == "emergency" else 0.5,
            estimated_duration=10.0,
            metadata={"source": request.request_id},
        ))

        # Scheduled — jika bukan emergency
        if ctx.environment != "emergency":
            candidates.append(ActivationCandidate(
                candidate_id=f"{base_name}_sch",
                name="Scheduled Activation",
                candidate_type="scheduled",
                confidence=0.7,
                context_id=ctx.context_id,
                priority_score=0.6,
                estimated_duration=30.0,
                prerequisites=[f"{base_name}_imm"],
                metadata={"source": request.request_id},
            ))

        # Conditional — jika ada goals
        if ctx.total_goals > 0:
            candidates.append(ActivationCandidate(
                candidate_id=f"{base_name}_cond",
                name="Conditional Activation",
                candidate_type="conditional",
                confidence=0.5,
                context_id=ctx.context_id,
                priority_score=0.4,
                estimated_duration=20.0,
                prerequisites=[f"{base_name}_imm", f"{base_name}_sch"],
                metadata={"goal_count": ctx.total_goals},
            ))

        # Manual — jika environment idle
        if ctx.environment == "idle":
            candidates.append(ActivationCandidate(
                candidate_id=f"{base_name}_manual",
                name="Manual Activation",
                candidate_type="manual",
                confidence=0.3,
                context_id=ctx.context_id,
                priority_score=0.2,
                estimated_duration=60.0,
                metadata={"reason": "idle_manual_override"},
            ))

        # Batch — jika banyak kandidat
        if ctx.total_candidates >= 5:
            candidates.append(ActivationCandidate(
                candidate_id=f"{base_name}_batch",
                name="Batch Activation",
                candidate_type="batch",
                confidence=0.8,
                context_id=ctx.context_id,
                priority_score=0.7,
                estimated_duration=45.0,
                prerequisites=[f"{base_name}_imm"],
                metadata={"candidate_count": ctx.total_candidates},
            ))

        return candidates

    def build_types_list(self) -> List[str]:
        return list(self.GOAL_TYPES)
