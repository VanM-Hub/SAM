# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 136 - Mission Objectives tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.mission_runtime.mission_objective import MissionObjective
from sam.mission_runtime.objective_summary import ObjectiveSummary
from sam.mission_runtime.objective_registry import (
    ObjectiveRegistry,
    ObjectiveRegistrationResult,
)
from sam.mission_runtime.objective_builder import ObjectiveBuilder, ObjectiveBuildResult
from sam.mission_runtime.objective_validator import (
    ObjectiveValidator,
    ObjectiveValidationReport,
)
from sam.mission_runtime.conversation_objective import ConversationObjectiveBridge
from sam.mission_runtime.dashboard_objective import DashboardObjectiveBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _registry():
    r = ObjectiveRegistry()
    r.register(MissionObjective("o1", title="One", priority=1, depends_on=("o0",)))
    r.register(MissionObjective("o0", title="Zero", priority=0))
    return r


class TestObjectiveImmutable:
    def test_frozen(self):
        o = MissionObjective("o1")
        with pytest.raises(FrozenInstanceError):
            o.title = "X"


class TestRegistryImmutableResult:
    def test_register_get(self):
        r = _registry()
        assert r.get("o1").priority == 1

    def test_count(self):
        assert _registry().count() == 2

    def test_all_ordered_by_priority(self):
        order = [o.objective_id for o in _registry().all()]
        assert order == ["o0", "o1"]


class TestObjectiveBuilder:
    def test_add(self):
        r = ObjectiveRegistry()
        result = ObjectiveBuilder(r).add("o1", "One")
        assert result.accepted is True
        assert result.objective.objective_id == "o1"
        assert r.count() == 1


class TestObjectiveValidator:
    def test_valid(self):
        r = _registry()
        assert ObjectiveValidator(r).validate().valid is True

    def test_dangling_invalid(self):
        r = ObjectiveRegistry()
        r.register(MissionObjective("o1", depends_on=("ghost",)))
        report = ObjectiveValidator(r).validate()
        assert report.valid is False
        assert report.issue_count == 1


class TestObjectiveSummary:
    def test_summary(self):
        s = ObjectiveSummary("m", ("a", "b"), total=2)
        assert s.total == 2

    def test_frozen(self):
        s = ObjectiveSummary("m", ("a",))
        with pytest.raises(FrozenInstanceError):
            s.mission_id = "x"


# ---------- Conversation bridge ----------
class TestConversationObjectiveBridge:
    def test_add_count(self):
        b = ConversationObjectiveBridge(ObjectiveRegistry())
        b.add("o1", "One")
        assert b.count() == 1

    def test_summarize(self):
        b = ConversationObjectiveBridge(ObjectiveRegistry())
        b.add("o1", "One")
        s = b.summarize("m")
        assert s.total == 1


# ---------- Dashboard bridge ----------
class TestDashboardObjectiveBridge:
    def test_five_cards(self):
        b = ConversationObjectiveBridge(ObjectiveRegistry())
        b.add("o1", "One")
        cards = DashboardObjectiveBridge().cards_for(b.summarize("m"))
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        s = ObjectiveSummary("m", ("a",))
        b = DashboardObjectiveBridge()
        assert "defined" in b.verdict_card(s).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        MissionObjective,
        ObjectiveSummary,
        ObjectiveRegistrationResult,
        ObjectiveBuildResult,
        ObjectiveValidationReport,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
