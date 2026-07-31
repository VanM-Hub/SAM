"""Provider Interface — kontrak bersama semua provider (Program A, Sprint 228).

Sprint 228 — Provider Interface (OP-2401, Program A — External Connector).
Interface generik yang menjadi satu-satunya kontrak antara Connector/Provider Runtime
dengan semua provider (OpenAI, Anthropic, Gemini, DeepSeek, Ollama, OpenClaw, dll).

Prinsip Program A:
- Semua provider melalui interface yang sama (tidak ada provider-specific logic di
  Agent/Mission/Workflow).
- Semua provider bersifat plug-in.
- Preview -> Approval -> Execute.
- Default external_calls = 0 pada mode preview.
- Tidak membuat runtime baru; tidak mengubah Architecture v23.
"""
from .provider_request import (
    ProviderRequest,
    ProviderRequestBuilder,
)
from .provider_response import (
    ProviderResponse,
    ProviderResponseBuilder,
)
from .provider_error import ProviderError, ProviderErrorKind, ProviderException
from .provider_capability import (
    ProviderCapability,
    ProviderCapabilitySet,
    PROVIDER_CAPABILITY_KEYS,
)
from .provider_session import ProviderSession, ProviderSessionState
from .provider_factory import ProviderFactory, ProviderFactoryEntry
from .provider_registry import ProviderRegistry, ProviderRegistryEntry

__all__ = [
    # request
    "ProviderRequest",
    "ProviderRequestBuilder",
    # response
    "ProviderResponse",
    "ProviderResponseBuilder",
    # error
    "ProviderError",
    "ProviderErrorKind",
    "ProviderException",
    # capability
    "ProviderCapability",
    "ProviderCapabilitySet",
    "PROVIDER_CAPABILITY_KEYS",
    # session
    "ProviderSession",
    "ProviderSessionState",
    # factory
    "ProviderFactory",
    "ProviderFactoryEntry",
    # registry
    "ProviderRegistry",
    "ProviderRegistryEntry",
]
