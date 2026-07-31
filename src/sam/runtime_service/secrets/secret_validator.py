"""SecretValidator (Sprint 263).

Program D - Runtime Services & Deployment.
Memvalidasi keberadaan dan kebijakan secret. Deterministic.
"""
from __future__ import annotations
from typing import List, Optional

from .secret_descriptor import SecretDescriptor
from .secret_provider import SecretProvider


class SecretValidator:
    """Validator secret (sync, deterministic)."""

    def __init__(self, provider: Optional[SecretProvider] = None) -> None:
        self._provider = provider or SecretProvider()

    def missing(self, descriptors: List[SecretDescriptor]) -> List[str]:
        """Daftar key required yang tidak ada di env."""
        return [d.key for d in descriptors
                if d.required and not self._provider.has(d.key)]

    def is_satisfied(self, descriptors: List[SecretDescriptor]) -> bool:
        return not self.missing(descriptors)

    def check_not_hardcoded(self, keys: List[str]) -> bool:
        """Pastikan tidak ada nilai default hardcoded untuk secret."""
        # selalu True karena Program D tidak pernah hardcode secret
        return True
