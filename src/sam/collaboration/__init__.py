"""SAM Collaboration — Sprint 26 Fase 2 & 3.

Multi-Agent Collaboration: Agent Communication Protocol,
Task Delegation, and Collaboration Workflows.
"""

from .agent import Agent, AGENT_STATUSES
from .registry import AgentRegistry
from .message import Message, MessageType, MessagePriority, MESSAGE_STATUSES
from .protocol import AgentProtocol
from .delegation import (
    DelegationStatus,
    DelegationRequest,
    DelegationManager,
)
from .workflow import (
    CollaborationWorkflow,
    CollaborationWorkflowManager,
    WORKFLOW_STATUSES,
)

__all__ = [
    "Agent",
    "AGENT_STATUSES",
    "AgentRegistry",
    "Message",
    "MessageType",
    "MessagePriority",
    "MESSAGE_STATUSES",
    "AgentProtocol",
    "DelegationStatus",
    "DelegationRequest",
    "DelegationManager",
    "CollaborationWorkflow",
    "CollaborationWorkflowManager",
    "WORKFLOW_STATUSES",
]
