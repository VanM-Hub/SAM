"""
H4 — Operational Alerting Evidence Tests.

Menutup gap H4 (Priority P5, Program D / MISSION-2D, EA-001-004 D4-G1):
- Tidak ada alerting/notification AKTIF (High): platform mengobservasi kondisi
  kritis (Observation layer) tetapi TIDAK memberi tahu operator.

Modul: src/sam/operational_alerting/ (stand-alone capability).
Menyediakan: policy (severity threshold & kanal), routing dedup, store
(ring buffer + acknowledge/resolve), audit metadata.

Constraint EA-002: stand-alone; tidak ubah runtime existing; tidak melakukan
efek eksternal (network/host); murni in-process & deterministik.
"""

import pytest

from sam.operational_alerting.audit import AlertAuditLog
from sam.operational_alerting.dispatcher import AlertDispatcher
from sam.operational_alerting.policy import AlertPolicyEvaluator, build_routing
from sam.operational_alerting.router import AlertRouter, AlertStore
from sam.operational_alerting.state import (
    AlertChannel,
    AlertPolicy,
    AlertRecord,
    AlertSeverity,
    AlertStatus,
    default_policy,
)


@pytest.fixture
def dispatcher():
    return AlertDispatcher()


@pytest.fixture
def alert():
    return AlertRecord(
        title="health degrade",
        message="dependency service down",
        severity=AlertSeverity.CRITICAL,
        source="platform:health",
        source_kind="operational",
    )


# ---------------------------------------------------------------------------
# Records & severity
# ---------------------------------------------------------------------------

class TestRecord:
    def test_record_computes_fingerprint(self):
        a = AlertRecord(title="x", severity=AlertSeverity.ERROR, source="s")
        assert a.fingerprint  # non-empty
        b = AlertRecord(title="x", severity=AlertSeverity.ERROR, source="s")
        assert a.fingerprint == b.fingerprint  # deterministic

    def test_severity_normalized_from_string(self):
        a = AlertRecord(title="x", severity="critical", source="s")
        assert a.severity == AlertSeverity.CRITICAL

    def test_severity_rank_order(self):
        assert AlertSeverity.INFO.rank < AlertSeverity.CRITICAL.rank
        assert AlertSeverity.ERROR.rank == 2

    def test_record_no_payload_secret_guard(self):
        # metadata hanya dict publik; tidak ada field rahasia
        a = AlertRecord(title="x", severity=AlertSeverity.INFO, source="s",
                        metadata={"ok": 1})
        d = a.as_dict()
        assert "metadata" in d
        assert d["metadata"] == {"ok": 1}


# ---------------------------------------------------------------------------
# Policy evaluation
# ---------------------------------------------------------------------------

class TestPolicy:
    def test_default_policy_min_warning(self):
        p = default_policy()
        assert p.min_severity == AlertSeverity.WARNING
        assert p.enabled is True

    def test_route_critical(self, alert):
        p = default_policy()
        decision = build_routing(alert, p)
        assert decision.routed is True
        assert AlertChannel.OPERATOR.value in decision.target_channels

    def test_drop_below_threshold(self):
        p = default_policy()  # min = warning
        rec = AlertRecord(title="info", severity=AlertSeverity.INFO, source="s")
        decision = build_routing(rec, p)
        assert decision.routed is False

    def test_disabled_policy_drops(self, alert):
        p = AlertPolicy(policy_id="off", enabled=False)
        decision = build_routing(alert, p)
        assert decision.routed is False

    def test_policy_threshold_override(self, alert):
        p = AlertPolicy(policy_id="only-critical", min_severity=AlertSeverity.CRITICAL)
        assert build_routing(alert, p).routed is True
        warn = AlertRecord(title="w", severity=AlertSeverity.WARNING, source="s")
        assert build_routing(warn, p).routed is False


# ---------------------------------------------------------------------------
# Router: dedup + store lifecycle
# ---------------------------------------------------------------------------

class TestRouter:
    def test_route_dispatches(self):
        r = AlertRouter()
        rec = AlertRecord(title="x", severity=AlertSeverity.ERROR, source="s")
        stored = r.store.add(rec, [AlertChannel.OPERATOR.value])
        assert r.store.count() == 1
        assert stored.status == AlertStatus.OPEN

    def test_acknowledge(self):
        r = AlertRouter()
        rec = AlertRecord(title="x", severity=AlertSeverity.ERROR, source="s")
        r.store.add(rec, [AlertChannel.OPERATOR.value])
        assert r.acknowledge(rec.alert_id) is True
        assert r.store.by_id(rec.alert_id).status == AlertStatus.ACKNOWLEDGED
        assert r.store.by_id(rec.alert_id).acknowledged_by == "operator"

    def test_resolve(self):
        r = AlertRouter()
        rec = AlertRecord(title="x", severity=AlertSeverity.ERROR, source="s")
        r.store.add(rec, [AlertChannel.OPERATOR.value])
        assert r.resolve(rec.alert_id) is True
        assert r.store.by_id(rec.alert_id).status == AlertStatus.RESOLVED

    def test_unknown_acknowledge_false(self):
        r = AlertRouter()
        assert r.acknowledge("nope") is False
        assert r.resolve("nope") is False

    def test_ring_buffer_retention(self):
        store = AlertStore(max_records=5)
        for i in range(20):
            rec = AlertRecord(title=str(i), severity=AlertSeverity.INFO, source="s")
            store.add(rec, [])
        assert store.count() == 5
        assert store.all()[0].record.title == "15"

    def test_open_count(self):
        store = AlertStore()
        for s in (AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL):
            store.add(AlertRecord(title="x", severity=s, source="s"), [])
        assert store.open_count() == 3
        assert store.critical_open() == 1


# ---------------------------------------------------------------------------
# Dispatcher end-to-end
# ---------------------------------------------------------------------------

class TestDispatcher:
    def test_emit_routes_and_dispatches(self, dispatcher, alert):
        decision = dispatcher.emit(alert)
        assert decision.routed is True
        assert dispatcher.dispatched() == 1
        assert dispatcher.open_alerts() == 1
        assert dispatcher.critical_open() == 1

    def test_emit_drops_below_policy(self, dispatcher):
        rec = AlertRecord(title="info", severity=AlertSeverity.INFO, source="s")
        decision = dispatcher.emit(rec)
        assert decision.routed is False
        assert dispatcher.dispatched() == 0

    def test_dedup_on_duplicate_fingerprint(self, dispatcher, alert):
        dispatcher.emit(alert)
        second = AlertRecord(
            title="health degrade", severity=AlertSeverity.CRITICAL,
            source="platform:health", source_kind="operational",
        )
        decision = dispatcher.emit(second)
        # fingerprint sama, masih OPEN -> dedup, tidak di-dispatch lagi
        assert decision.routed is True
        assert dispatcher.dispatched() == 1
        assert dispatcher.deduped() == 1
        assert dispatcher.open_alerts() == 1

    def test_new_alert_after_resolve_allowed(self, dispatcher, alert):
        d1 = dispatcher.emit(alert)
        dispatcher.resolve(alert.alert_id)
        assert dispatcher.open_alerts() == 0
        # alert baru fingerprint sama setelah yang lama resolved -> boleh
        dispatcher.emit(alert)
        assert dispatcher.dispatched() == 2
        assert dispatcher.open_alerts() == 1

    def test_trigger_convenience(self, dispatcher):
        dispatcher.trigger(
            title="cpu high",
            severity=AlertSeverity.ERROR,
            source="platform:health",
        )
        assert dispatcher.open_alerts() == 1

    def test_audit_tracks_events(self, dispatcher, alert):
        dispatcher.emit(alert)
        dispatcher.acknowledge(alert.alert_id, by="oncall")
        dispatcher.resolve(alert.alert_id)
        audit = dispatcher.audit
        events = [r.event for r in audit.all()]
        assert "route" in events
        assert "acknowledge" in events
        assert "resolve" in events
        assert audit.count() == 3


# ---------------------------------------------------------------------------
# Audit standalone
# ---------------------------------------------------------------------------

class TestAudit:
    def test_no_payload(self):
        log = AlertAuditLog()
        log.record("route", "a1", AlertSeverity.CRITICAL, source="hp")
        for rec in log.all():
            d = rec.as_dict()
            assert "state" not in d
            assert "payload" not in d

    def test_ring_buffer(self):
        log = AlertAuditLog(max_records=3)
        for i in range(10):
            log.record("route", f"a{i}", AlertSeverity.INFO)
        assert log.count() == 3
        assert log.all()[0].alert_id == "a7"

    def test_by_event_and_failures(self):
        log = AlertAuditLog()
        log.record("route", "a1", AlertSeverity.ERROR, outcome="success")
        log.record("route", "a2", AlertSeverity.ERROR, outcome="rejected")
        assert len(log.by_event("route")) == 2
        assert len(log.failures()) == 1


# ---------------------------------------------------------------------------
# Round-trip: kondisi kritis -> alert -> operator acknowledge -> resolve
# ---------------------------------------------------------------------------

class TestAlertRoundTrip:
    def test_full_round_trip(self):
        """Simulasi: health turun -> alert critical -> operator lihat &
        acknowledge -> kondisi pulih -> resolve."""
        d = AlertDispatcher()

        # 1. platform mendeteksi health turun (critical)
        d.emit(AlertRecord(
            title="runtime_health degraded",
            severity=AlertSeverity.CRITICAL,
            source="observation:platform_health",
            source_kind="operational",
        ))
        assert d.open_alerts() == 1
        assert d.critical_open() == 1

        # 2. operator melihat & acknowledge
        alert_id = d.router.store.all()[0].record.alert_id
        assert d.acknowledge(alert_id, by="oncall") is True
        assert d.router.store.by_id(alert_id).status == AlertStatus.ACKNOWLEDGED
        assert d.router.store.by_id(alert_id).acknowledged_by == "oncall"

        # 3. kondisi pulih -> resolve
        assert d.resolve(alert_id) is True
        assert d.router.store.by_id(alert_id).status == AlertStatus.RESOLVED
        assert d.open_alerts() == 0

        # 4. audit mencatat seluruh siklus
        events = [r.event for r in d.audit.all()]
        assert events.count("route") == 1
        assert "acknowledge" in events
        assert "resolve" in events
