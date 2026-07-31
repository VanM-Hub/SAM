"""Provider Base — abstraksi bersama Provider Runtime (Phase XIV).

Berisi DTO umum dan BaseProvider. Tidak ada logika provider spesifik.
"""
from .provider_descriptor import ProviderDescriptor, ProviderStatus, ProviderSummary
from .provider_capability import ProviderCapability, ProviderOperation
from .provider_contract import ProviderContract, ProviderContractCompliance
from .protocol import ProviderProtocol, ProtocolCompliance
from .base_provider import BaseProvider, ProviderError

__all__ = [
    "ProviderDescriptor",
    "ProviderStatus",
    "ProviderSummary",
    "ProviderCapability",
    "ProviderOperation",
    "ProviderContract",
    "ProviderContractCompliance",
    "ProviderProtocol",
    "ProtocolCompliance",
    "BaseProvider",
    "ProviderError",
]
