"""SAM Cognitive Runtime (Phase XIX).

Menyatukan output seluruh runtime (Mission, Agent, Skill, Memory, Knowledge)
menjadi representasi kognitif deterministik siap dikonsumsi reasoning engine
masa depan. Bukan LLM, bukan AI, tidak melakukan inferensi — hanya menyusun
Cognitive Context secara deterministik.

Folder lama `src/sam/cognitive/` (Goal/Autonomy/Budget/Healing, Sprint 24)
TIDAK disentuh; fase ini membangun `cognitive_runtime/` paralel.
"""
from .dashboard import ExecutionCard
from .foundation import (
    CognitiveDescriptor,
    CognitiveCapability,
    CognitiveContract,
    CognitiveMetadata,
    CognitiveRegistry,
    ConversationCognitiveBridge,
    DashboardCognitiveBridge,
)
from .context import (
    CognitiveContext,
    CognitiveSnapshot,
    CognitiveScope,
    VALID_SCOPES,
    CognitiveReference,
    CognitiveValidator,
    CognitiveValidation,
    ConversationContextBridge,
    DashboardContextBridge,
)

__all__ = [
    "ExecutionCard",
    "CognitiveDescriptor",
    "CognitiveCapability",
    "CognitiveContract",
    "CognitiveMetadata",
    "CognitiveRegistry",
    "ConversationCognitiveBridge",
    "DashboardCognitiveBridge",
    "CognitiveContext",
    "CognitiveSnapshot",
    "CognitiveScope",
    "VALID_SCOPES",
    "CognitiveReference",
    "CognitiveValidator",
    "CognitiveValidation",
    "ConversationContextBridge",
    "DashboardContextBridge",
]
