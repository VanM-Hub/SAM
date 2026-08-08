"""gateway / recommendation / compliance — WP-10/12/13 tests (IP-3.1-001)."""

from pathlib import Path

from sam.governance_intelligence.compliance import compliance_check
from sam.governance_intelligence.gateway import IntelligenceGateway
from sam.governance_intelligence.knowledge.indexes import index_governance, index_mission
from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.repository import (
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)
from sam.governance_intelligence.reasoning.engine import keyword_rule


def _make_gateway(mission_content):
    mission = MissionRepository(index_mission("m.md", mission_content))
    ev = EvidenceRepository(load_index("e", "m.md", "evidence", mission_content))
    gov = index_governance("g.md", "# Policy Approval\nApprove only with evidence.\n# Workflow Runtime\nx\n")
    pol = PolicyRepository(gov)
    runtime = RuntimeRepository(gov)
    return IntelligenceGateway(mission, pol, runtime, ev)


_MD_MISSION = "# Objective\n\nDo things.\n\n# Scope\n\nScoped.\n"


def test_gateway_ask_and_trace(evidence_repo):
    from sam.governance_intelligence.knowledge.indexes import index_mission
    mission = MissionRepository(index_mission("m.md", _MD_MISSION))
    pol = PolicyRepository(index_governance("g.md", "# Policy\nx"))
    runtime = RuntimeRepository(index_governance("g.md", "# Runtime\nx"))
    gw = IntelligenceGateway(mission, pol, runtime, evidence_repo)
    r = gw.ask("Objective")
    assert r.kind == "answer"
    t = gw.trace("Objective")
    assert t.kind == "trace"
    assert isinstance(t.data["citations"], list)


def test_gateway_recommendation_requires_evidence():
    gw = _make_gateway(_MD_MISSION)
    r = gw.recommend("go", [("objective", keyword_rule("objective"))])
    assert r.kind == "recommendation"
    assert r.data["has_evidence"] is True


def test_gateway_explain():
    gw = _make_gateway(_MD_MISSION)
    r = gw.explain("assess", [("objective", keyword_rule("objective"))])
    assert r.kind == "explanation"
    assert "confidence" in r.data


def test_gateway_recommendation_no_evidence_no_emit():
    gw = _make_gateway(_MD_MISSION)
    r = gw.recommend("go", [("none", keyword_rule("zzz-absent"))])
    # directive: no recommendation without evidence
    assert r.data["has_evidence"] is False
    assert r.data["confidence"] == 0.0


def test_compliance_passes(mission_content):
    # WP-13 (5 forbidden) + WP-24 (3 required positive) = 8 checks.
    rep = compliance_check(Path("src/sam/governance_intelligence"))
    assert rep.passed() is True
    assert len(rep.checks) == 8
    names = {c.name for c in rep.checks}
    assert {
        "no runtime mutation", "no authority", "no orchestration",
        "no execution", "no approval",
        "deterministic reasoning", "explainable output",
        "evidence-backed recommendation",
    } <= names
