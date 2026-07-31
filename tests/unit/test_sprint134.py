# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 134 - Mission Foundation tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.mission_runtime.mission_context import MissionContext
from sam.mission_runtime.mission_descriptor import MissionDescriptor
from sam.mission_runtime.mission_request import MissionRequest
from sam.mission_runtime.mission_registry import MissionRegistry, MissionRegistrationResult
from sam.mission_runtime.mission_builder import MissionBuilder, MissionOpenPlan
from sam.mission_runtime.conversation_mission import ConversationMissionBridge
from sam.mission_runtime.dashboard_mission import DashboardMissionBridge
from sam.connectors.dashboard_connector import ExecutionCard


# ---------- DTO immutability ----------
class TestContextImmutable:
    def test_frozen(self):
        c = MissionContext("m1")
        with pytest.raises(FrozenInstanceError):
            c.tenant = "x"


class TestDescriptorImmutable:
    def test_frozen(self):
        d = MissionDescriptor("m1")
        with pytest.raises(FrozenInstanceError):
            d.name = "y"


class TestRequestImmutable:
    def test_frozen(self):
        r = MissionRequest("m1")
        with pytest.raises(FrozenInstanceError):
            r.intent = "close"

    def test_lifecycle_only(self):
        assert MissionRequest("m1").is_lifecycle_managed is True


# ---------- Registry ----------
class TestMissionRegistry:
    def test_register_count(self):
        r = MissionRegistry()
        r.register(MissionDescriptor("a", name="A"))
        r.register(MissionDescriptor("b", name="B"))
        assert r.count() == 2

    def test_get(self):
        r = MissionRegistry()
        r.register(MissionDescriptor("a", name="A"))
        assert r.get("a").name == "A"

    def test_missing(self):
        assert MissionRegistry().get("nope") is None

    def test_ids(self):
        r = MissionRegistry()
        r.register(MissionDescriptor("a"))
        assert r.ids() == frozenset({"a"})


# ---------- Builder ----------
class TestMissionBuilder:
    def test_open(self):
        r = MissionRegistry()
        plan = MissionBuilder(r).open(MissionRequest("m1"))
        assert plan.opened is True
        assert plan.is_plan_only is True
        assert r.count() == 1

    def test_empty_returns_none(self):
        assert MissionBuilder(MissionRegistry()).open(MissionRequest("")) is None

    def test_plan_frozen(self):
        plan = MissionBuilder(MissionRegistry()).open(MissionRequest("m1"))
        with pytest.raises(FrozenInstanceError):
            plan.opened = False


# ---------- Conversation bridge ----------
class TestConversationMissionBridge:
    def test_open_and_count(self):
        b = ConversationMissionBridge(MissionRegistry())
        b.open(MissionRequest("m1"))
        assert b.count() == 1

    def test_locate(self):
        b = ConversationMissionBridge(MissionRegistry())
        b.open(MissionRequest("m1"))
        assert b.locate("m1") is not None


# ---------- Dashboard bridge ----------
class TestDashboardMissionBridge:
    def test_five_cards(self):
        b = DashboardMissionBridge(MissionRegistry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        b = DashboardMissionBridge(MissionRegistry())
        assert "lifecycle" in b.verdict_card().summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        MissionContext,
        MissionDescriptor,
        MissionRequest,
        MissionOpenPlan,
        MissionRegistrationResult,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
