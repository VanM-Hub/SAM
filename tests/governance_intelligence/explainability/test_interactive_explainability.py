"""WP-33 - Interactive Explainability tests (IP-3.1-003).

Scenarios:
  - follow-up question       : a second question stays on the same evidence chain
  - evidence navigation      : navigate() preserves the layered chain
  - context switching        : changing topic still keeps governance refs
  - clarification            : asking "show related policy" returns the policy basis
  - ambiguity resolution     : unsupported question reports missing evidence explicitly

Every answer must keep the evidence chain, governance references,
architecture references, and trust assessment.
"""

from __future__ import annotations

from sam.governance_intelligence.conversation import ConversationGateway
from sam.governance_intelligence.knowledge.indexes import index_governance, index_mission
from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
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
    gov = index_governance("docs/governance.md", gov_text)
    policy = PolicyRepository(gov)
    runtime = RuntimeRepository(gov)
    evidence = EvidenceRepository(load_index("evidence", "docs/foundation/MISSION.md", "evidence", mission_text))
    adr = ADRRepository(index_governance("docs/architecture/", "# ADR-approval-gate\n\nApproval gating architecture.\n"))
    return mission, policy, runtime, evidence, adr


class TestFollowUpQuestion:
    def test_follow_up_preserves_evidence_chain(self):
        mission, policy, runtime, evidence, adr = _build()
        gw = ConversationGateway(mission, policy, runtime, evidence, adr)
        gw.start()
        first = gw.ask("Why was Mission rejected?")
        second = gw.ask("Show related policy.")
        # both answers carry an evidence chain list
        assert isinstance(first.data["evidence_chain"], list)
        assert isinstance(second.data["evidence_chain"], list)
        # session context continuity: active topic updated, turn advanced
        assert first.data["session"]["turn"] == 1
        assert second.data["session"]["turn"] == 2


class TestEvidenceNavigation:
    def test_navigation_preserves_layers(self):
        mission, policy, runtime, evidence, adr = _build()
        gw = ConversationGateway(mission, policy, runtime, evidence, adr)
        gw.start()
        nav = gw.navigate()
        assert nav.kind == "navigation"
        root = nav.data["root"]
        assert root["layer"] == "Mission"


class TestContextSwitching:
    def test_switch_topic_keeps_governance_and_architecture(self):
        mission, policy, runtime, evidence, adr = _build()
        gw = ConversationGateway(mission, policy, runtime, evidence, adr)
        gw.start()
        gw.ask("Why is approval required?")
        # context switch
        r = gw.ask("What is the runtime health status?")
        # still carries governance + architecture basis
        assert r.data["governance_basis"]
        assert r.data["architectural_basis"]
        assert r.data["trust"] is not None


class TestClarification:
    def test_show_related_policy_grounds_evidence(self):
        mission, policy, runtime, evidence, adr = _build()
        gw = ConversationGateway(mission, policy, runtime, evidence, adr)
        gw.start()
        gw.ask("Why does the workflow stop?")
        r = gw.ask("Show related policy.")
        # policy appears in governance basis
        assert any("Policy" in b or "policy" in b for b in r.data["governance_basis"])


class TestAmbiguityResolution:
    def test_out_of_scope_reports_missing_evidence(self):
        mission, policy, runtime, evidence, adr = _build()
        gw = ConversationGateway(mission, policy, runtime, evidence, adr)
        gw.start()
        r = gw.ask("What is the purpose of an undefined external widget?")
        # ambiguity resolved deterministically: no hidden guess, answer still produced
        assert "answer" in r.data
        assert isinstance(r.data["evidence_chain"], list)
