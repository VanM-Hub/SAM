"""
OP-286 — Evidence Builder

Mengumpulkan evidence dari DTO layers.
Tidak membaca Repository, Domain, atau Storage.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    kind: str  # observation, finding, recommendation, mission, timeline, approval, trust, dashboard, health
    source: str
    content: str
    timestamp: str = ""
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "source": self.source,
            "content": self.content,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EvidenceSet:
    items: tuple[EvidenceItem, ...] = ()
    total: int = 0
    by_kind: dict[str, list[EvidenceItem]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "by_kind": {k: [i.to_dict() for i in v]
                        for k, v in self.by_kind.items()},
        }


class EvidenceBuilder:
    """
    Mengumpulkan evidence dari DTO tanpa menyentuh Repository.

    Evidence dikelompokkan per kind dengan identifier unik.
    """

    _counter: int = 0

    def _next_id(self, kind: str) -> str:
        type(self)._counter += 1
        return f"ev-{kind}-{self._counter}"

    def build(self,
              observations: list[dict[str, Any]] | None = None,
              findings: list[dict[str, Any]] | None = None,
              recommendations: list[dict[str, Any]] | None = None,
              mission_data: dict[str, Any] | None = None,
              timeline_data: dict[str, Any] | None = None,
              approval_data: dict[str, Any] | None = None,
              trust_data: dict[str, Any] | None = None,
              dashboard_data: dict[str, Any] | None = None,
              health_data: dict[str, Any] | None = None,
              ) -> EvidenceSet:
        """Collect evidence from DTO sources."""
        items: list[EvidenceItem] = []

        if observations:
            items.extend(self._from_kind(observations, "observation", "operations"))
        if findings:
            items.extend(self._from_kind(findings, "finding", "operations"))
        if recommendations:
            items.extend(self._from_kind(recommendations, "recommendation", "operations"))
        if mission_data:
            items.append(self._from_single(mission_data, "mission", "mission"))
        if timeline_data:
            items.append(self._from_single(timeline_data, "timeline", "timeline"))
        if approval_data:
            items.append(self._from_single(approval_data, "approval", "operations"))
        if trust_data:
            items.append(self._from_single(trust_data, "trust", "intelligence"))
        if dashboard_data:
            items.append(self._from_single(dashboard_data, "dashboard", "presentation"))
        if health_data:
            items.append(self._from_single(health_data, "health", "health"))

        by_kind: dict[str, list[EvidenceItem]] = {}
        for it in items:
            by_kind.setdefault(it.kind, []).append(it)

        return EvidenceSet(
            items=tuple(items),
            total=len(items),
            by_kind=by_kind,
        )

    def _from_kind(self, data_list: list[dict[str, Any]],
                   kind: str, source: str) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        for d in data_list:
            content = d.get("title") or d.get("description") or d.get("detail") or str(d)
            items.append(EvidenceItem(
                id=self._next_id(kind),
                kind=kind,
                source=source,
                content=str(content)[:500],
                timestamp=d.get("timestamp", ""),
                confidence=d.get("confidence", 1.0),
                metadata=d,
            ))
        return items

    def _from_single(self, data: dict[str, Any],
                     kind: str, source: str) -> EvidenceItem:
        content = data.get("summary") or data.get("status") or data.get("detail") or str(data)
        return EvidenceItem(
            id=self._next_id(kind),
            kind=kind,
            source=source,
            content=str(content)[:500],
            timestamp=data.get("timestamp", ""),
            confidence=data.get("confidence", 1.0),
            metadata=data,
        )
