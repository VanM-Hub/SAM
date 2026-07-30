"""SAM Activation Runtime — Phase VIII.

Menerima Operational Plan dari Operational Brain, menghasilkan Activation Package.
TIDAK MENGEKSEKUSI. Hanya preview & package.
"""

from sam.activation.activation_context import ActivationContext
from sam.activation.activation_request import ActivationRequest
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_registry import ActivationRegistry, ActivationSnapshot
from sam.activation.activation_builder import ActivationBuilder
from sam.activation.activation_draft import ActivationDraft
from sam.activation.conversation_activation import ConversationActivation
from sam.activation.dashboard_activation import DashboardActivation, ActivationCard
from sam.activation.runtime import ActivationRuntime

__all__ = [
    "ActivationContext",
    "ActivationRequest",
    "ActivationCandidate",
    "ActivationRegistry", "ActivationSnapshot",
    "ActivationBuilder",
    "ActivationDraft",
    "ConversationActivation",
    "DashboardActivation", "ActivationCard",
    "ActivationRuntime",
]
