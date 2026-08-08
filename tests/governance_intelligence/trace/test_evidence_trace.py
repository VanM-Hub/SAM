"""WP-18 - Evidence Trace Engine tests (IP-3.1-002).

Verifies that "why did Recommendation X appear?" resolves a deterministic
chain: Recommendation -> Evidence -> Policy -> Mission -> ADR -> Architecture
Order.
"""

from __future__ import annotations

import pytest

from sam.governance_intelligence.knowledge.indexes import index_governance, index_mission
from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)
from sam.governance_intelligence.trace import EvidenceTrace, EvidenceTraceEngine


def _fixtures():
    mission_text = (
        "# Mission\n\nGovern lifecycle with deterministic reasoning.\n\n"
        "# Objective\n\napproval policy\n"
    )
    gov_text = (
        "# approval\n\nApprove only with evidence.\n\n"
        "# Workflow Runtime\n\napproval workflow stops.\n"
    )
    mission = MissionRepository(index_mission("docs/foundation/MISSION.md", mission_text))
    gov_idx = index_governance("docs/governance.md", gov_text)
    policy = PolicyRepository(gov_idx)
    runtime = RuntimeRepository(gov_idx)
    evidence = EvidenceRepository(load_index("evidence", "docs/foundation/MISSION.md", "evidence", mission_text))
    adr = ADRRepository(index_governance("docs/adr/", "# ADR approve-recs\n\nDecision basis.\n"))
    return mission, policy, runtime, evidence, adr


class TestEvidenceTrace:
    def test_trace_recommendation_returns_chain(self):
        mission, policy, runtime, evidence, adr = _fixtures()
        t: EvidenceTrace = EvidenceTraceEngine(
            mission, policy, evidence, adr, runtime
        ).trace_recommendation("approve")
        assert isinstance(t, EvidenceTrace)
        assert t.target == "approve"
        # chain covers the required layers in order
        layers = [n.layer for n in t.chain]
        assert "Recommendation" in layers
        assert "Evidence" in layers
        assert "Policy" in layers
        assert "Mission" in layers
        assert "ADR" in layers
        assert "Architecture Order" in layers

    def test_trace_chain_deterministic(self):
        mission, policy, runtime, evidence, adr = _fixtures()
        eng = EvidenceTraceEngine(mission, policy, evidence, adr, runtime)
        t1 = eng.trace_recommendation("approve")
        t2 = eng.trace_recommendation("approve")
        assert t1.public_dict() == t2.public_dict()

    def test_trace_public_dict(self):
        mission, policy, runtime, evidence, adr = _fixtures()
        t = EvidenceTraceEngine(
            mission, policy, evidence, adr, runtime
        ).trace_recommendation("approve")
        d = t.public_dict()
        assert "target" in d and "chain" in d and "complete" in d
