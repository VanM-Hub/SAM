"""Operational Builder — membuat kandidat dari konteks.

Builder hanya membuat kandidat. Tidak memilih, tidak mengurutkan.
"""

from typing import List

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_goal import GoalType, OperationalGoal
from sam.operational_brain.operational_candidate import OperationalCandidate


class OperationalBuilder:
    """Membangun kandidat berdasarkan konteks operasional."""

    def build(self, context: OperationalContext) -> List[OperationalCandidate]:
        """Hasilkan kandidat dari konteks."""
        candidates: List[OperationalCandidate] = []

        # Jika ada pending_decisions, buat kandidat STABILITY
        if context.pending_decisions > 0:
            goal = OperationalGoal(
                goal_id=f"g_stab_{context.context_id}",
                goal_type=GoalType.STABILITY,
                title="Process pending decisions",
                description=f"Process {context.pending_decisions} pending decisions",
                priority=2,
            )
            candidates.append(self._make_candidate(
                "c_stab", goal,
                score=0.9, urgency=0.9, impact=0.8, effort=0.3,
                confidence=0.9, reason="Pending decisions need resolution",
            ))

        # Jika ada pending_approvals
        if context.pending_approvals > 0:
            goal = OperationalGoal(
                goal_id=f"g_app_{context.context_id}",
                goal_type=GoalType.MISSION,
                title="Process approvals",
                description=f"Process {context.pending_approvals} pending approvals",
                priority=3,
            )
            candidates.append(self._make_candidate(
                "c_app", goal,
                score=0.8, urgency=0.7, impact=0.7, effort=0.2,
                confidence=0.85, reason="Approvals block downstream work",
            ))

        # Resource check
        if context.available_resources > 0:
            goal = OperationalGoal(
                goal_id=f"g_opt_{context.context_id}",
                goal_type=GoalType.OPTIMIZATION,
                title="Utilize available resources",
                description=f"Optimize {context.available_resources} available resources",
                priority=4,
            )
            candidates.append(self._make_candidate(
                "c_opt", goal,
                score=0.7, urgency=0.5, impact=0.6, effort=0.4,
                confidence=0.75, reason="Resources available for work",
            ))

        # Mission candidates
        for mission in context.active_missions:
            goal = OperationalGoal(
                goal_id=f"g_ms_{mission}_{context.context_id}",
                goal_type=GoalType.MISSION,
                title=f"Mission: {mission}",
                description=f"Continue mission {mission}",
                priority=1,
            )
            candidates.append(self._make_candidate(
                f"c_ms_{mission}", goal,
                score=0.95, urgency=0.8, impact=0.9, effort=0.5,
                confidence=0.95, reason=f"Active mission {mission} ongoing",
            ))

        # Low resource → RECOVERY candidate
        if context.available_resources <= 0 and context.environment in ("busy", "emergency"):
            goal = OperationalGoal(
                goal_id=f"g_rec_{context.context_id}",
                goal_type=GoalType.RECOVERY,
                title="Recover operational capacity",
                description="No resources available in busy/emergency environment",
                priority=1,
            )
            candidates.append(self._make_candidate(
                "c_rec", goal,
                score=0.98, urgency=1.0, impact=0.95, effort=0.6,
                confidence=0.8, reason="Critical resource shortage",
            ))

        # Default idle candidate
        if not candidates:
            goal = OperationalGoal(
                goal_id=f"g_idle_{context.context_id}",
                goal_type=GoalType.MONITORING,
                title="Idle monitoring",
                description="No pending work — monitoring only",
                priority=10,
            )
            candidates.append(self._make_candidate(
                "c_idle", goal,
                score=0.1, urgency=0.0, impact=0.0, effort=0.0,
                confidence=1.0, reason="Default idle state",
            ))

        return candidates

    def _make_candidate(self, cid: str, goal: OperationalGoal,
                        score: float, urgency: float, impact: float,
                        effort: float, confidence: float, reason: str) -> OperationalCandidate:
        return OperationalCandidate(
            candidate_id=cid,
            goal=goal,
            score=score,
            urgency=urgency,
            impact=impact,
            effort=effort,
            confidence=confidence,
            reason=reason,
        )
