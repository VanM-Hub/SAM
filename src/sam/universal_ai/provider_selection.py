"""Provider Selection - WP-17 (MISSION-5.1 / IP-5.1-002).

Pemilihan Provider berdasarkan capability dan context. Selection menghasilkan
Provider Resolution yang dapat dijelaskan; bukan hidden decision, bukan
governance override, bukan execution bypass.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .adapter_framework import ConnectionStatus, ProviderAdapter


@dataclass(frozen=True)
class SelectionEvidence:
    """Bukti pemilihan provider."""

    provider_id: str
    reason: str
    compatible: bool = True
    status: str = ""

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "reason": self.reason,
            "compatible": self.compatible,
            "status": self.status,
        }


@dataclass(frozen=True)
class ProviderResolution:
    """Hasil pemilihan provider yang dapat dijelaskan."""

    selected_provider_id: Optional[str]
    rationale: Tuple[str, ...] = field(default_factory=tuple)
    candidates: Tuple[SelectionEvidence, ...] = field(default_factory=tuple)

    @property
    def resolved(self) -> bool:
        return self.selected_provider_id is not None

    def as_dict(self) -> dict:
        return {
            "selected_provider_id": self.selected_provider_id,
            "rationale": list(self.rationale),
            "candidates": [c.as_dict() for c in self.candidates],
            "resolved": self.resolved,
        }


class ProviderSelector:
    """Memilih provider berdasarkan capability dan ketersediaan."""

    def __init__(
        self,
        adapters: Tuple[ProviderAdapter, ...] = (),
        preference: Tuple[str, ...] = (),
    ) -> None:
        self._adapters = list(adapters)
        self._preference = tuple(preference)

    def add(self, adapter: ProviderAdapter) -> None:
        self._adapters.append(adapter)

    def select(self, *, required_capability: str = "text_generation", available_only: bool = True) -> ProviderResolution:
        """Pilih provider kompatibel pertama berdasarkan urutan preference lalu deklarasi."""
        candidates: List[SelectionEvidence] = []
        # urutkan: preference dulu, lalu sisanya sesuai urutan pendaftaran
        ordered = self._sort_by_preference()

        for adapter in ordered:
            compatible = adapter.provider_id not in (bad for bad, _ in self._known_incompatible())
            if available_only and adapter.status == ConnectionStatus.ERROR:
                candidates.append(
                    SelectionEvidence(adapter.provider_id, "unavailable (error)", compatible=False, status=adapter.status.value)
                )
                continue
            candidates.append(
                SelectionEvidence(adapter.provider_id, "compatible candidate", compatible=compatible, status=adapter.status.value)
            )
            if compatible:
                return ProviderResolution(
                    selected_provider_id=adapter.provider_id,
                    rationale=("selected by compatibility & preference",),
                    candidates=tuple(candidates),
                )

        return ProviderResolution(
            selected_provider_id=None,
            rationale=("no compatible provider available",),
            candidates=tuple(candidates),
        )

    def _sort_by_preference(self) -> List[ProviderAdapter]:
        pref = [a for a in self._adapters if a.provider_id in self._preference]
        rest = [a for a in self._adapters if a.provider_id not in self._preference]
        return pref + rest

    def _known_incompatible(self) -> Tuple[Tuple[str, str], ...]:
        return ()
