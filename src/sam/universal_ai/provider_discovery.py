"""AI Provider Discovery - WP-06 (MISSION-5.1 / IP-5.1-001).

Discovery terhadap provider/model/capability yang terdaftar. Deterministik
dan registry-based; tidak ada implicit discovery yang menghasilkan execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .capability_model import AICapabilityKind
from .provider_descriptor import AIModelDescriptor, ProviderDescriptor
from .provider_identity import ProviderIdentity, ProviderStatus
from .provider_registry import AIProviderRegistry


@dataclass(frozen=True)
class DiscoveryResult:
    """Hasil discovery satu entitas."""

    provider_id: str
    model_id: Optional[str] = None
    capability: Optional[AICapabilityKind] = None

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "capability": self.capability.value if self.capability else None,
        }


class AIProviderDiscovery:
    """Mesin discovery deterministik berbasis registry dan descriptor."""

    def __init__(
        self,
        registry: AIProviderRegistry,
        descriptors: Tuple[ProviderDescriptor, ...] = (),
    ) -> None:
        self._registry = registry
        self._descriptors = {d.identity.provider_id: d for d in descriptors}

    def set_descriptors(self, descriptors: Tuple[ProviderDescriptor, ...]) -> None:
        self._descriptors = {d.identity.provider_id: d for d in descriptors}

    def discover_providers(self, status: Optional[ProviderStatus] = None) -> Tuple[ProviderIdentity, ...]:
        return self._registry.list(status=status)

    def discover_models(self, provider_id: Optional[str] = None) -> Tuple[AIModelDescriptor, ...]:
        if provider_id is not None:
            desc = self._descriptors.get(provider_id)
            return desc.supported_models if desc else ()
        return tuple(
            m
            for desc in self._descriptors.values()
            for m in desc.supported_models
        )

    def discover_capability(
        self, kind: AICapabilityKind
    ) -> Tuple[DiscoveryResult, ...]:
        """Temukan provider/model yang mendukung sebuah capability."""
        results = []
        for provider_id, desc in self._descriptors.items():
            for model in desc.supported_models:
                if _supports(model.capability, kind):
                    results.append(
                        DiscoveryResult(provider_id=provider_id, model_id=model.model_id, capability=kind)
                    )
        return tuple(results)

    def compatibility_filter(
        self, *, requires: AICapabilityKind, provider_id: Optional[str] = None
    ) -> Tuple[ProviderIdentity, ...]:
        """Filter provider yang kompatibel dengan capability tertentu."""
        matched = self.discover_capability(requires)
        provider_ids = {r.provider_id for r in matched}
        if provider_id is not None:
            provider_ids &= {provider_id}
        out = []
        for p in self._registry.list():
            if p.provider_id in provider_ids:
                out.append(p)
        return tuple(out)


_ATTR_BY_KIND = {
    AICapabilityKind.TEXT_GENERATION: "supports_text_generation",
    AICapabilityKind.STRUCTURED_OUTPUT: "supports_structured_output",
    AICapabilityKind.VISION: "supports_vision",
    AICapabilityKind.EMBEDDING: "supports_embedding",
    AICapabilityKind.TOOL_CALLING: "supports_tool_calling",
    AICapabilityKind.CONTEXT_HANDLING: "context_window",
}


def _supports(model_capability: object, kind: AICapabilityKind) -> bool:
    """Deteksi dukungan capability pada ModelCapability."""
    attr = _ATTR_BY_KIND.get(kind)
    if attr is None:
        return False
    value = getattr(model_capability, attr, None)
    if kind == AICapabilityKind.CONTEXT_HANDLING:
        return bool(value and value > 0)
    return bool(value)
