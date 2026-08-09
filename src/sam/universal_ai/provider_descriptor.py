"""AI Provider & Model Descriptor - WP-03/WP-04 (MISSION-5.1 / IP-5.1-001).

Descriptor menjelaskan karakteristik Provider dan Model secara declarative.
Provider dan Model dibedakan secara eksplisit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from .provider_identity import ProviderIdentity


@dataclass(frozen=True)
class ModelCapability:
    """Kemampuan yang dimiliki sebuah model."""

    supports_text_generation: bool = False
    supports_structured_output: bool = False
    supports_vision: bool = False
    supports_embedding: bool = False
    supports_tool_calling: bool = False
    context_window: int = 0

    def as_dict(self) -> dict:
        return {
            "supports_text_generation": self.supports_text_generation,
            "supports_structured_output": self.supports_structured_output,
            "supports_vision": self.supports_vision,
            "supports_embedding": self.supports_embedding,
            "supports_tool_calling": self.supports_tool_calling,
            "context_window": self.context_window,
        }


@dataclass(frozen=True)
class AIModelDescriptor:
    """Deskripsi AI Model yang disediakan oleh Provider."""

    model_id: str
    name: str
    provider_id: str
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    capability: ModelCapability = field(default_factory=ModelCapability)
    modality: Tuple[str, ...] = field(default_factory=tuple)
    available: bool = False

    def as_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "provider_id": self.provider_id,
            "metadata": dict(self.metadata),
            "capability": self.capability.as_dict(),
            "modality": list(self.modality),
            "available": self.available,
        }


@dataclass(frozen=True)
class ProviderDescriptor:
    """Deskripsi karakteristik Provider secara declarative."""

    identity: ProviderIdentity
    supported_models: Tuple[AIModelDescriptor, ...] = field(default_factory=tuple)
    interfaces: Tuple[str, ...] = field(default_factory=tuple)
    operational_metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    compatibility_metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def models(self) -> Tuple[AIModelDescriptor, ...]:
        return self.supported_models

    def model(self, model_id: str) -> Optional[AIModelDescriptor]:
        for m in self.supported_models:
            if m.model_id == model_id:
                return m
        return None

    def as_dict(self) -> dict:
        return {
            "identity": self.identity.as_dict(),
            "supported_models": [m.as_dict() for m in self.supported_models],
            "interfaces": list(self.interfaces),
            "operational_metadata": dict(self.operational_metadata),
            "compatibility_metadata": dict(self.compatibility_metadata),
        }
