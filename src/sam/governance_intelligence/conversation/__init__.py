"""WP-26 + WP-32 - Interactive Query Engine & Governance Conversation API
(IP-3.1-003).

Interactive Query Engine (WP-26): dialogue in steps. Operator asks, SAM
answers, operator asks a follow-up ("show related policy"), SAM returns the
evidence. Output is deterministic; there is no conversational memory that
mutates governance.

Governance Conversation API (WP-32): a gateway exposing
    conversation.start()      : begin a new session, reset session context
    conversation.ask()        : run one deterministic interactive turn
    conversation.trace()      : return the full evidence trace for the topic
    conversation.end()        : close the session, discard session context

Conversation NEVER changes governance. Only session context is stored; it is
discarded when the session ends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sam.governance_intelligence.interactive import InteractivePipeline, InteractiveTurn
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)
from sam.governance_intelligence.navigation import EvidenceNavigationEngine, EvidenceNavigationTree
from sam.governance_intelligence.relationship import (
    GovernanceRelationshipEngine,
    RelationshipGraph,
)
from sam.governance_intelligence.session import SessionContext, SessionContextStore
from sam.governance_intelligence.trace import EvidenceTrace, EvidenceTraceEngine


@dataclass(frozen=True)
class ConversationReply:
    kind: str  # 'answer' | 'trace' | 'navigation' | 'relationship' | 'session'
    data: dict

    def public_dict(self) -> dict:
        return {"kind": self.kind, "data": self.data}


class ConversationGateway:
    """WP-32. Session-scoped, read-only, deterministic conversation gateway."""

    def __init__(
        self,
        mission: MissionRepository,
        policy: PolicyRepository,
        runtime: RuntimeRepository,
        evidence: EvidenceRepository,
        adr: ADRRepository,
        workflow: Optional[RuntimeRepository] = None,
    ) -> None:
        self._mission = mission
        self._policy = policy
        self._runtime = runtime
        self._evidence = evidence
        self._adr = adr
        self._workflow = workflow or runtime
        self._session = SessionContextStore()
        self._pipeline = InteractivePipeline(mission, policy, runtime, evidence, adr)
        self._trace = EvidenceTraceEngine(mission, policy, evidence, adr, runtime)
        self._nav = EvidenceNavigationEngine(mission, self._workflow, policy, evidence, adr, runtime)
        self._rel = GovernanceRelationshipEngine(
            mission, self._workflow, policy, runtime, evidence, adr
        )

    # --- lifecycle ----------------------------------------------------------
    def start(self) -> ConversationReply:
        ctx = self._session.start()
        return ConversationReply(kind="session", data={"action": "started", "session": ctx.public_dict()})

    def end(self) -> ConversationReply:
        self._session.end()
        return ConversationReply(kind="session", data={"action": "ended"})

    # --- interactive turns --------------------------------------------------
    def ask(self, question: str) -> ConversationReply:
        ctx = self._session.get()
        turn = self._pipeline.run(question, ctx)
        self._session.update(
            topic=question,
            mission=turn.session.active_mission,
            workflow=turn.session.active_workflow,
            evidence=turn.session.active_evidence,
        )
        return ConversationReply(kind="answer", data=turn.public_dict())

    def trace(self, topic: Optional[str] = None) -> ConversationReply:
        ctx = self._session.get()
        key = topic or ctx.active_topic or ""
        trace = self._trace.trace_recommendation(key if key else "decision")
        return ConversationReply(kind="trace", data=trace.public_dict())

    # --- exploration (WP-27 / WP-28) ----------------------------------------
    def navigate(self) -> ConversationReply:
        tree = self._nav.build()
        return ConversationReply(kind="navigation", data=tree.public_dict())

    def relationship(self) -> ConversationReply:
        graph = self._rel.build()
        return ConversationReply(kind="relationship", data=graph.public_dict())
