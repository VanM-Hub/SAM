"""Provider Failover Assessment - WP-18 (MISSION-5.1 / IP-5.1-002).

Assessment kemungkinan penggunaan Provider alternatif ketika Provider utama
tidak tersedia. Menghasilkan assessment/recommendation; BUKAN automatic failover
tanpa mekanisme Governance yang sesuai.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .adapter_framework import ConnectionStatus, ProviderAdapter


@dataclass(frozen=True)
class FailoverCandidate:
    """Kandidat alternatif provider."""

    provider_id: str
    compatible: bool
    reason: str

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "compatible": self.compatible,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class FailoverAssessment:
    """Hasil assessment failover (proposal, bukan eksekusi)."""

    primary_provider_id: str
    available: bool
    candidates: Tuple[FailoverCandidate, ...] = field(default_factory=tuple)
    recommendation: str = "none"

    def as_dict(self) -> dict:
        return {
            "primary_provider_id": self.primary_provider_id,
            "available": self.available,
            "candidates": [c.as_dict() for c in self.candidates],
            "recommendation": self.recommendation,
        }


class FailoverAssessor:
    """Assesment ketersediaan provider alternatif (read-only)."""

    def __init__(self, adapters: Tuple[ProviderAdapter, ...] = ()) -> None:
        self._adapters = list(adapters)

    def assess(self, primary_provider_id: str) -> FailoverAssessment:
        primary = next((a for a in self._adapters if a.provider_id == primary_provider_id), None)
        available = primary is not None and primary.status != ConnectionStatus.ERROR

        candidates: Tuple[FailoverCandidate, ...] = tuple(
            FailoverCandidate(
                provider_id=a.provider_id,
                compatible=a.status != ConnectionStatus.ERROR,
                reason="alternative provider",
            )
            for a in self._adapters
            if a.provider_id != primary_provider_id and a.status != ConnectionStatus.ERROR
        )

        recommendation = "none"
        if not available and candidates:
            recommendation = "use_alternative"
        elif not available:
            recommendation = "no_alternative_available"

        return FailoverAssessment(
            primary_provider_id=primary_provider_id,
            available=available,
            candidates=candidates,
            recommendation=recommendation,
        )
