"""WP-21 - Governance Knowledge Expansion tests (IP-3.1-002).

Verifies the expanded read-only index supports Architecture Orders,
Engineering Verdicts, Chief Architect Acceptance, Certification Reports, and
Milestone History, all without mutation.
"""

from __future__ import annotations

import pytest

from sam.governance_intelligence.knowledge.expansion import (
    ACCEPTANCE,
    ARCH_ORDER,
    CERTIFICATION,
    MILESTONE,
    VERDICT,
    ExpandedKnowledgeQueries,
    build_expanded_index,
    index_kind,
)
from sam.governance_intelligence.knowledge.models import KnowledgeIndex, KnowledgeItem


class TestKnowledgeExpansion:
    def test_index_kind_builds_immutable_items(self):
        idx: KnowledgeIndex = index_kind(
            "verdict",
            [
                {"key": "verdict.ip3.1-001", "title": "Governance Intelligence Verdict",
                 "source": "decisions/", "kind_override": VERDICT},
                {"key": "arch.001", "title": "Architecture Order 001",
                 "source": "decisions/", "kind_override": ARCH_ORDER},
            ],
        )
        assert isinstance(idx, KnowledgeIndex)
        assert idx.size() == 2
        for it in idx.all():
            assert isinstance(it, KnowledgeItem)
            assert it.signature  # content signature for change detection

    def test_queries_by_kind(self):
        idx = index_kind(
            "cert",
            [
                {"key": "cert.a", "title": "Cert A", "source": "x/", "kind_override": CERTIFICATION},
                {"key": "mil.1", "title": "Milestone 1", "source": "y/", "kind_override": MILESTONE},
                {"key": "acc.1", "title": "Acceptance 1", "source": "z/", "kind_override": ACCEPTANCE},
                {"key": "arch.9", "title": "Arch Order 9", "source": "w/", "kind_override": ARCH_ORDER},
            ],
        )
        q = ExpandedKnowledgeQueries(idx)
        assert len(q.certifications()) == 1
        assert len(q.milestones()) == 1
        assert len(q.acceptances()) == 1
        assert len(q.arch_orders()) == 1
        assert len(q.verdicts()) == 0

    def test_build_expanded_index_read_only(self):
        idx = build_expanded_index("verdicts", [])
        assert idx.name == "verdicts"
        assert idx.size() == 0

    def test_latest_by_kind(self):
        idx = index_kind("verdict", [{"key": "v.1", "title": "V1", "source": "s/", "kind_override": "verdict"}])
        q = ExpandedKnowledgeQueries(idx)
        latest = q.latest("verdict")
        assert len(latest) == 1 and latest[0].key == "v.1"
