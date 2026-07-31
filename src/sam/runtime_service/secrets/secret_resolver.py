"""SecretResolver (Sprint 263).

Program D - Runtime Services & Deployment.
Meresolusi secret tanpa menyimpan nilai dalam objek.
"""
from __future__ import annotations
from typing import Dict, Optional

from .secret_provider import SecretProvider


class SecretResolver:
    """Resolver secret dari env (sync, deterministic)."""

    def __init__(self, provider: Optional[SecretProvider] = None) -> None:
        self._provider = provider or SecretProvider()

    def resolve(self, key: str) -> Optional[str]:
        return self._provider.get(key)

    def resolve_required(self, key: str) -> str:
        return self._provider.required(key)

    def available(self, keys: list) -> Dict[str, str]:
        return self._provider.resolve_all(keys)
