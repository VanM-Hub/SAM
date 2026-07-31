"""Provider Runtime Integration (Program A, Sprint 235).

Sprint 235 — OpenClaw Runtime Integration (OP-2408).
Menghubungkan semua adapter LLM (Program A) menjadi satu runtime terpadu,
kompatibel dengan pola runtime OpenClaw. Preview-only, external_calls=0.

Prinsip:
- Semua provider LLM melalui LLMAdapter (interface yang sama).
- Tidak menyentuh legacy Runtime OpenClaw (src/sam/openclaw/).
- Immutable DTO + builder deterministic + preview->approval->execute.
"""
from .runtime_integration import (
    ProviderIntegration,
    ProviderIntegrationResult,
    ProviderRuntimeManifest,
)
from .openclaw_gateway import OpenClawGateway

__all__ = [
    "ProviderIntegration",
    "ProviderIntegrationResult",
    "ProviderRuntimeManifest",
    "OpenClawGateway",
]
