# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 142 - Mission Runtime tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.mission_runtime.mission_status import MissionStatus
from sam.mission_runtime.mission_pipeline import MissionPipeline
from sam.mission_runtime.mission_snapshot import MissionSnapshot
from sam.mission_runtime.mission_reporter import MissionReporter
from sam.mission_runtime.mission_runtime import MissionRuntime
from sam.mission_runtime.conversation_runtime import ConversationRuntimeBridge
from sam.mission_runtime.dashboard_runtime import DashboardRuntimeBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestStatusImmutable:
    def test_frozen(self):
        s = MissionStatus()
        with pytest.raises(FrozenInstanceError):
            s.state = "x"

    def test_ready(self):
        assert MissionStatus("ready").is_ready is True


class TestPipelineImmutable:
    def test_frozen(self):
        p = MissionPipeline()
        with pytest.raises(FrozenInstanceError):
            p.stages = ()

    def test_stage_count(self):
        assert MissionPipeline().stage_count == 10


class TestMissionRuntime:
    def test_status(self):
        assert MissionRuntime().status().is_ready is True

    def test_report_ok(self):
        assert MissionRuntime().report().ok is True

    def test_version(self):
        assert MissionRuntime().snapshot().runtime_version == "2.0.0"


class TestSnapshotImmutable:
    def test_frozen(self):
        s = MissionSnapshot(MissionStatus(), MissionPipeline())
        with pytest.raises(FrozenInstanceError):
            s.runtime_version = "9"


class TestReporterImmutable:
    def test_frozen(self):
        r = MissionReporter(MissionStatus(), MissionSnapshot(MissionStatus(), MissionPipeline()))
        with pytest.raises(FrozenInstanceError):
            r.runtime_ready = False


# ---------- Conversation bridge ----------
class TestConversationRuntimeBridge:
    def test_report(self):
        b = ConversationRuntimeBridge(MissionRuntime())
        assert b.report().ok is True

    def test_snapshot(self):
        b = ConversationRuntimeBridge(MissionRuntime())
        assert b.snapshot().ready is True


# ---------- Dashboard bridge ----------
class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        report = MissionRuntime().report()
        cards = DashboardRuntimeBridge().cards_for(report)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        report = MissionRuntime().report()
        b = DashboardRuntimeBridge()
        assert "lifecycle" in b.verdict_card(report).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [MissionStatus, MissionPipeline, MissionSnapshot, MissionReporter]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
