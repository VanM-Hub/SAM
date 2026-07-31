"""Provider Certification — sertifikasi provider (read-only).

Sprint 155 — Certification.
Memvalidasi provider terdaftar terhadap kriteria. Tidak invoke.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..base.base_provider import BaseProvider
from ..registry.provider_registry import ProviderRegistry


@dataclass(frozen=True)
class CertificationCriterion:
    """Kriteria sertifikasi (immutable)."""
    name: str
    passed: bool = False


@dataclass(frozen=True)
class CertificationResult:
    """Hasil sertifikasi (immutable)."""
    provider_id: str = ""
    certified: bool = False
    criteria: List[CertificationCriterion] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.criteria if c.passed)


class ProviderCertifier:
    """Certifier provider. Deterministik, read-only."""

    CRITERIA = ["registered", "has_capability", "has_contract", "preview_only"]

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    def certify(self, provider_id: str) -> CertificationResult:
        desc = self._registry.get(provider_id)
        if not desc:
            return CertificationResult(provider_id=provider_id, certified=False)
        caps = self._registry.get_capabilities(provider_id)
        contract = self._registry.get_contract(provider_id)
        criteria = [
            CertificationCriterion("registered", True),
            CertificationCriterion("has_capability", len(caps) > 0),
            CertificationCriterion("has_contract", contract is not None),
            CertificationCriterion(
                "preview_only",
                all(getattr(c, "preview_only", True) for c in caps),
            ),
        ]
        certified = all(c.passed for c in criteria)
        return CertificationResult(
            provider_id=provider_id, certified=certified, criteria=criteria
        )

    def certify_all(self) -> List[CertificationResult]:
        return [self.certify(pid) for pid in self._registry.list_ids()]

    def certified_ids(self) -> List[str]:
        return [r.provider_id for r in self.certify_all() if r.certified]
