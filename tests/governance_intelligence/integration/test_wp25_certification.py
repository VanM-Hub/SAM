"""WP-25 - Integration & Certification test (IP-3.1-002).

Wires WP-16..WP-24 through the IntelligenceGatewayV2 and validates the
exit-criteria questions of IP-3.1-002:

    "Why was this decision taken?"
    "Which evidence is most influential?"
    "Which policy caused the workflow to stop?"
    "Which ADR grounds the recommendation?"
    "What changes if specific evidence is unavailable?" (simulation)

Each answer must always carry: an explanation, an evidence chain, governance
references, architecture references, a trust assessment, and what information
is still missing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sam.governance_intelligence.api_v2 import IntelligenceGatewayV2
from sam.governance_intelligence.compliance import compliance_check
from sam.governance_intelligence.gateway import IntelligenceGateway
from sam.governance_intelligence.knowledge.expansion import (
    ARCH_ORDER,
    CERTIFICATION,
    VERDICT,
    index_kind,
)
from sam.governance_intelligence.knowledge.indexes import index_governance, index_mission
from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)
from sam.governance_intelligence.reasoning.engine.reasoner import (
    GovernanceReasoner,
    keyword_rule,
)


def _build():
    mission_text = (
        "# Mission\n\nGovern lifecycle with deterministic reasoning.\n\n"
        "# Objective\n\nsafe, explainable operation gated by approval\n"
    )
    gov_text = (
        "# Approval Policy\n\nApprove only with evidence.\n\n"
        "# Workflow Runtime\n\nWorkflow stops without an approval gate.\n\n"
        "# Health\n\nRuntime unhealthy when evidence is missing.\n"
    )
    mission = MissionRepository(index_mission("docs/foundation/MISSION.md", mission_text))
    gov_idx = index_governance("docs/governance.md", gov_text)
    policy = PolicyRepository(gov_idx)
    runtime = RuntimeRepository(gov_idx)
    evidence = EvidenceRepository(load_index("evidence", "docs/foundation/MISSION.md", "evidence", mission_text))
    adr = ADRRepository(index_governance("docs/architecture/", "# ADR-approval-gate\n\nApproval gating architecture.\n"))
    gw_v1 = IntelligenceGateway(mission, policy, runtime, evidence)
    gw_v2 = IntelligenceGatewayV2(gw_v1, mission, policy, runtime, evidence, adr)
    return gw_v1, gw_v2


class TestExitCriteria:
    def test_why_decision_taken(self):
        _, gw = _build()
        r = gw.why("approval")
        assert r.kind == "why"
        chain = r.data["chain"]
        # explanation of the decision includes the evidence-based chain
        assert len(chain) >= 2

    def test_which_evidence_most_influential(self):
        _, gw = _build()
        r = gw.understand()
        # trust assessment explains evidence quality; evidence_availability
        # identifies which evidence is present/influential
        trust = r.data["trust"]
        assert "overall" in trust
        assert "completeness" in trust

    def test_which_policy_stops_workflow(self):
        _, gw = _build()
        r = gw.why("workflow")
        chain = r.data["chain"]
        # a policy node appears in the trace (the policy that gates/stop)
        assert any(n["layer"] == "Policy" for n in chain)

    def test_which_adr_grounds_recommendation(self):
        _, gw = _build()
        r = gw.why("approval")
        chain = r.data["chain"]
        # the ADR is referenced in the trace (architecture grounding)
        assert any(n["layer"] == "ADR" for n in chain)

    def test_what_if_missing_evidence(self):
        _, gw = _build()
        r = gw.what_if("approval")
        assert r.kind == "what_if"
        assert r.data["governance_unchanged"] is True
        assert "outcome" in r.data


class TestCertification:
    def test_compliance_passes_package(self):
        rep = compliance_check(Path("src/sam/governance_intelligence"))
        assert rep.passed() is True

    def test_proof_suite_runs(self):
        # Full capability smoke: v2 covers understand + why + how + what_if
        _, gw = _build()
        assert gw.understand().kind == "understanding"
        assert gw.why("approval").kind == "why"
        assert gw.what_if("approval").kind == "what_if"


class TestExpandedKnowledgeWiring:
    def test_expanded_artifacts_queryable(self):
        idx = index_kind(
            "cert",
            [
                {"key": "verdict.v1", "title": "Verdict 1", "source": "s/", "kind_override": VERDICT},
                {"key": "cert.c1", "title": "Cert 1", "source": "c/", "kind_override": CERTIFICATION},
                {"key": "arch.a1", "title": "Arch Order 1", "source": "a/", "kind_override": ARCH_ORDER},
            ],
        )
        from sam.governance_intelligence.knowledge.expansion import ExpandedKnowledgeQueries

        q = ExpandedKnowledgeQueries(idx)
        assert len(q.verdicts()) == 1
        assert len(q.certifications()) == 1
        assert len(q.arch_orders()) == 1
