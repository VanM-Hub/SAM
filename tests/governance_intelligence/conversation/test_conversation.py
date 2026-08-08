"""WP-26/29/30/31/32 - Interactive Conversation & Context Memory tests
(IP-3.1-003).

Covers:
  WP-26 Interactive Query Engine (dialogue, deterministic, no governance memory)
  WP-29 Session Context Memory (session-scoped, discarded on end)
  WP-30 Question Planner (strategy only, no reasoning)
  WP-31 Multi-step Reasoning Pipeline (deterministic)
  WP-32 Governance Conversation API (start/ask/trace/end)
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
from sam.governance_intelligence.planner import QuestionPlanner
from sam.governance_intelligence.session import SessionContext, SessionContextStore


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


class TestSessionContext:
    def test_start_creates_empty_context(self):
        store = SessionContextStore()
        ctx = store.start()
        assert ctx.turn == 0
        assert ctx.active_topic is None

    def test_update_returns_new_context_immutable(self):
        store = SessionContextStore()
        store.start()
        c1 = store.get()
        c2 = store.update(topic="approval", evidence=["e1"])
        assert c1.active_topic is None  # original unchanged (immutable)
        assert c2.active_topic == "approval"
        assert c2.active_evidence == ["e1"]
        assert c2.turn == 1

    def test_end_discards_context(self):
        store = SessionContextStore()
        store.start()
        store.update(topic="approval")
        store.end()
        assert store.get().active_topic is None


class TestQuestionPlanner:
    def test_plan_is_strategy_only(self):
        plan = QuestionPlanner().plan("Which policy caused the workflow to stop?")
        # planner composes requirements, does NOT reason
        assert "policy" in plan.required_knowledge or plan.required_knowledge
        assert plan.reasoning_steps
        assert "reason" in plan.reasoning_steps

    def test_plan_deterministic(self):
        p1 = QuestionPlanner().plan("Why was mission rejected?")
        p2 = QuestionPlanner().plan("Why was mission rejected?")
        assert p1.public_dict() == p2.public_dict()


class TestConversationAPI:
    def test_start_ask_end_flow(self):
        mission, policy, runtime, evidence, adr = _build()
        gw = ConversationGateway(mission, policy, runtime, evidence, adr)
        s = gw.start()
        assert s.kind == "session"
        assert s.data["action"] == "started"

        a = gw.ask("Why was mission rejected?")
        assert a.kind == "answer"
        assert a.data["question"]
        assert "answer" in a.data
        assert a.data["plan"]["reasoning_steps"]
        # evidence chain preserved across the answer
        assert isinstance(a.data["evidence_chain"], list)

        e = gw.end()
        assert e.kind == "session"
        assert e.data["action"] == "ended"

    def test_trace_returns_chain(self):
        mission, policy, runtime, evidence, adr = _build()
        gw = ConversationGateway(mission, policy, runtime, evidence, adr)
        gw.start()
        gw.ask("Why is approval required?")
        t = gw.trace()
        assert t.kind == "trace"
        assert "chain" in t.data

    def test_session_context_carried_between_turns(self):
        mission, policy, runtime, evidence, adr = _build()
        gw = ConversationGateway(mission, policy, runtime, evidence, adr)
        gw.start()
        f = gw.ask("Why is approval required?")
        assert f.data["session"]["active_topic"] == "Why is approval required?"
        f2 = gw.ask("Which policy causes this?")
        assert f2.data["session"]["turn"] == 2

    def test_conversation_does_not_mutate_governance(self):
        from sam.governance_intelligence.knowledge.repository import EvidenceRepository

        mission, policy, runtime, evidence, adr = _build()
        before_repo = evidence.size()
        gw = ConversationGateway(mission, policy, runtime, evidence, adr)
        gw.start()
        gw.ask("Why was Mission rejected?")
        gw.ask("Show related policy.")
        gw.ask("Explain the relationship to the ADR.")
        gw.end()
        # repositories unchanged - conversation only reads
        assert evidence.size() == before_repo


class TestInteractiveDeterministic:
    def test_same_question_same_answer(self):
        mission, policy, runtime, evidence, adr = _build()
        gw1 = ConversationGateway(mission, policy, runtime, evidence, adr)
        gw2 = ConversationGateway(mission, policy, runtime, evidence, adr)
        gw1.start(); gw2.start()
        r1 = gw1.ask("Which policy causes concern?")
        r2 = gw2.ask("Which policy causes concern?")
        assert r1.public_dict()["data"]["answer"] == r2.public_dict()["data"]["answer"]
