"""
ConversationSessionContext — In-memory session context for Conversation.

Tracks current mission, decision, recommendation, approval, and timeline
reference so SAM can answer follow-up questions like "kenapa?" and "apa solusinya?"
without LLM or persistence. Deterministic, session-scoped, zero dependencies.
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class SessionContext:
    """Tracks contextual state for a single conversation session.

    All fields are in-memory only. Reset on SAM start or session clear.
    """

    # ── Mission ────────────────────────────────────────────────────────
    current_mission_id: Optional[str] = None
    current_mission_name: Optional[str] = None
    current_mission_state: Optional[str] = None

    # ── Decision ───────────────────────────────────────────────────────
    last_decision_id: Optional[str] = None
    last_decision_title: Optional[str] = None
    last_decision_action: Optional[str] = None
    last_decision_risk: Optional[str] = None
    last_decision_confidence: Optional[float] = None

    # ── Recommendation ─────────────────────────────────────────────────
    last_recommendation_id: Optional[str] = None
    last_recommendation_text: Optional[str] = None
    last_recommendation_alternatives: list[str] = field(default_factory=list)

    # ── Approval ───────────────────────────────────────────────────────
    last_approval_id: Optional[str] = None
    last_approval_status: Optional[str] = None
    last_approval_reason: Optional[str] = None

    # ── Timeline ───────────────────────────────────────────────────────
    last_timeline_event_id: Optional[str] = None
    last_timeline_event_type: Optional[str] = None
    last_timeline_event_description: Optional[str] = None
    last_timeline_timestamp: Optional[str] = None

    # ── Verification / Execution ───────────────────────────────────────
    last_verification_result: Optional[str] = None
    last_execution_plan_id: Optional[str] = None
    last_execution_status: Optional[str] = None

    # ── Conversation ───────────────────────────────────────────────────
    last_query_type: Optional[str] = None  # "what_happened" | "why" | "solution" | ...
    last_response_text: Optional[str] = None

    # ── Internal ───────────────────────────────────────────────────────
    _query_count: int = 0

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def update_from_mission(self, mission: Any) -> None:
        """Mirror fields from a mission domain object (duck-typed)."""
        self.current_mission_id = getattr(mission, "mission_id", None) or getattr(mission, "id", None)
        self.current_mission_name = getattr(mission, "name", None)
        self.current_mission_state = getattr(mission, "state", None) or getattr(mission, "status", None)

    def update_from_decision(self, decision: Any) -> None:
        self.last_decision_id = getattr(decision, "decision_id", None) or getattr(decision, "id", None)
        self.last_decision_title = getattr(decision, "title", None) or getattr(decision, "description", None)
        self.last_decision_action = getattr(decision, "action", None)
        self.last_decision_risk = getattr(decision, "risk", None) or getattr(decision, "risk_level", None)
        self.last_decision_confidence = getattr(decision, "confidence", None)

    def update_from_recommendation(self, recommendation: Any) -> None:
        self.last_recommendation_id = getattr(recommendation, "recommendation_id", None) or getattr(recommendation, "id", None)
        self.last_recommendation_text = getattr(recommendation, "text", None) or getattr(recommendation, "description", None)
        alt = getattr(recommendation, "alternatives", None) or getattr(recommendation, "alternative_actions", None)
        if alt:
            self.last_recommendation_alternatives = [str(a) for a in alt]

    def update_from_approval(self, approval: Any) -> None:
        self.last_approval_id = getattr(approval, "approval_id", None) or getattr(approval, "id", None)
        self.last_approval_status = getattr(approval, "status", None)
        self.last_approval_reason = getattr(approval, "reason", None)

    def update_from_timeline_event(self, event: Any) -> None:
        self.last_timeline_event_id = getattr(event, "event_id", None) or getattr(event, "id", None)
        self.last_timeline_event_type = getattr(event, "event_type", None) or getattr(event, "type", None)
        self.last_timeline_event_description = getattr(event, "description", None)
        self.last_timeline_timestamp = getattr(event, "timestamp", None)

    def update_from_query(self, query_type: str, response_text: str) -> None:
        self.last_query_type = query_type
        self.last_response_text = response_text
        self._query_count += 1

    def clear_mission(self) -> None:
        self.current_mission_id = None
        self.current_mission_name = None
        self.current_mission_state = None

    def clear_session(self) -> None:
        """Full reset — back to blank session."""
        for field_name in self.__dataclass_fields__:
            if field_name.startswith("_"):
                continue
            default = self.__dataclass_fields__[field_name].default
            setattr(self, field_name, default)
        self._query_count = 0

    @property
    def has_context(self) -> bool:
        return self.current_mission_id is not None or self.last_decision_id is not None

    @property
    def summary(self) -> dict:
        return {
            "mission": f"{self.current_mission_name or '—'} ({self.current_mission_state or 'unknown'})"
            if self.current_mission_id else None,
            "last_decision": self.last_decision_title,
            "last_recommendation": self.last_recommendation_text,
            "last_approval_status": self.last_approval_status,
            "query_count": self._query_count,
        }


# Singleton holder for the active session context
_active_context: Optional[SessionContext] = None


def get_session_context() -> SessionContext:
    """Return the module-level session context singleton."""
    global _active_context
    if _active_context is None:
        _active_context = SessionContext()
    return _active_context


def reset_session_context() -> None:
    """Clear and reinitialize the session context."""
    global _active_context
    _active_context = SessionContext()
