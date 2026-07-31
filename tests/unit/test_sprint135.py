# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 135 - Mission Definition tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.mission_runtime.mission_scope import MissionScope
from sam.mission_runtime.mission_constraints import MissionConstraints
from sam.mission_runtime.mission_metadata import MissionMetadata
from sam.mission_runtime.mission_definition import MissionDefinition
from sam.mission_runtime.mission_validator import (
    MissionValidator,
    MissionValidationIssue,
    MissionValidationReport,
)
from sam.mission_runtime.conversation_definition import ConversationDefinitionBridge
from sam.mission_runtime.dashboard_definition import DashboardDefinitionBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _definition():
    return MissionDefinition(
        mission_id="m1",
        scope=MissionScope(domain="ops", modules=("a", "b")),
        constraints=MissionConstraints(preview_only=True, max_objectives=10),
        metadata=MissionMetadata(mission_id="m1", version="1.0.0"),
    )


class TestScopeImmutable:
    def test_frozen(self):
        s = MissionScope()
        with pytest.raises(FrozenInstanceError):
            s.domain = "x"


class TestConstraintsImmutable:
    def test_frozen(self):
        c = MissionConstraints()
        with pytest.raises(FrozenInstanceError):
            c.preview_only = False

    def test_plan_only(self):
        assert MissionConstraints().is_plan_only is True


class TestMetadataImmutable:
    def test_frozen(self):
        m = MissionMetadata("m")
        with pytest.raises(FrozenInstanceError):
            m.owner = "x"


class TestDefinitionImmutable:
    def test_frozen(self):
        d = _definition()
        with pytest.raises(FrozenInstanceError):
            d.mission_id = "x"

    def test_well_defined(self):
        assert _definition().is_well_defined is True


class TestMissionValidator:
    def test_valid(self):
        assert MissionValidator().validate(_definition()).valid is True

    def test_empty_id_invalid(self):
        d = _definition()
        bad = MissionDefinition(
            mission_id="",
            scope=d.scope,
            constraints=d.constraints,
            metadata=d.metadata,
        )
        assert MissionValidator().validate(bad).valid is False

    def test_not_plan_only_invalid(self):
        d = _definition()
        bad = MissionDefinition(
            mission_id=d.mission_id,
            scope=d.scope,
            constraints=MissionConstraints(preview_only=False),
            metadata=d.metadata,
        )
        report = MissionValidator().validate(bad)
        assert report.valid is False
        assert report.issue_count == 1


# ---------- Conversation bridge ----------
class TestConversationDefinitionBridge:
    def test_define(self):
        d = ConversationDefinitionBridge().define("m1")
        assert d.mission_id == "m1"

    def test_validate(self):
        d = ConversationDefinitionBridge().define("m1")
        assert ConversationDefinitionBridge().validate(d).valid is True


# ---------- Dashboard bridge ----------
class TestDashboardDefinitionBridge:
    def test_five_cards(self):
        cards = DashboardDefinitionBridge().cards_for(_definition())
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        b = DashboardDefinitionBridge()
        assert "defined" in b.verdict_card(_definition()).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        MissionScope,
        MissionConstraints,
        MissionMetadata,
        MissionDefinition,
        MissionValidationReport,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
