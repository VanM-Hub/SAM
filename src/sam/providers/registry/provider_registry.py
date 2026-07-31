"""Provider Registry — engine registrasi provider (preview-only).

Sprint 144 — Provider Foundation (OP-1404).
Registry hanya menyimpan metadata provider. Tidak tahu isi provider.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from ..base.provider_descriptor import (
    ProviderDescriptor,
    ProviderStatus,
    ProviderSummary,
)
from ..base.provider_capability import ProviderCapability
from ..base.provider_contract import ProviderContract


class ProviderRegistry:
    """Registry provider — mendaftarkan & memetakan metadata provider.

    Sinkronus, deterministik, preview-only. Tidak melakukan panggilan eksternal.
    """

    def __init__(self) -> None:
        self._descriptors: Dict[str, ProviderDescriptor] = {}
        self._status: Dict[str, ProviderStatus] = {}
        self._capabilities: Dict[str, List[ProviderCapability]] = {}
        self._contracts: Dict[str, ProviderContract] = {}

    def register(self, descriptor: ProviderDescriptor) -> bool:
        """Daftarkan provider descriptor ke registry."""
        if descriptor.provider_id in self._descriptors:
            return False
        self._descriptors[descriptor.provider_id] = descriptor
        self._status[descriptor.provider_id] = ProviderStatus(
            provider_id=descriptor.provider_id,
            registered=True,
            state="registered",
        )
        return True

    def attach_capability(self, capability: ProviderCapability) -> bool:
        """Kaitkan kapabilitas ke provider (hanya jika sudah terdaftar)."""
        if capability.provider_id not in self._descriptors:
            return False
        self._capabilities.setdefault(capability.provider_id, []).append(capability)
        return True

    def attach_contract(self, contract: ProviderContract) -> bool:
        if contract.provider_id not in self._descriptors:
            return False
        self._contracts[contract.provider_id] = contract
        return True

    def get(self, provider_id: str) -> Optional[ProviderDescriptor]:
        return self._descriptors.get(provider_id)

    def get_status(self, provider_id: str) -> Optional[ProviderStatus]:
        return self._status.get(provider_id)

    def get_capabilities(self, provider_id: str) -> List[ProviderCapability]:
        return list(self._capabilities.get(provider_id, []))

    def get_contract(self, provider_id: str) -> Optional[ProviderContract]:
        return self._contracts.get(provider_id)

    def list_ids(self) -> List[str]:
        return sorted(self._descriptors.keys())

    def count(self) -> int:
        return len(self._descriptors)

    def summary(self) -> ProviderSummary:
        by_type: Dict[str, int] = {}
        for d in self._descriptors.values():
            by_type[d.provider_type] = by_type.get(d.provider_type, 0) + 1
        return ProviderSummary(
            total_providers=len(self._descriptors),
            registered=sum(1 for s in self._status.values() if s.registered),
            discovered=sum(1 for s in self._status.values() if s.discovered),
            by_type=by_type,
        )
