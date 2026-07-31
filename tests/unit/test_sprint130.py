# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 130 - Synchronization tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.sync_request import SyncRequest
from sam.orchestrator.sync_state import SyncState
from sam.orchestrator.sync_snapshot import SyncSnapshot
from sam.orchestrator.sync_validator import SyncValidator, SyncValidationReport
from sam.orchestrator.sync_summary import SyncSummary
from sam.orchestrator.conversation_sync import ConversationSyncBridge
from sam.orchestrator.dashboard_sync import DashboardSyncBridge
from sam.connectors.dashboard_connector import ExecutionCard


class TestRequestImmutable:
    def test_frozen(self):
        r = SyncRequest("s")
        with pytest.raises(FrozenInstanceError):
            r.runtimes = ()


class TestStateImmutable:
    def test_frozen(self):
        s = SyncState("r")
        with pytest.raises(FrozenInstanceError):
            s.state = "synchronized"

    def test_property(self):
        assert SyncState("r", "synchronized").is_synchronized is True


class TestSnapshotImmutable:
    def test_frozen(self):
        s = SyncSnapshot("s")
        with pytest.raises(FrozenInstanceError):
            s.states = ()

    def test_counts(self):
        snap = SyncSnapshot(
            "s",
            states=(
                SyncState("a", "synchronized"),
                SyncState("b", "pending"),
            ),
        )
        assert snap.total == 2
        assert snap.synchronized_count == 1
        assert snap.all_synchronized is False


class TestSyncValidator:
    def test_valid(self):
        snap = SyncSnapshot(
            "s",
            states=(SyncState("a", "synchronized"), SyncState("b", "synchronized")),
        )
        assert SyncValidator().validate(snap).valid is True

    def test_duplicate_invalid(self):
        snap = SyncSnapshot("s", states=(SyncState("a"), SyncState("a")))
        report = SyncValidator().validate(snap)
        assert report.valid is False
        assert report.issue_count == 1

    def test_unknown_state_invalid(self):
        snap = SyncSnapshot("s", states=(SyncState("a", "bogus"),))
        assert SyncValidator().validate(snap).valid is False


class TestSyncSummary:
    def test_summary(self):
        s = SyncSummary("s", ("a", "b"), synchronized=2, total=2)
        assert s.total == 2

    def test_frozen(self):
        s = SyncSummary("s", ("a",))
        with pytest.raises(FrozenInstanceError):
            s.sync_id = "x"


# ---------- Conversation bridge ----------
class TestConversationSyncBridge:
    def test_sync(self):
        b = ConversationSyncBridge()
        snap = b.sync(SyncRequest("s", ("a", "b", "c")))
        assert b.synchronized(snap) == 3

    def test_summary(self):
        b = ConversationSyncBridge()
        snap = b.sync(SyncRequest("s", ("a", "b")))
        assert b.summary(snap)["total"] == 2


# ---------- Dashboard bridge ----------
class TestDashboardSyncBridge:
    def test_five_cards(self):
        snap = SyncSnapshot(
            "s",
            states=(SyncState("a", "synchronized"), SyncState("b", "synchronized")),
        )
        cards = DashboardSyncBridge().cards_for(snap)
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        snap = SyncSnapshot("s", states=(SyncState("a", "synchronized"),))
        b = DashboardSyncBridge()
        assert "sync" in b.verdict_card(snap).summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [SyncRequest, SyncState, SyncSnapshot, SyncValidationReport, SyncSummary]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
