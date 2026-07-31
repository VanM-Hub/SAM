"""Dashboard Model Foundation — bridge dashboard (5 cards) <-> model (Sprint 239).

Program B — Model Runtime Integration.
Read-only bridge; tidak ada dashboard melainkan representasi kartu model.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict

from .model_descriptor import ModelDescriptor
from .model_registry import ModelRegistry


@dataclass(frozen=True)
class DashboardModelCard:
    """Satu kartu model pada dashboard (immutable)."""
    card_id: str
    title: str
    content: str = ""
    model_id: str = ""
    preview_only: bool = True

    def as_dict(self) -> dict:
        return {
            "card_id": self.card_id,
            "title": self.title,
            "content": self.content,
            "model_id": self.model_id,
            "preview_only": self.preview_only,
        }


class DashboardModelFoundation:
    """Bridge dashboard <-> model foundation. Read-only, 5 cards.

    Menyajikan hingga 5 kartu ringkasan model.
    """

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self._registry = registry or ModelRegistry()

    def cards(self) -> List[DashboardModelCard]:
        descriptors = self._registry.all()
        # 5 kartu tetap terstruktur
        cards = [
            DashboardModelCard(card_id="model-count", title="Total Model",
                               content=str(len(descriptors))),
            DashboardModelCard(card_id="model-chat", title="Chat Models",
                               content=str(self._count_by_type("chat"))),
            DashboardModelCard(card_id="model-embedding", title="Embedding Models",
                               content=str(self._count_by_type("embedding"))),
            DashboardModelCard(card_id="model-reasoning", title="Reasoning Models",
                               content=str(self._count_by_type("reasoning"))),
            DashboardModelCard(card_id="model-vision", title="Vision Models",
                               content=str(self._count_by_type("vision"))),
        ]
        return cards[:5]

    def _count_by_type(self, model_type: str) -> int:
        return sum(1 for d in self._registry.all() if d.model_type == model_type)

    def as_dict(self) -> Dict[str, object]:
        return {"cards": [c.as_dict() for c in self.cards()]}
