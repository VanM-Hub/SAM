"""Provider Builder — builder registrasi provider (preview-only).

Sprint 144 — Provider Foundation (OP-1405).
Membangun registry dari kumpulan provider Benar secara deterministik.
"""
from __future__ import annotations
from typing import List

from ..base.base_provider import BaseProvider
from ..base.provider_descriptor import ProviderDescriptor
from ..base.provider_capability import ProviderCapability
from ..base.provider_contract import ProviderContract
from .provider_registry import ProviderRegistry


class ProviderBuilder:
    """Builder registry — mendaftarkan provider beserta metadata-nya."""

    def __init__(self) -> None:
        self._registry = ProviderRegistry()

    def add(self, provider: BaseProvider) -> bool:
        """Daftarkan satu provider lengkap (descriptor + capability + contract)."""
        if provider.descriptor is None:
            return False
        ok = self._registry.register(provider.descriptor)
        if not ok:
            return False
        for cap in provider.capabilities:
            self._registry.attach_capability(cap)
        if provider.contract is not None:
            self._registry.attach_contract(provider.contract)
        return True

    def build(self) -> ProviderRegistry:
        return self._registry
