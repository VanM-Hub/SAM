"""Sprint 272 + ENG-G-001 · G1 — Presentation Layer: conversation capability.

Bridge lama (Sprint 272) tetap untuk metadata snapshot read-only.
Struktur G1 menambah ViewModel, Command, dan UI Composition sebagai
fondasi Presentation Capability (module/ViewModel/Command/UI composition).
Capability dihubungkan ke RuntimeService pada G2+ (via jalur
runtime_service.api yang sudah ada); di sini TIDAK ada business logic
dan TIDAK ada akses langsung ke Runtime/Registry/Provider/Connector.
"""
from .bridge import ConversationBridge, ConversationBridgeSnapshot
from .viewmodel import ConversationViewModel
from .commands import ConversationCommand, ConversationCommandSpec
from .composition import ConversationComposition, compose_conversation
from .wiring import ConversationRuntimeWiring, wire_conversation_runtime
from .integration import ConversationResult, ConversationIntegration

__all__ = [
    "ConversationBridge",
    "ConversationBridgeSnapshot",
    "ConversationViewModel",
    "ConversationCommand",
    "ConversationCommandSpec",
    "ConversationComposition",
    "compose_conversation",
    "ConversationRuntimeWiring",
    "wire_conversation_runtime",
    "ConversationResult",
    "ConversationIntegration",
]
