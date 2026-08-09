# -*- coding: utf-8 -*-
"""IP-3.6-C Operational Evidence - Certification (WP-C1..C5, MISSION-3.6).

Menguji: Production Audit Evidence (WP-C1), Operational Metrics (WP-C2),
Runtime Evidence Consolidation (WP-C3), Platform Health Evidence (WP-C4),
Governance Evidence Aggregation (WP-C5), operational evidence compliance
(group OE).

Guardrail (MISSION-3.6): Operational Evidence CONSOLIDATES & AGGREGATES
evidence yang diberikan; TIDAK mengumpulkan via sensor/agent atau memodifikasi
evidence sumber.
"""

import pytest

from sam.platform import (
    AuditEvent,
    AuditEvidenceSummary,
    GovernanceEvidenceAggregate,
    GovernanceEvidencePoint,
    HealthEvidenceSummary,
    HealthSignal,
    MetricPoint,
    MetricsSummary,
    RuntimeConsolidation,
    RuntimeEvidencePiece,
    aggregate_governance_evidence,
    consolidate_runtime_evidence,
    operational_evidence_compliance_check,
    summarize_audit_evidence,
    summarize_health_evidence,
    summarize_metrics,
)


# --- WP-C1 Production Audit Evidence ----------------------------------------

def test_audit_summary_counts():
    s = summarize_audit_evidence([
        AuditEvent("a1", "info", recorded=True),
        AuditEvent("a2", "info", recorded=True),
        AuditEvent("a3", "warn", recorded=True),
        AuditEvent("a4", "info", recorded=False),
    ])
    assert s.recorded_events == 3
    assert s.missing_events == 1
    assert s.total == 4
    assert ("info", 2) in s.kind_counts
    assert ("warn", 1) in s.kind_counts


def test_audit_summary_empty():
    s = summarize_audit_evidence([])
    assert s.total == 0
    assert s.kind_counts == ()


# --- WP-C2 Operational Metrics -----------------------------------------------

def test_metrics_average_per_name():
    s = summarize_metrics([
        MetricPoint("cpu", 0.5),
        MetricPoint("cpu", 0.7),
        MetricPoint("mem", 0.4),
    ])
    assert s.value_of("cpu") == pytest.approx(0.6)
    assert s.value_of("mem") == pytest.approx(0.4)
    assert s.average == pytest.approx((0.5 + 0.7 + 0.4) / 3, abs=1e-3)


def test_metrics_missing_name():
    s = summarize_metrics([MetricPoint("cpu", 0.5)])
    assert s.value_of("nope") is None


def test_metrics_empty_average_zero():
    s = summarize_metrics([])
    assert s.average == 0.0
    assert s.by_name == ()


# --- WP-C3 Runtime Evidence Consolidation ------------------------------------

def test_runtime_consolidation_healthy():
    c = consolidate_runtime_evidence([
        RuntimeEvidencePiece("runtime", status="ok"),
        RuntimeEvidencePiece("governance", status="ok"),
    ])
    assert c.source_count == 2
    assert c.healthy
    assert ("ok", 2) in c.status_distribution


def test_runtime_consolidation_unhealthy():
    c = consolidate_runtime_evidence([
        RuntimeEvidencePiece("runtime", status="ok"),
        RuntimeEvidencePiece("workflow", status="degraded"),
    ])
    assert not c.healthy
    assert ("degraded", 1) in c.status_distribution


# --- WP-C4 Platform Health Evidence -----------------------------------------

def test_health_all_ok():
    s = summarize_health_evidence([
        HealthSignal("core", healthy=True),
        HealthSignal("net", healthy=True),
    ])
    assert s.ok
    assert s.healthy == ("core", "net")


def test_health_unhealthy_collected():
    s = summarize_health_evidence([
        HealthSignal("core", healthy=True),
        HealthSignal("net", healthy=False),
    ])
    assert not s.ok
    assert s.unhealthy == ("net",)


# --- WP-C5 Governance Evidence Aggregation -----------------------------------

def test_governance_aggregate_normalized():
    a = aggregate_governance_evidence([
        GovernanceEvidencePoint("decision", 0.8),
        GovernanceEvidencePoint("policy", 0.6),
    ])
    # weighted_sum = sum(w*w), total = sum(w)
    assert a.weighted_sum == pytest.approx(0.8 ** 2 + 0.6 ** 2)
    assert a.total_weight == pytest.approx(1.4)
    assert a.normalized == pytest.approx((0.8 ** 2 + 0.6 ** 2) / 1.4, abs=1e-3)


def test_governance_aggregate_empty_normalized_zero():
    a = aggregate_governance_evidence([])
    assert a.normalized == 0.0
    assert (a.weighted_sum, a.total_weight) == (0.0, 0.0)


# --- OE compliance -----------------------------------------------------------

def test_operational_evidence_compliance_passes():
    res = operational_evidence_compliance_check()
    assert res.ok, res.messages
    assert res.group == "OE"
    assert res.forbidden_found == ()


# --- Exit criteria: consolidate evidence, never collect/modify --------------

def test_oe_has_no_collector_verbs():
    import sam.platform.operational_evidence as oe
    names = [n for n in dir(oe) if not n.startswith("_")]
    forbidden = {"collect_metric", "probe_runtime", "spawn_sensor",
                 "modify_evidence", "write_audit_log", "emit_metric"}
    assert not (forbidden & set(names))
