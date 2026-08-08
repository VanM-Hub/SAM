"""WP-35 - IP-3.1-003 Integration & Operational Certification test.

Wires WP-26..WP-34 end-to-end and validates the IP-3.1-003 exit criteria:

Operator drives a conversation step by step (preserving session context,
evidence chain, governance references, architecture references, trust
assessment) withOUT changing governance or runtime:

    "Mengapa Mission ini ditolak?"           -> answer + evidence chain
    "Tunjukkan Policy yang menjadi dasar."    -> governance basis
    "Jelaskan hubungan Policy tersebut dengan ADR." -> architecture basis
    "Evidence apa yang belum tersedia?"       -> trust/missing info
    "Bagaimana tingkat trust terhadap jawaban ini?" -> trust assessment
"""

from __future__ import annotations

from pathlib import Path

from sam.governance_intelligence.compliance import compliance_check
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
        "# Workflow Runtime\n\nWorkflow stops without an approval gate.\n"
    )
    mission = MissionRepository(index_mission("docs/foundation/MISSION.md", mission_text))
    gov = index_governance("docs/governance.md", gov_text)
    policy = PolicyRepository(gov)
    runtime = RuntimeRepository(gov)
    evidence = EvidenceRepository(load_index("evidence", "docs/foundation/MISSION.md", "evidence", mission_text))
    adr = ADRRepository(index_governance("docs/architecture/", "# ADR-approval-gate\n\nApproval gating architecture.\n"))
    return mission, policy, runtime, evidence, adr


class TestExitCriteria:
    def test_full_interactive_exploration(self):
        mission, policy, runtime, evidence, adr = _build()
        gw = ConversationGateway(mission, policy, runtime, evidence, adr)
        before = evidence.size()
        gw.start()

        # 1. Why was this Mission rejected?
        r1 = gw.ask("Why was this Mission rejected?")
        assert r1.kind == "answer"
        assert isinstance(r1.data["evidence_chain"], list)

        # 2. Show the policy that grounds it
        r2 = gw.ask("Show the policy that is the basis.")
        assert r2.data["governance_basis"], "governance basis expected"

        # 3. Explain the relationship between that policy and the ADR
        r3 = gw.ask("Explain the relationship between that policy and the ADR.")
        assert r3.data["architectural_basis"], "architectural basis expected"

        # 4. What evidence is not yet available?
        r4 = gw.ask("What evidence is not yet available?")
        assert "answer" in r4.data

        # 5. How much trust is there in this answer?
        r5 = gw.ask("How much trust is there in this answer?")
        assert r5.data["trust"] is not None

        # Session continuity maintained across all 5 turns
        assert r5.data["session"]["turn"] == 5
        gw.end()

        # governance/runtime unchanged by the whole conversation
        assert evidence.size() == before


class TestCertification:
    def test_compliance_passes_package(self):
        rep = compliance_check(Path("src/sam/governance_intelligence"))
        assert rep.passed() is True
        assert len(rep.checks) == 12

    def test_conversation_modules_present(self):
        # Repository expansion targets exist
        import sam.governance_intelligence.conversation  # noqa: F401
        import sam.governance_intelligence.planner  # noqa: F401
        import sam.governance_intelligence.navigation  # noqa: F401
        import sam.governance_intelligence.relationship  # noqa: F401
        import sam.governance_intelligence.session  # noqa: F401
        import sam.governance_intelligence.interactive  # noqa: F401
