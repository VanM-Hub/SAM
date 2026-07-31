"""Sprint 261 - Intelligence Runtime Foundation: builder (merakit registri tanpa hardcode provider)."""
from __future__ import annotations

from dataclasses import dataclass

from .registry import IntelligenceRegistry, KNOWN_RUNTIMES


@dataclass(frozen=True)
class IntelligenceBuilder:
    """Builder deterministik untuk menyusun IntelligenceRegistry.

    Mengisi entri dari KNOWN_RUNTIMES (nama runtime struktural), bukan nama
    provider API. Tidak menghubungi IO/network apa pun.
    """

    registry: IntelligenceRegistry

    @classmethod
    def create(cls) -> "IntelligenceBuilder":
        return cls(registry=IntelligenceRegistry())

    def register_known_runtimes(self) -> "IntelligenceBuilder":
        reg = self.registry
        for name in KNOWN_RUNTIMES:
            kind = (
                "runtime"
                if "Runtime" in name or name in ("Guardian", "Mission")
                else "layer"
            )
            reg = reg.with_entry(name, kind)
        return IntelligenceBuilder(registry=reg)

    def build(self) -> IntelligenceRegistry:
        return self.registry
