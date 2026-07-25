"""Strategy Planner — Sprint 27 Fase 2.

Accepts a Strategic Goal and generates a multi-phase Strategic Plan
with ordered intents for each phase. Integrates with StrategicGoalManager
for goal evaluation and PlanningEngine for intent creation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database
from sam.strategy.goal import StrategicGoal, StrategicGoalManager
from sam.strategy.plan import StrategicPlan, StrategicPlanManager
from sam.reasoning.intent import Intent, IntentType, IntentStatus
from sam.reasoning.planner import PlanningEngine


logger = structlog.get_logger()

PHASE_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "SHORT_TERM": [
        {
            "name": "Assessment",
            "description": "Evaluate current state and gather baseline metrics",
            "duration_days": 7,
            "intents": [
                {"type": "DIAGNOSE", "target": "system", "description": "Assess current metrics"},
                {"type": "DIAGNOSE", "target": "system", "description": "Identify gaps to target"},
            ],
        },
        {
            "name": "Implementation",
            "description": "Execute changes to close metric gaps",
            "duration_days": 14,
            "intents": [
                {"type": "OPTIMIZE", "target": "system", "description": "Improve target metrics"},
            ],
        },
        {
            "name": "Validation",
            "description": "Verify improvements meet target metrics",
            "duration_days": 7,
            "intents": [
                {"type": "MONITOR", "target": "system", "description": "Validate metric improvements"},
            ],
        },
    ],
    "MEDIUM_TERM": [
        {
            "name": "Research & Planning",
            "description": "Analyze requirements and design approach",
            "duration_days": 14,
            "intents": [
                {"type": "DIAGNOSE", "target": "system", "description": "Deep analysis"},
                {"type": "CUSTOM", "target": "system", "description": "Design solution architecture"},
            ],
        },
        {
            "name": "Development",
            "description": "Build and integrate changes across components",
            "duration_days": 30,
            "intents": [
                {"type": "OPTIMIZE", "target": "system", "description": "Implement optimizations"},
                {"type": "DEPLOY", "target": "system", "description": "Roll out changes"},
            ],
        },
        {
            "name": "Testing & Stabilization",
            "description": "Validate, monitor, and stabilize",
            "duration_days": 16,
            "intents": [
                {"type": "MONITOR", "target": "system", "description": "Monitor for regressions"},
                {"type": "REPAIR", "target": "system", "description": "Address issues"},
            ],
        },
    ],
    "LONG_TERM": [
        {
            "name": "Discovery",
            "description": "Comprehensive analysis and strategic alignment",
            "duration_days": 21,
            "intents": [
                {"type": "DIAGNOSE", "target": "system", "description": "Full system audit"},
                {"type": "CUSTOM", "target": "system", "description": "Strategic alignment review"},
            ],
        },
        {
            "name": "Architecture",
            "description": "Design and plan major architectural changes",
            "duration_days": 30,
            "intents": [
                {"type": "CUSTOM", "target": "system", "description": "Architecture design"},
                {"type": "OPTIMIZE", "target": "system", "description": "Design optimizations"},
            ],
        },
        {
            "name": "Execution Phase 1",
            "description": "Implement first wave of changes",
            "duration_days": 45,
            "intents": [
                {"type": "DEPLOY", "target": "system", "description": "Phase 1 deployment"},
                {"type": "SCALE", "target": "system", "description": "Scale improvements"},
            ],
        },
        {
            "name": "Execution Phase 2",
            "description": "Implement remaining changes",
            "duration_days": 45,
            "intents": [
                {"type": "DEPLOY", "target": "system", "description": "Phase 2 deployment"},
                {"type": "OPTIMIZE", "target": "system", "description": "Final optimizations"},
            ],
        },
        {
            "name": "Monitoring & Optimization",
            "description": "Long-term monitoring and continuous improvement",
            "duration_days": 30,
            "intents": [
                {"type": "MONITOR", "target": "system", "description": "Continuous monitoring"},
                {"type": "REPAIR", "target": "system", "description": "Address issues"},
            ],
        },
    ],
}


class StrategyPlanner:
    """Creates strategic plans from Strategic Goals.

    Uses PlanningEngine for intent creation and StrategicGoalManager for
    goal evaluation. Generates phase structures based on goal horizon.
    """

    def __init__(
        self,
        planning_engine: PlanningEngine,
        plan_manager: StrategicPlanManager,
        goal_manager: StrategicGoalManager,
    ) -> None:
        self.planning_engine = planning_engine
        self.plan_manager = plan_manager
        self.goal_manager = goal_manager
        self.logger = logger.bind(component="StrategyPlanner")

    async def create_strategy(self, goal_id: str) -> StrategicPlan:
        """Create a strategic plan from a strategic goal.

        Evaluates the goal, selects phase templates based on horizon,
        generates intents per phase, and persists the plan.
        """
        goal = await self.goal_manager.get_goal(goal_id)
        if goal is None:
            raise ValueError(f"Strategic goal not found: {goal_id}")

        progress = goal.evaluate_progress()
        templates = PHASE_TEMPLATES.get(goal.horizon, PHASE_TEMPLATES["LONG_TERM"])

        # Build phases: clone template and attach generated intents
        phases = []
        total_days = 0
        for template in templates:
            phase = {
                "name": template["name"],
                "description": template["description"],
                "duration_days": template["duration_days"],
                "intents": [],
            }
            for intent_tpl in template["intents"]:
                intent = Intent(
                    type=IntentType(intent_tpl["type"]),
                    target=intent_tpl["target"],
                    description=intent_tpl["description"],
                    parameters={
                        "strategic_goal_id": goal_id,
                        "current_progress": progress,
                    },
                )
                dump = intent.model_dump()
                # Convert datetimes to ISO strings for JSON serialization
                if "created_at" in dump and isinstance(dump["created_at"], datetime):
                    dump["created_at"] = dump["created_at"].isoformat()
                if "updated_at" in dump and isinstance(dump["updated_at"], datetime):
                    dump["updated_at"] = dump["updated_at"].isoformat()
                dump.pop("status", None)  # omit model-level PENDING, use DB-backed status
                phase["intents"].append(dump)
            phases.append(phase)
            total_days += template["duration_days"]

        plan = StrategicPlan(
            id=str(uuid.uuid4()),
            strategic_goal_id=goal_id,
            name=f"Strategy: {goal.name}",
            description=f"Strategic plan for: {goal.description}",
            phases=phases,
            estimated_duration_days=total_days,
            status="PENDING",
            current_phase_index=0,
        )

        await self.plan_manager.create_plan(plan)

        # Persist intents to plan_intents table
        for idx, phase in enumerate(phases):
            for intent_data in phase["intents"]:
                await self.plan_manager.save_intent(plan.id, idx, intent_data)

        self.logger.info(
            "Strategy created",
            goal_id=goal_id,
            plan_id=plan.id,
            phases=len(phases),
            total_days=total_days,
        )
        return plan

    async def get_next_intent(self, plan_id: str) -> Optional[Intent]:
        """Get the next pending intent from the current plan phase."""
        plan = await self.plan_manager.get_plan(plan_id)
        if plan is None:
            raise ValueError(f"Strategic plan not found: {plan_id}")

        phase = await self.plan_manager.get_current_phase(plan_id)
        if phase is None:
            return None

        # Look through stored intents for this phase to find next PENDING one
        stored = await self.plan_manager.get_phase_intents(
            plan_id, plan.current_phase_index
        )
        for s in stored:
            if s.get("status") == "PENDING":
                return Intent(
                    id=s.get("id", s.get("stored_id", str(uuid.uuid4()))),
                    type=IntentType(s.get("type", "CUSTOM")),
                    target=s.get("target", ""),
                    description=s.get("description", ""),
                    parameters=s.get("parameters", {}),
                    status=IntentStatus.PENDING,
                )

        return None

    async def execute_next_phase(self, plan_id: str) -> Dict[str, Any]:
        """Execute the next phase: set plan ACTIVE, return phase details."""
        plan = await self.plan_manager.get_plan(plan_id)
        if plan is None:
            raise ValueError(f"Strategic plan not found: {plan_id}")

        phase = await self.plan_manager.get_current_phase(plan_id)
        if phase is None:
            return {"status": "NO_PHASES", "message": "Plan has no phases"}

        if plan.status == "PENDING":
            await self.plan_manager.update_status(plan_id, "ACTIVE")

        return {
            "status": "ACTIVE",
            "plan_id": plan_id,
            "phase_index": plan.current_phase_index,
            "phase_name": phase.get("name", ""),
            "phase_description": phase.get("description", ""),
            "duration_days": phase.get("duration_days", 0),
            "intents": phase.get("intents", []),
        }

    async def get_plan_progress(self, plan_id: str) -> float:
        """Get overall plan progress as a float 0.0–1.0.

        Computed as: (completed_phases + current_phase_progress) / total_phases
        """
        plan = await self.plan_manager.get_plan(plan_id)
        if plan is None:
            raise ValueError(f"Strategic plan not found: {plan_id}")
        if not plan.phases:
            return 1.0 if plan.status == "COMPLETED" else 0.0
        if plan.status == "COMPLETED":
            return 1.0

        total = len(plan.phases)
        current = plan.current_phase_index
        completed_phases = min(current, total)
        base = completed_phases / total

        # Phase-in-progress contribution (0 to 1/total)
        if current < total:
            stored = await self.plan_manager.get_phase_intents(plan_id, current)
            if stored:
                completed_intents = sum(1 for s in stored if s.get("status") == "COMPLETED")
                phase_weight = completed_intents / len(stored) / total
                base += phase_weight

        return min(1.0, base)

    async def get_goal_plans(
        self, goal_id: str, limit: int = 10
    ) -> List[StrategicPlan]:
        """List all plans associated with a strategic goal."""
        return await self.plan_manager.list_plans(goal_id=goal_id, limit=limit)
