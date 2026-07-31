"""Provider Preview — preview mapping provider (Sprint 247).

Program B — Model Runtime Integration.
Preview pilihan provider; tidak ada network call. external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .provider_mapping import ProviderMapping
from .provider_selector import ProviderSelection


@dataclass(frozen=True)
class ProviderPreview:
    """Preview provider (immutable). Belum network."""
    preview_id: str
    mapping: ProviderMapping
    selection: ProviderSelection
    note: str = "mapping preview - no network call"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "preview_id": self.preview_id,
            "mapping": self.mapping.as_dict(),
            "selection": self.selection.as_dict(),
            "note": self.note,
            "external_calls": self.external_calls,
        }
