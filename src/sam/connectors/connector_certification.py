"""Connector Certification — engine sertifikasi connector.

Sprint 122 — Connector Certification.
Sertifikasi menilai kesiapan runtime connector (preview-only, deterministik).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class CertificationCriterion:
    """Satu kriteria sertifikasi."""
    name: str
    passed: bool = False
    detail: str = ""


@dataclass(frozen=True)
class CertificationResult:
    """Hasil sertifikasi."""
    certified: bool = False
    score: float = 0.0
    criteria: List[CertificationCriterion] = field(default_factory=list)


class ConnectorCertifier:
    """Sertifikasi connector runtime berdasarkan regulatity."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def certify(self) -> CertificationResult:
        criteria = []
        has_connector = self._registry.count() > 0
        criteria.append(CertificationCriterion("has_connectors", has_connector,
                                               f"{self._registry.count()} connectors"))
        with_cap = sum(1 for cid in self._registry.list_ids()
                       if self._registry.get_capabilities(cid))
        criteria.append(CertificationCriterion("has_capabilities", with_cap > 0,
                                               f"{with_cap} with capabilities"))
        passed = sum(1 for c in criteria if c.passed)
        score = (passed / len(criteria)) * 100.0 if criteria else 0.0
        certified = all(c.passed for c in criteria)
        return CertificationResult(certified, round(score, 1), criteria)
