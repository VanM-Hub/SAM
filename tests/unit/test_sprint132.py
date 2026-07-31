# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 132 - Runtime Engine tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.runtime_status import RuntimeStatus
from sam.orchestrator.runtime_pipeline import RuntimePipeline
from sam.orchestrator.runtime_snapshot import RuntimeSnapshot
from sam.orchestrator.runtime_report import RuntimeReport
from sam.orchestrator.runtime_engine import RuntimeEngine
from sam.orchestrator.conversation_engine import ConversationEngineBridge
from sam.orchestrator.dashboard_engine import DashboardEngineBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestStatusImmutable:
    def test_frozen(self):
        s = RuntimeStatus()
        with pytest.raises(FrozenInstanceError):
            s.state = "x"

    def test_ready(self):
        assert RuntimeStatus("ready").is_ready is True


class TestPipelineImmutable:
    def test_frozen(self):
        p = RuntimePipeline("p")
        with pytest.raises(FrozenInstanceError):
            p.order = ()

    def test_count(self):
        p = RuntimePipeline("p", ("a", "b", "c"))
        assert p.stage_count == 3


class TestEngine:
    def test_status(self):
        assert RuntimeEngine().status().is_ready is True

    def test_build_pipeline(self):
        p = RuntimeEngine().build_pipeline("pl", ("a", "b"))
        assert p.stage_count == 2

    def test_report_ok(self):
        e = RuntimeEngine()
        pipeline = e.build_pipeline("pl", ("a", "b"))
        assert e.report(pipeline).ok is True

    def test_version(self):
        e = RuntimeEngine()
        pipeline = e.build_pipeline("pl", ("a",))
        assert e.snapshot(pipeline).engine_version == "2.0.0"


class TestSnapshotImmutable:
    def test_frozen(self):
        s = RuntimeSnapshot(RuntimeStatus(), RuntimePipeline("p"))
        with pytest.raises(FrozenInstanceError):
            s.engine_version = "9"


class TestReportImmutable:
    def test_frozen(self):
        r = RuntimeReport(RuntimeStatus(), RuntimeSnapshot(RuntimeStatus(), RuntimePipeline("p")))
        with pytest.raises(FrozenInstanceError):
            r.engine_ready = False


# ---------- Conversation bridge ----------
class TestConversationEngineBridge:
    def test_report(self):
        b = ConversationEngineBridge(RuntimeEngine())
        report = b.report("pl", ("a", "b", "c"))
        assert report.ok is True
        assert b.stages(report) == 3


# ---------- Dashboard bridge ----------
class TestDashboardEngineBridge:
    def test_five_cards(self):
        e = RuntimeEngine()
        report = e.report(e.build_pipeline("pl", ("a", "b", "c", "d")))
        cards = DashboardEngineBridge().cards_for(report)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        e = RuntimeEngine()
        report = e.report(e.build_pipeline("pl", ("a",)))
        b = DashboardEngineBridge()
        assert "plan" in b.verdict_card(report).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [RuntimeStatus, RuntimePipeline, RuntimeSnapshot, RuntimeReport]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
