"""WP-29 - Context Memory / Session Context (IP-3.1-003).

A per-session conversational context, NOT runtime memory and NOT governance
state. It tracks what the operator is currently exploring so follow-up
questions can stay on-topic deterministically.

Context Memory stores:
    active_topic   : the current subject/question being explored
    active_mission : the mission the session is focused on
    active_workflow: the workflow under discussion
    active_evidence: evidence currently referenced

Guarantees:
  - session-bound: the context exists only for the lifetime of a conversation
  - never persists mutable governance state
  - when the session ends the context is discarded
  - deterministic: same inputs produce identical public projections
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import List, Optional


@dataclass(frozen=True)
class SessionContext:
    """Immutable snapshot of the active session context (WP-29)."""

    active_topic: Optional[str] = None
    active_mission: Optional[str] = None
    active_workflow: Optional[str] = None
    active_evidence: List[str] = field(default_factory=list)
    turn: int = 0

    def with_updates(
        self,
        topic: Optional[str] = None,
        mission: Optional[str] = None,
        workflow: Optional[str] = None,
        evidence: Optional[List[str]] = None,
    ) -> "SessionContext":
        """Return a NEW context with the given fields updated (immutable)."""
        return replace(
            self,
            active_topic=topic if topic is not None else self.active_topic,
            active_mission=mission if mission is not None else self.active_mission,
            active_workflow=workflow if workflow is not None else self.active_workflow,
            active_evidence=list(evidence) if evidence is not None else list(self.active_evidence),
            turn=self.turn + 1,
        )

    def public_dict(self) -> dict:
        return {
            "active_topic": self.active_topic,
            "active_mission": self.active_mission,
            "active_workflow": self.active_workflow,
            "active_evidence": list(self.active_evidence),
            "turn": self.turn,
        }


class SessionContextStore:
    """WP-29 in-process, session-scoped context holder.

    A new conversation creates a fresh context. The store holds ONLY the
    session context (active_topic / mission / workflow / evidence) - it never
    stores, mutates, or caches governance or runtime state.
    """

    def __init__(self) -> None:
        self._context: SessionContext = SessionContext()

    def start(self) -> SessionContext:
        """Begin a new conversation with an empty context."""
        self._context = SessionContext()
        return self._context

    def get(self) -> SessionContext:
        return self._context

    def update(self, **kwargs) -> SessionContext:
        self._context = self._context.with_updates(**kwargs)
        return self._context

    def end(self) -> None:
        """Discard the session context (session is over)."""
        self._context = SessionContext()

    @property
    def is_active(self) -> bool:
        return self._context.turn > 0 or self._context.active_topic is not None
