"""
Decision Planner.

Produces DecisionPlan from DecisionEvaluation.
Rule-based. Deterministic. No domain knowledge.
"""

import uuid
from datetime import datetime
from .planning import DecisionPlan, DecisionAlternative, PlanningStage
from .evaluation import DecisionEvaluation, ReadinessLevel
from .planning_alternatives import AlternativeGeneratorS54
from .strategy import StrategyBuilder
from .constraints import ConstraintEngine


class DecisionPlanner:
    """Plans decision options from evaluation."""

    def __init__(self) -> None:
        self._alternatives = AlternativeGeneratorS54()
        self._strategy = StrategyBuilder()
        self._constraints = ConstraintEngine()

    def plan(self, evaluation: DecisionEvaluation) -> DecisionPlan:
        """Create a decision plan from an evaluation."""
        stages = []
        strategy = None
        constraints_result = None

        # Stage 1: Generate alternatives
        alternatives = self._alternatives.generate(evaluation)
        stages.append(PlanningStage(name="alternatives", status="completed",
                                     result={"count": len(alternatives)}))

        # Stage 2: Build strategy
        strategy = self._strategy.build(evaluation)
        stages.append(PlanningStage(name="strategy", status="completed"))

        # Stage 3: Check constraints
        constraints_result = self._constraints.check(evaluation)
        stages.append(PlanningStage(name="constraints", status="completed",
                                     result={"blocked": constraints_result.get("blocked", False),
                                             "constraints": len(constraints_result.get("details", []))}))

        # Recommend best alternative
        recommended = alternatives[0] if alternatives else None

        return DecisionPlan(
            plan_id=str(uuid.uuid4()),
            timestamp=datetime.now().timestamp(),
            evaluation_id=evaluation.evaluation_id,
            alternatives=alternatives,
            recommended=recommended,
            strategy=strategy,
            constraints=constraints_result,
            stages=stages,
            summary=f"Plan: {len(alternatives)} alternatives, readiness={evaluation.ready}",
        )
