"""SecretRuntime (Sprint 263).

Program D - Runtime Services & Deployment.
Orkestrasi secret runtime: resolve + validasi, semua dari env.
Provider lain TIDAK mengetahui secret ini.
"""
from __future__ import annotations
from typing import Dict, List, Optional

from .secret_descriptor import SecretDescriptor
from .secret_provider import SecretProvider
from .secret_resolver import SecretResolver
from .secret_validator import SecretValidator
from . import SUPPORTED_SECRETS


class SecretRuntime:
    """Runtime secret (sync, deterministic)."""

    def __init__(self, provider: Optional[SecretProvider] = None) -> None:
        self._provider = provider or SecretProvider()
        self._resolver = SecretResolver(self._provider)
        self._validator = SecretValidator(self._provider)
        self._descriptors: Dict[str, SecretDescriptor] = {
            key: SecretDescriptor(key=key) for key in SUPPORTED_SECRETS
        }

    def get(self, key: str) -> Optional[str]:
        return self._resolver.resolve(key)

    def is_available(self, key: str) -> bool:
        return self._provider.has(key)

    def available_providers(self) -> List[str]:
        """Daftar secret (env key) yang tersedia."""
        return [d.key for d in self._descriptors.values()
                if self._provider.has(d.key)]

    def missing_required(self, required_keys: Optional[list] = None) -> List[str]:
        """Daftar key yang harus ada tapi tidak tersedia di env."""
        keys = required_keys or [d.key for d in self._descriptors.values()
                                 if d.required]
        return [k for k in keys if not self._provider.has(k)]

    def redact(self, value: Optional[str]) -> str:
        """Samarkan nilai secret untuk logging."""
        if value is None:
            return "<unset>"
        if len(value) <= 4:
            return "****"
        return value[:2] + "****" + value[-2:]
