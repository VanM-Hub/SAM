"""Tests for C-Phase 3 (Workstream C5): Audit Operational Intelligence.

Memverifikasi observer Audit menghasilkan observasi operasional Audit
(audits, correlation, compliance, search) secara read-only, tanpa merekam.
"""
from __future__ import annotations
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.audit_intelligence import (
    AuditCorrelation,
    AuditIntelligenceObserver,
    AuditIntelligenceReport,
    AuditView,
    ComplianceStatus,
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
        runtime_id="audit",
        health_state="healthy",
        dashboard_count=9,
        metric_count=1,
        has_preview=True,
        has_metadata=True,
        has_lifecycle=False,
    )))
    return reg


# ── Fake AuditRegistry (read-only) ──

class _FakeAudit:
    def __init__(self, audit_id, category, description, provenance=True,
                 traceability=True, tags=()):
        self.audit_id = audit_id
        self.category = category
        self.description = description
        self.provenance = provenance
        self.traceability = traceability
        self.tags = list(tags)


class _FakeAuditRegistry:
    def __init__(self, items):
        self._items = list(items)
    def all_entries(self):
        return list(self._items)


def _audit_registry():
    return _FakeAuditRegistry([
        _FakeAudit("AUD-001", "compliance", "Runtime compliance", tags=["policy", "runtime"]),
        _FakeAudit("AUD-002", "security", "Access security", provenance=True, traceability=True),
        _FakeAudit("AUD-003", "compliance", "Data compliance", traceability=False),
    ])


class TestAuditViews:
    def test_lists_audits(self):
        ob = AuditIntelligenceObserver(_pub_registry(), _audit_registry())
        audits = ob.audits()
        assert len(audits) == 3
        assert isinstance(audits[0], AuditView)
        assert audits[0].audit_id == "AUD-001"

    def test_timeline_is_audits(self):
        ob = AuditIntelligenceObserver(_pub_registry(), _audit_registry())
        assert len(ob.timeline()) == 3


class TestAuditCorrelation:
    def test_by_category(self):
        ob = AuditIntelligenceObserver(_pub_registry(), _audit_registry())
        c = ob.correlation()
        assert isinstance(c, AuditCorrelation)
        assert c.total_audits == 3
        cats = dict(c.by_category)
        assert cats["compliance"] == 2
        assert cats["security"] == 1
        assert c.traceable_count == 2
        assert c.provenance_count == 3


class TestAuditCompliance:
    def test_compliance_status(self):
        ob = AuditIntelligenceObserver(_pub_registry(), _audit_registry())
        cs = ob.compliance()
        assert isinstance(cs, ComplianceStatus)
        assert cs.total_audits == 3
        assert cs.traceable == 2
        assert cs.compliant is False  # ada audit tanpa traceability


class TestAuditSearch:
    def test_search_by_category(self):
        ob = AuditIntelligenceObserver(_pub_registry(), _audit_registry())
        res = ob.search("security")
        assert len(res) == 1
        assert res[0].audit_id == "AUD-002"

    def test_search_by_tag(self):
        ob = AuditIntelligenceObserver(_pub_registry(), _audit_registry())
        res = ob.search("policy")
        assert len(res) == 1

    def test_search_empty_query_returns_none(self):
        ob = AuditIntelligenceObserver(_pub_registry(), _audit_registry())
        assert ob.search("") == ()


class TestAuditReport:
    def test_report_aggregates(self):
        ob = AuditIntelligenceObserver(_pub_registry(), _audit_registry())
        rep = ob.report()
        assert isinstance(rep, AuditIntelligenceReport)
        assert rep.correlation is not None
        assert rep.compliance is not None
        assert rep.as_dict()["audit_count"] == 3

    def test_report_with_search(self):
        ob = AuditIntelligenceObserver(_pub_registry(), _audit_registry())
        rep = ob.report("security")
        assert len(rep.search_results) == 1


class TestAuditEvidence:
    def test_evidence_summary_delegates(self):
        ob = AuditIntelligenceObserver(_pub_registry(), _audit_registry())
        idx = ob.evidence_summary()
        assert idx.total_entries > 0
        assert idx.verified_count == idx.total_entries


class TestAuditReadOnly:
    def test_pub_registry_unchanged(self):
        reg = _pub_registry()
        before = reg.observe_all().runtime_count
        ob = AuditIntelligenceObserver(reg, _audit_registry())
        ob.report(); ob.audits(); ob.correlation(); ob.compliance(); ob.search("a")
        after = reg.observe_all().runtime_count
        assert before == after == 1
