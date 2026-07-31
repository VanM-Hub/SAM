"""Agent State — lifecycle state machine (Phase XV, Sprint 158)."""
from .agent_state import (
    AgentState, CREATED, PREPARING, RUNNING, WAITING,
    COMPLETED, CANCELLED, FAILED, ALL_STATES, TERMINAL_STATES,
)
from .state_machine import StateMachine, TransitionResult
from .transition_rule import TransitionRule
from .transition_history import TransitionHistory, TransitionEvent
from .state_validator import StateValidator, StateValidation
from .conversation_state import ConversationStateBridge
from .dashboard_state import DashboardStateBridge

__all__ = [
    "AgentState",
    "CREATED", "PREPARING", "RUNNING", "WAITING",
    "COMPLETED", "CANCELLED", "FAILED", "ALL_STATES", "TERMINAL_STATES",
    "StateMachine",
    "TransitionResult",
    "TransitionRule",
    "TransitionHistory",
    "TransitionEvent",
    "StateValidator",
    "StateValidation",
    "ConversationStateBridge",
    "DashboardStateBridge",
]
