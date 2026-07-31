"""LLM Common Adapter — adapter generik LLM (Program A, Sprint 229).

Sprint 229 — LLM Common Adapter (OP-2402, Program A).
Adapter umum yang dipakai semua penyedia LLM (OpenAI, Anthropic, Gemini,
DeepSeek, Ollama, dst) melalui interface yang sama. Tidak ada provider-specific
logic di sini — setiap penyedia mengimplementasikan map generik ini.

Prinsip:
- Immutable DTO.
- Preview -> Approval -> Execute.
- External calls default = 0 (preview tidak pernah memanggil network).
- Tidak ada network import sama sekali di lapisan ini.
"""
from .llm_request import LLMRequest, LLMRequestBuilder
from .llm_response import LLMResponse, LLMResponseBuilder
from .llm_message import LLMMessage, LLMRole, LLMMessageBuilder
from .llm_model import LLMModel, LLMModelCapability
from .llm_capability import LLMCapability, LLMCapabilitySet
from .llm_session import LLMSession, LLMSessionState
from .llm_adapter import LLMAdapter, LLMAdapterResult

__all__ = [
    "LLMRequest",
    "LLMRequestBuilder",
    "LLMResponse",
    "LLMResponseBuilder",
    "LLMMessage",
    "LLMRole",
    "LLMMessageBuilder",
    "LLMModel",
    "LLMModelCapability",
    "LLMCapability",
    "LLMCapabilitySet",
    "LLMSession",
    "LLMSessionState",
    "LLMAdapter",
    "LLMAdapterResult",
]
