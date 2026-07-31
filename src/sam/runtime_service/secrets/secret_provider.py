"""SecretProvider (Sprint 263).

Program D - Runtime Services & Deployment.
Mengambil secret hanya dari environment. Tidak pernah hardcode.
"""
from __future__ import annotations
import os
from typing import Dict, Optional


class SecretProvider:
    """Penyedia secret dari environment (sync, deterministic)."""

    def __init__(self, env: Optional[Dict[str, str]] = None) -> None:
        self._env = env if env is not None else os.environ

    def get(self, key: str) -> Optional[str]:
        """Ambil secret dari env. Return None jika tidak ada."""
        return self._env.get(key)

    def has(self, key: str) -> bool:
        return key in self._env

    def resolve_all(self, keys: list) -> Dict[str, str]:
        """Ambil sekumpulan secret yang tersedia."""
        return {k: self._env[k] for k in keys if k in self._env}

    def required(self, key: str) -> str:
        value = self._env.get(key)
        if not value:
            raise KeyError(f"required secret missing from env: {key}")
        return value
