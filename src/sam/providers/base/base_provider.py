"""BaseProvider — abstraksi bersama untuk semua provider (Phase XIV).

Sprint 144 — Provider Foundation (OP-1404).
Semua provider wajib mengimplementasikan kontrak Connector Runtime,
bukan berkomunikasi langsung dengan runtime lain.

Preview-only: membangun request, validasi, dan representasi aksi
tanpa melakukan eksekusi nyata.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from .provider_descriptor import ProviderDescriptor
from .provider_capability import ProviderCapability
from .provider_contract import ProviderContract


class ProviderError(Exception):
    """Kesalahan domain dalam Provider Runtime (deterministik)."""


class BaseProvider:
    """Kelas dasar semua provider. Sinkronus, deterministik, preview-only."""

    descriptor: ProviderDescriptor = None  # type: ignore[assignment]
    capabilities: List[ProviderCapability] = []
    contract: Optional[ProviderContract] = None

    def __init__(self) -> None:
        self._preview_count = 0
        self._external_calls = 0  # selalu 0 di Phase XIV

    # --- Identitas ---
    def describe(self) -> ProviderDescriptor:
        return self.descriptor

    def get_capabilities(self) -> List[ProviderCapability]:
        return list(self.capabilities)

    def get_contract(self) -> Optional[ProviderContract]:
        return self.contract

    def supports(self, operation: str) -> bool:
        return any(c.supports(operation) for c in self.capabilities)

    # --- Preview (tidak pernah eksekusi) ---
    def preview(self, operation: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Simulasi aksi tanpa eksekusi nyata. external_calls selalu 0."""
        if not self.supports(operation):
            raise ProviderError(
                f"provider {self.descriptor.provider_id} does not support {operation}"
            )
        self._preview_count += 1
        return {
            "provider_id": self.descriptor.provider_id,
            "operation": operation,
            "preview": True,
            "external_calls": 0,
            "request": request,
        }

    @property
    def preview_count(self) -> int:
        return self._preview_count

    @property
    def external_calls(self) -> int:
        return self._external_calls
