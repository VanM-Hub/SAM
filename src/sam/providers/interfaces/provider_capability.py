"""Provider Capability — kapabilitas standar provider (Sprint 228).

Program A — External Connector Integration.
Tidak ada provider-specific logic; ProviderCapability menyatukan mana operasi
yang didukung provider dalam bentuk generik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Set, Tuple

PROVIDER_CAPABILITY_KEYS: Tuple[str, ...] = (
    "generate",     # hasilkan output dari input
    "embed",        # representasi vektor
    "chat",         # percakapan
    "classify",     # klasifikasi
    "extract",      # ekstraksi
    "summarize",    # ringkasan
    "translate",    # terjemahan
    "tool_call",    # pemanggilan tool
)


@dataclass(frozen=True)
class ProviderCapability:
    """Kapabilitas yang didukung provider (immutable, generik)."""
    provider_id: str
    operation: str
    supported: bool = True
    mode: str = "preview"  # preview | approval | execute
    external_calls: int = 0  # default tidak ada panggilan eksternal

    @property
    def key(self) -> str:
        return f"{self.provider_id}:{self.operation}"


@dataclass(frozen=True)
class ProviderCapabilitySet:
    """Set kapabilitas provider — immutable (frozen), mendukung lookup cepat."""
    provider_id: str
    operations: Tuple[str, ...] = field(default_factory=tuple)

    def supports(self, operation: str) -> bool:
        return operation in self.operations

    @property
    def count(self) -> int:
        return len(self.operations)

    def as_set(self) -> Set[str]:
        return set(self.operations)
