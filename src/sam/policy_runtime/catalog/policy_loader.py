"""Policy Loader — loader policy read-only (Sprint 208).

Loader HANYA mengembalikan representasi yang sudah ada di memori —
tidak load file, tidak cache, TIDAK disk/IO.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..model.policy import Policy
from .policy_catalog import PolicyCatalog


@dataclass(frozen=True)
class PolicyLoadResult:
    """Hasil load (immutable)."""
    ok: bool = False
    policy: Policy | None = None
    detail: str = ""


class PolicyLoader:
    """Loader policy. Read-only (tanpa disk/IO, tanpa cache)."""

    def __init__(self, catalog: PolicyCatalog) -> None:
        self._catalog = catalog

    def load(self, policy_id: str) -> PolicyLoadResult:
        pol = self._catalog.get(policy_id)
        if pol is None:
            return PolicyLoadResult(ok=False, detail="not found")
        return PolicyLoadResult(ok=True, policy=pol, detail="loaded")
