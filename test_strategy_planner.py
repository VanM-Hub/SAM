"""Tests for Strategy Planner — Sprint 27 Fase 2.

Strategic Plan CRUD, phase advancement, current intent, plan intents
persistence, and Strategy Planner (create_strategy, get_next_intent,
execute_next_phase, plan_progress).
"""

import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import pytest_asyncio

from sam.persistence.database import Database
from sam.strategy.goal import StrategicGoal, StrategicGoalManager
from sam.strategy.plan import StrategicPlan, StrategicPlanManager, PLAN_STATUSES
from sam.strategy.planner import StrategyPlanner
from sam.reasoning.intent import Intent, IntentType, IntentStatus
from sam.reasoning.planner import PlanningEngine
from sam.reasoning.templates import GraphTemplate, BUILTIN_TEMPLATES


# ═════════════════════════════════════════════════════════════════
# Fixtures
# ═════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def db():
    """Create temporary database with all migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    database = Database(db_path)
    await database.initialize()
    from sam.persistence.migrations.manager import MigrationManager
    migrations_dir = Path(__file__).parent.parent / "sam" / "persistence" / "migrations"
    manager = MigrationManager(database, str(migrations_dir))
    await manager.migrate()
    yield database
    await database.close()
    Path(db_path).unlink(missing_ok=True)


@pytest_asyncio.fixture
async def sgm(db):
    return StrategicGoalManager(db)


@pytest_asyncio.fixture
async def spm(db):
    return StrategicPlanManager(db)


def make_goal(
    id: str = "sg-plan-1",
    horizon: str = "SHORT_TERM",
    target: Optional[Dict[str, float]] = None,
    current: Optional[Dict[str, float]] = None,
) -> StrategicGoal:
    return StrategicGoal(
        id=id,
        name="Achieve 95% Reliability",
        description="Increase system reliability to 95%",
        horizon=horizon,
        target_metrics=target or {"reliability": 0.95},
        current_metrics=current or {"reliability": 0.80},
        priority=8,
    )


def make_plan(
    id: str = "sp-1",
    goal_id: str = "sg-plan-1",
    name: str = "Test Plan",
    phases: Optional[List[Dict[str, Any]]] = None,
    status: str = "PENDING",
) -> StrategicPlan:
    if phases is None:
        phases = [
            {"name": "Phase 1", "description": "First", "duration_days": 7, "intents": []},
            {"name": "Phase 2", "description": "Second", "duration_days": 14, "intents": []},
        ]
    return StrategicPlan(
        id=id,
        strategic_goal_id=goal_id,
        name=name,
        description="Test plan description",
        phases=phases,
        estimated_duration_days=30,
        status=status,
    )


# ═══════════════════════════════════════════════
# StrategicPlan model tests
# ═══════════════════════════════════════════════

class TestStrategicPlanModel:
    def test_create_minimal(self):
        p = StrategicPlan(id="sp-m", strategic_goal_id="sg-1", name="Min Plan")
        assert p.status == "PENDING"
        assert p.phases == []
        assert p.current_phase_index == 0

    def test_create_with_all_fields(self):
        phases = [{"name": "A", "description": "Ph A", "duration_days": 5, "intents": []}]
        p = StrategicPlan(
            id="sp-full", strategic_goal_id="sg-1", name="Full Plan",
            description="Full desc", phases=phases,
            estimated_duration_days=60, status="ACTIVE", current_phase_index=0,
        )
        assert p.status == "ACTIVE"
        assert len(p.phases) == 1
        assert p.estimated_duration_days == 60

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            StrategicPlan(id="sp-bs", strategic_goal_id="sg-1", name="Bad", status="BOGUS")

    def test_plan_statuses_enum(self):
        assert sorted(PLAN_STATUSES) == sorted(["PENDING", "ACTIVE", "COMPLETED", "FAILED", "PAUSED"])

    def test_to_dict_and_from_dict_roundtrip(self):
        p = make_plan()
        d = p.to_dict()
        p2 = StrategicPlan.from_dict(d)
        assert p2.id == p.id
        assert p2.name == p.name
        assert len(p2.phases) == 2
        assert p2.status == p.status

    def test_from_dict_with_json_string_phases(self):
        d = {
            "id": "sp-js",
            "strategic_goal_id": "sg-1",
            "name": "JSON Plan",
            "description": "",
            "phases": '[{"name":"X","description":"","duration_days":5,"intents":[]}]',
            "estimated_duration_days": 30,
            "status": "PENDING",
            "current_phase_index": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        p = StrategicPlan.from_dict(d)
        assert len(p.phases) == 1
        assert p.phases[0]["name"] == "X"


# ═══════════════════════════════════════════════
# StrategicPlanManager CRUD tests
# ═══════════════════════════════════════════════

class TestStrategicPlanManagerCreate:
    @pytest.mark.asyncio
    async def test_create_plan(self, spm, db):
        p = make_plan()
        pid = await spm.create_plan(p)
        assert pid == "sp-1"
        row = await db.fetch_one("SELECT * FROM strategic_plans WHERE id = ?", (pid,))
        assert row is not None
        assert row["name"] == "Test Plan"

    @pytest.mark.asyncio
    async def test_get_plan(self, spm):
        p = make_plan(id="sp-get")
        await spm.create_plan(p)
        found = await spm.get_plan("sp-get")
        assert found is not None
        assert found.name == "Test Plan"

    @pytest.mark.asyncio
    async def test_get_plan_nonexistent(self, spm):
        found = await spm.get_plan("ghost-sp")
        assert found is None


class TestStrategicPlanManagerUpdate:
    @pytest.mark.asyncio
    async def test_update_status(self, spm):
        await spm.create_plan(make_plan(id="sp-upd"))
        await spm.update_status("sp-upd", "ACTIVE")
        updated = await spm.get_plan("sp-upd")
        assert updated.status == "ACTIVE"

    @pytest.mark.asyncio
    async def test_update_status_invalid(self, spm):
        with pytest.raises(ValueError, match="Invalid status"):
            await spm.update_status("sp-none", "BOGUS")

    @pytest.mark.asyncio
    async def test_update_status_nonexistent(self, spm):
        with pytest.raises(ValueError, match="Strategic plan not found"):
            await spm.update_status("ghost-sp", "ACTIVE")


class TestStrategicPlanManagerAdvance:
    @pytest.mark.asyncio
    async def test_advance_phase(self, spm):
        p = make_plan(id="sp-adv")
        await spm.create_plan(p)
        new_idx = await spm.advance_phase("sp-adv")
        assert new_idx == 1
        updated = await spm.get_plan("sp-adv")
        assert updated.current_phase_index == 1

    @pytest.mark.asyncio
    async def test_advance_beyond_last_raises(self, spm):
        p = make_plan(id="sp-adv-end")
        await spm.create_plan(p)
        await spm.advance_phase("sp-adv-end")  # → 1
        with pytest.raises(ValueError, match="no more phases"):
            await spm.advance_phase("sp-adv-end")  # → 2, but only 2 phases (idx 0, 1)

    @pytest.mark.asyncio
    async def test_get_current_phase(self, spm):
        p = make_plan(id="sp-cp")
        await spm.create_plan(p)
        phase = await spm.get_current_phase("sp-cp")
        assert phase is not None
        assert phase["name"] == "Phase 1"

    @pytest.mark.asyncio
    async def test_get_current_phase_empty_phases(self, spm):
        p = StrategicPlan(id="sp-cp-e", strategic_goal_id="sg-1", name="Empty")
        await spm.create_plan(p)
        phase = await spm.get_current_phase("sp-cp-e")
        assert phase is None

    @pytest.mark.asyncio
    async def test_get_current_phase_after_advance(self, spm):
        p = make_plan(id="sp-cp-a")
        await spm.create_plan(p)
        await spm.advance_phase("sp-cp-a")
        phase = await spm.get_current_phase("sp-cp-a")
        assert phase["name"] == "Phase 2"


class TestStrategicPlanManagerList:
    @pytest.mark.asyncio
    async def test_list_plans(self, spm):
        for i in range(3):
            await spm.create_plan(make_plan(id=f"sp-lst-{i}"))
        plans = await spm.list_plans()
        assert len(plans) >= 3

    @pytest.mark.asyncio
    async def test_list_plans_by_status(self, spm):
        await spm.create_plan(make_plan(id="sp-ls1", status="ACTIVE"))
        await spm.create_plan(make_plan(id="sp-ls2", status="PENDING"))
        active = await spm.list_plans(status="ACTIVE")
        assert len(active) == 1

    @pytest.mark.asyncio
    async def test_list_plans_by_goal(self, spm):
        await spm.create_plan(make_plan(id="sp-lg1", goal_id="sg-alpha"))
        await spm.create_plan(make_plan(id="sp-lg2", goal_id="sg-beta"))
        alpha = await spm.list_plans(goal_id="sg-alpha")
        assert len(alpha) == 1

    @pytest.mark.asyncio
    async def test_list_plans_invalid_status(self, spm):
        with pytest.raises(ValueError, match="Invalid status"):
            await spm.list_plans(status="BOGUS")


class TestStrategicPlanManagerIntents:
    @pytest.mark.asyncio
    async def test_save_and_get_phase_intents(self, spm):
        await spm.create_plan(make_plan(id="sp-int"))
        intent_data = {
            "id": "int-1",
            "type": "DIAGNOSE",
            "target": "system",
            "description": "Check health",
            "parameters": {},
        }
        intent_id = await spm.save_intent("sp-int", 0, intent_data)
        assert intent_id == "int-1"

        intents = await spm.get_phase_intents("sp-int", 0)
        assert len(intents) == 1
        assert intents[0]["type"] == "DIAGNOSE"

    @pytest.mark.asyncio
    async def test_get_phase_intents_empty(self, spm):
        await spm.create_plan(make_plan(id="sp-int-e"))
        intents = await spm.get_phase_intents("sp-int-e", 0)
        assert intents == []

    @pytest.mark.asyncio
    async def test_save_intent_multiple_phases(self, spm):
        await spm.create_plan(make_plan(id="sp-int-m"))
        await spm.save_intent("sp-int-m", 0, {"type": "DIAGNOSE", "target": "a", "description": "A"})
        await spm.save_intent("sp-int-m", 0, {"type": "OPTIMIZE", "target": "b", "description": "B"})
        await spm.save_intent("sp-int-m", 1, {"type": "MONITOR", "target": "c", "description": "C"})

        phase0 = await spm.get_phase_intents("sp-int-m", 0)
        phase1 = await spm.get_phase_intents("sp-int-m", 1)
        assert len(phase0) == 2
        assert len(phase1) == 1


# ═══════════════════════════════════════════════
# StrategyPlanner tests
# ═══════════════════════════════════════════════

class TestStrategyPlannerCreate:
    @pytest.mark.asyncio
    async def test_create_strategy_short_term(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-planner-st"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-planner-st")
        assert plan.strategic_goal_id == "sg-planner-st"
        assert len(plan.phases) == 3  # SHORT_TERM template
        assert plan.status == "PENDING"
        # Each phase should have intents
        for phase in plan.phases:
            assert len(phase["intents"]) > 0

    @pytest.mark.asyncio
    async def test_create_strategy_medium_term(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-planner-mt", horizon="MEDIUM_TERM"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-planner-mt")
        assert len(plan.phases) == 3  # MEDIUM_TERM template
        for phase in plan.phases:
            assert len(phase["intents"]) > 0

    @pytest.mark.asyncio
    async def test_create_strategy_long_term(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-planner-lt", horizon="LONG_TERM"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-planner-lt")
        assert len(plan.phases) == 5  # LONG_TERM template

    @pytest.mark.asyncio
    async def test_create_strategy_nonexistent_goal(self, sgm, spm):
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        with pytest.raises(ValueError, match="Strategic goal not found"):
            await planner.create_strategy("ghost-sg")

    @pytest.mark.asyncio
    async def test_create_strategy_persists_intents(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-planner-pi"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-planner-pi")
        # Check intents were saved to DB
        for idx in range(len(plan.phases)):
            stored = await spm.get_phase_intents(plan.id, idx)
            assert len(stored) > 0


class TestStrategyPlannerNextIntent:
    @pytest.mark.asyncio
    async def test_get_next_intent_first_phase(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-ni-1"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-ni-1")
        intent = await planner.get_next_intent(plan.id)
        assert intent is not None
        assert isinstance(intent, Intent)
        assert intent.status == IntentStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_next_intent_after_all_completed(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-ni-2"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-ni-2")
        # Mark all intents as COMPLETED
        for idx in range(len(plan.phases)):
            stored = await spm.get_phase_intents(plan.id, idx)
            for s in stored:
                await spm.db.execute(
                    "UPDATE plan_intents SET status = 'COMPLETED', updated_at = ? WHERE id = ?",
                    (datetime.now(timezone.utc).isoformat(), s["stored_id"]),
                )
        intent = await planner.get_next_intent(plan.id)
        assert intent is None

    @pytest.mark.asyncio
    async def test_get_next_intent_phase_mismatch(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-ni-3"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-ni-3")
        # Advance phase, then next intent should be from phase 1
        await spm.advance_phase(plan.id)
        intent = await planner.get_next_intent(plan.id)
        assert intent is not None
        # Intent should be from phase 1 (second phase)
        assert intent.status == IntentStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_next_intent_nonexistent_plan(self, sgm, spm):
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        with pytest.raises(ValueError, match="Strategic plan not found"):
            await planner.get_next_intent("ghost-plan")


class TestStrategyPlannerExecutePhase:
    @pytest.mark.asyncio
    async def test_execute_next_phase_pending(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-ex-1"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-ex-1")
        result = await planner.execute_next_phase(plan.id)
        assert result["status"] == "ACTIVE"
        assert result["phase_index"] == 0

        # Plan should now be ACTIVE
        stored = await spm.get_plan(plan.id)
        assert stored.status == "ACTIVE"

    @pytest.mark.asyncio
    async def test_execute_next_phase_already_active(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-ex-2"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-ex-2")
        await planner.execute_next_phase(plan.id)
        # Second call should keep ACTIVE
        result = await planner.execute_next_phase(plan.id)
        assert result["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_execute_next_phase_nonexistent(self, sgm, spm):
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        with pytest.raises(ValueError, match="Strategic plan not found"):
            await planner.execute_next_phase("ghost-plan")


class TestStrategyPlannerProgress:
    @pytest.mark.asyncio
    async def test_progress_pending(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-prog-1"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-prog-1")
        progress = await planner.get_plan_progress(plan.id)
        assert progress == 0.0  # PENDING, no phases completed

    @pytest.mark.asyncio
    async def test_progress_nonexistent(self, sgm, spm):
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        with pytest.raises(ValueError, match="Strategic plan not found"):
            await planner.get_plan_progress("ghost-plan")

    @pytest.mark.asyncio
    async def test_progress_completed(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-prog-2"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-prog-2")
        # Mark all intents as COMPLETED across all phases and advance through all
        for idx in range(len(plan.phases)):
            stored = await spm.get_phase_intents(plan.id, idx)
            for s in stored:
                await spm.db.execute(
                    "UPDATE plan_intents SET status = 'COMPLETED', updated_at = ? WHERE id = ?",
                    (datetime.now(timezone.utc).isoformat(), s["stored_id"]),
                )
            if idx < len(plan.phases) - 1:
                await spm.advance_phase(plan.id)
        await spm.update_status(plan.id, "COMPLETED")
        progress = await planner.get_plan_progress(plan.id)
        assert progress == 1.0

    @pytest.mark.asyncio
    async def test_progress_partial(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-prog-3"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plan = await planner.create_strategy("sg-prog-3")
        # Complete intents for phase 0 only
        stored = await spm.get_phase_intents(plan.id, 0)
        for s in stored:
            await spm.db.execute(
                "UPDATE plan_intents SET status = 'COMPLETED', updated_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), s["stored_id"]),
            )
        progress = await planner.get_plan_progress(plan.id)
        assert 0.0 < progress < 1.0


class TestStrategyPlannerGoalPlans:
    @pytest.mark.asyncio
    async def test_get_goal_plans(self, sgm, spm):
        await sgm.create_goal(make_goal(id="sg-gp-1"))
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        # Create 2 strategies for same goal
        await planner.create_strategy("sg-gp-1")
        await planner.create_strategy("sg-gp-1")
        plans = await planner.get_goal_plans("sg-gp-1")
        assert len(plans) == 2

    @pytest.mark.asyncio
    async def test_get_goal_plans_empty(self, sgm, spm):
        planner = StrategyPlanner(
            planning_engine=None,
            plan_manager=spm,
            goal_manager=sgm,
        )
        plans = await planner.get_goal_plans("sg-gp-empty")
        assert plans == []
