"""Sprint 159 — Mission Planner Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.agent.planner.mission_plan import MissionPlan
from sam.agent.planner.mission_step import MissionStep
from sam.agent.planner.mission_route import MissionRoute, PIPELINE_ROUTE
from sam.agent.planner.mission_dependency import MissionDependency
from sam.agent.planner.mission_builder import MissionBuilder, PlanResult
from sam.agent.planner.conversation_planner import ConversationPlannerBridge
from sam.agent.planner.dashboard_planner import DashboardPlannerBridge
from sam.agent.dashboard.agent_dashboard import ExecutionCard


class TestMissionStep:
    def test_preview_default(self):
        assert MissionStep("s1", "p1", 0, "guardian").preview_only is True

    def test_depends_on(self):
        s = MissionStep("s1", "p1", 0, "decision", dependencies=["s0"])
        assert s.depends_on("s0")
        assert not s.depends_on("zzz")

    def test_immutable(self):
        s = MissionStep("s1", "p1", 0, "guardian")
        with pytest.raises(FrozenInstanceError):
            s.runtime_name = "decision"


class TestMissionPlan:
    def _plan(self):
        steps = [
            MissionStep("a", "p1", 0, "mission"),
            MissionStep("b", "p1", 1, "guardian"),
            MissionStep("c", "p1", 2, "execution"),
        ]
        return MissionPlan("p1", "m1", steps)

    def test_step_count(self):
        assert self._plan().step_count == 3

    def test_ordered(self):
        p = self._plan()
        assert [s.runtime_name for s in p.ordered_steps()] == \
            ["mission", "guardian", "execution"]

    def test_immutable(self):
        p = MissionPlan("p1", "m1")
        with pytest.raises(FrozenInstanceError):
            p.mission_id = "x"


class TestMissionRoute:
    def test_default_route(self):
        r = MissionRoute("m1")
        assert r.runtime_count == len(PIPELINE_ROUTE)
        assert r.contains("guardian")
        assert r.contains("provider")
        assert not r.contains("bogus")

    def test_route_order(self):
        assert PIPELINE_ROUTE[0] == "mission"
        assert PIPELINE_ROUTE[-1] == "provider"
        assert "agent" in PIPELINE_ROUTE

    def test_immutable(self):
        r = MissionRoute("m1")
        with pytest.raises(FrozenInstanceError):
            r.mission_id = "x"


class TestMissionDependency:
    def test_default(self):
        d = MissionDependency("s1", "s0")
        assert d.plan_id == ""

    def test_immutable(self):
        d = MissionDependency("s1", "s0")
        with pytest.raises(FrozenInstanceError):
            d.depends_on = "z"


class TestMissionBuilder:
    def test_build_default(self):
        res = MissionBuilder().build_default("p1", "m1")
        assert res.valid is True
        assert res.plan.step_count == len(PIPELINE_ROUTE)

    def test_build_order(self):
        res = MissionBuilder().build_default("p1", "m1")
        names = [s.runtime_name for s in res.plan.ordered_steps()]
        assert names == PIPELINE_ROUTE

    def test_build_missing_id(self):
        res = MissionBuilder().build_default("", "m1")
        assert res.valid is False

    def test_build_from_route(self):
        route = MissionRoute("m1", runtimes=["guardian", "decision"])
        res = MissionBuilder().build_from_route("p1", "m1", route)
        assert res.valid is True
        assert res.plan.step_count == 2


class TestPlanResult:
    def test_default(self):
        assert PlanResult().valid is False


class TestConversationPlannerBridge:
    def test_show_pipeline_default(self):
        b = ConversationPlannerBridge()
        assert b.show_pipeline() == PIPELINE_ROUTE

    def test_show_pipeline_plan(self):
        res = MissionBuilder().build_default("p1", "m1")
        b = ConversationPlannerBridge(res.plan)
        assert len(b.show_pipeline()) == len(PIPELINE_ROUTE)

    def test_show_step_count(self):
        res = MissionBuilder().build_default("p1", "m1")
        b = ConversationPlannerBridge(res.plan)
        assert b.show_step_count() == len(PIPELINE_ROUTE)

    def test_show_remaining(self):
        res = MissionBuilder().build_default("p1", "m1")
        b = ConversationPlannerBridge(res.plan)
        assert b.show_remaining_steps(done=3) == res.plan.step_count - 3


class TestDashboardPlannerBridge:
    def test_five_cards(self):
        b = DashboardPlannerBridge(MissionBuilder().build_default("p1", "m1").plan)
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardPlannerBridge()
        assert b.overview_card().verdict == "ready"


class TestPlannerImmutability:
    DTO_CLASSES = [
        MissionPlan, MissionStep, MissionRoute,
        MissionDependency, PlanResult,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
