"""Connector Registry — engine registrasi connector (preview-only).

Sprint 112 — Connector Foundation.
Menyimpan deskripsi connector sebagai data murni. Tidak ada network, thread, async.
"""
from __future__ import annotations
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .connector_descriptor import ConnectorDescriptor, ConnectorStatus, ConnectorSummary
from .connector_capability import ConnectorCapability
from .connector_contract import ConnectorContract
from .connector_metadata import ConnectorMetadata


@dataclass(frozen=True)
class ConnectorRegistrationResult:
    """Hasil registrasi connector (immutable)."""
    success: bool
    connector_id: str
    message: str = ""
    total_registered: int = 0


class ConnectorRegistry:
    """Registry connector — mendaftarkan & memetakan descriptor.

    Sinkronus, deterministik, preview-only. Tidak melakukan panggilan eksternal apa pun.
    """

    def __init__(self) -> None:
        self._descriptors: Dict[str, ConnectorDescriptor] = {}
        self._status: Dict[str, ConnectorStatus] = {}
        self._capabilities: Dict[str, List[ConnectorCapability]] = {}
        self._contracts: Dict[str, ConnectorContract] = {}
        self._metadata: Dict[str, ConnectorMetadata] = {}

    def register(self, descriptor: ConnectorDescriptor) -> ConnectorRegistrationResult:
        """Daftarkan connector descriptor ke registry."""
        if descriptor.connector_id in self._descriptors:
            return ConnectorRegistrationResult(
                success=False, connector_id=descriptor.connector_id,
                message=f"connector {descriptor.connector_id} already registered",
                total_registered=len(self._descriptors),
            )
        self._descriptors[descriptor.connector_id] = descriptor
        self._status[descriptor.connector_id] = ConnectorStatus(
            connector_id=descriptor.connector_id, registered=True, state="registered",
        )
        return ConnectorRegistrationResult(
            success=True, connector_id=descriptor.connector_id,
            message="registered", total_registered=len(self._descriptors),
        )

    def attach_capability(self, capability: ConnectorCapability) -> bool:
        """Kaitkan kapabilitas ke connector (hanya jika connector sudah terdaftar)."""
        if capability.connector_id not in self._descriptors:
            return False
        self._capabilities.setdefault(capability.connector_id, []).append(capability)
        return True

    def attach_contract(self, contract: ConnectorContract) -> bool:
        if contract.connector_id not in self._descriptors:
            return False
        self._contracts[contract.connector_id] = contract
        return True

    def attach_metadata(self, meta: ConnectorMetadata) -> bool:
        if meta.connector_id not in self._descriptors:
            return False
        self._metadata[meta.connector_id] = meta
        return True

    def get(self, connector_id: str) -> Optional[ConnectorDescriptor]:
        return self._descriptors.get(connector_id)

    def get_status(self, connector_id: str) -> Optional[ConnectorStatus]:
        return self._status.get(connector_id)

    def get_capabilities(self, connector_id: str) -> List[ConnectorCapability]:
        return list(self._capabilities.get(connector_id, []))

    def get_contract(self, connector_id: str) -> Optional[ConnectorContract]:
        return self._contracts.get(connector_id)

    def get_metadata(self, connector_id: str) -> Optional[ConnectorMetadata]:
        return self._metadata.get(connector_id)

    def list_ids(self) -> List[str]:
        return sorted(self._descriptors.keys())

    def count(self) -> int:
        return len(self._descriptors)

    def summary(self) -> ConnectorSummary:
        by_type: Dict[str, int] = {}
        for d in self._descriptors.values():
            by_type[d.connector_type] = by_type.get(d.connector_type, 0) + 1
        return ConnectorSummary(
            total_connectors=len(self._descriptors),
            registered=sum(1 for s in self._status.values() if s.registered),
            discovered=sum(1 for s in self._status.values() if s.discovered),
            by_type=by_type,
        )
