"""Tests for C-Phase 3 (Workstream C3): Approval Operational Intelligence.

Memverifikasi observer Approval menghasilkan observasi operasional Approval
(queue, decision history, metrics) secara read-only, TANPA memanggil mutasi.
"""
from __future__ import annotations
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.approval_intelligence import (
    ApprovalIntelligenceObserver,
    ApprovalIntelligenceReport,
    ApprovalMetric,
    ApprovalMetrics,
    ApprovalQueue,
    ApprovalQueueEntry,
    DecisionHistory,
    DecisionHistoryEntry,
)


def _adapter_for(publication: RuntimePublication) -> PublicationAdapter:
    class _A(PublicationAdapter):
        def runtime_id(self) -> str:
            return publication.runtime_id
        def observe(self) -> RuntimePublication:
            return publication
    return _A()


def _pub_registry() -> PublicationRegistry:
    reg = PublicationRegistry()
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="approval",
        health_state="healthy",
        dashboard_count=10,
        metric_count=0,
        has_preview=False,
        has_metadata=False,
        has_lifecycle=True,
    )))
    return reg


# ── Fake IntakeRegistry + HistoryEngine (read-only) ──

class _FakeIntakeRecord:
    def __init__(self, record_id, timestamp, certified, readiness):
        self.record_id = record_id
        self.timestamp = timestamp
        self.certified = certified
        self.readiness_score = readiness


class _FakeIntakeRegistry:
    def __init__(self, records):
        self._records = list(records)
    def count(self):
        return len(self._records)
    def duplicates(self):
        return 1
    def list_all(self):
        return list(self._records)


class _FakeHistoryEntry:
    def __init__(self, approval_id, phase, actor, reason):
        self.approval_id = approval_id
        self.phase = phase
        self.actor = actor
        self.reason = reason


class _FakeHistoryAll:
    def __init__(self, entries):
        self.entries = list(entries)


class _FakeHistoryEngine:
    def __init__(self, entries):
        self._entries = list(entries)
    def get_all(self):
        return _FakeHistoryAll(self._entries)


def _intake():
    return _FakeIntakeRegistry([
        _FakeIntakeRecord("ap-1", 1000.0, True, 0.9),
        _FakeIntakeRecord("ap-2", 2000.0, False, 0.5),
        _FakeIntakeRecord("ap-3", 3000.0, False, 0.4),
    ])


def _history():
    return _FakeHistoryEngine([
        _FakeHistoryEntry("ap-1", "approve", "user-a", "ok"),
        _FakeHistoryEntry("ap-2", "pending", "user-b", ""),
    ])


class TestApprovalQueue:
    def test_queue_counts(self):
        ob = ApprovalIntelligenceObserver(_pub_registry(), _intake(), _history())
        q = ob.queue()
        assert isinstance(q, ApprovalQueue)
        assert q.total == 3
        assert q.certified == 1
        assert q.pending == 2
        assert q.duplicates == 1
        assert isinstance(q.entries[0], ApprovalQueueEntry)

    def test_queue_status_labels(self):
        ob = ApprovalIntelligenceObserver(_pub_registry(), _intake(), _history())
        q = ob.queue()
        assert q.entries[0].status == "certified"
        assert q.entries[1].status == "pending"


class TestDecisionHistory:
    def test_history_entries(self):
        ob = ApprovalIntelligenceObserver(_pub_registry(), _intake(), _history())
        h = ob.history()
        assert isinstance(h, DecisionHistory)
        assert h.total == 2
        assert isinstance(h.entries[0], DecisionHistoryEntry)
        assert h.entries[0].actor == "user-a"


class TestApprovalMetrics:
    def test_metrics(self):
        ob = ApprovalIntelligenceObserver(_pub_registry(), _intake(), _history())
        m = ob.metrics()
        assert isinstance(m, ApprovalMetrics)
        assert m.queue_size == 3
        assert m.history_entries == 2
        assert m.duplicate_count == 1
        assert all(isinstance(x, ApprovalMetric) for x in m.metrics)


class TestApprovalReport:
    def test_report_aggregates(self):
        ob = ApprovalIntelligenceObserver(_pub_registry(), _intake(), _history())
        rep = ob.report()
        assert isinstance(rep, ApprovalIntelligenceReport)
        assert rep.queue is not None
        assert rep.history is not None
        assert rep.metrics is not None
        assert rep.as_dict()["queue"]["total"] == 3


class TestApprovalReadOnly:
    def test_pub_registry_unchanged(self):
        reg = _pub_registry()
        before = reg.observe_all().runtime_count
        ob = ApprovalIntelligenceObserver(reg, _intake(), _history())
        ob.report(); ob.queue(); ob.history(); ob.metrics()
        after = reg.observe_all().runtime_count
        assert before == after == 1
