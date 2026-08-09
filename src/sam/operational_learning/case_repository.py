"""Case Repository - WP-11 (MISSION-4.3 / IP-4.3-002).

Menyimpan kasus operasional (immutable) untuk pembelajaran. Kasus dapat
dicari kembali.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .persistent_storage import PersistenceEngine


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class Case:
    """Satu kasus operasional (immutable)."""

    case_id: str
    title: str
    description: str = ""
    features: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)
    outcome: str = ""
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
    tags: Tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    def feature_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.features}

    def as_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "title": self.title,
            "description": self.description,
            "features": [list(f) for f in self.features],
            "outcome": self.outcome,
            "evidence_ids": list(self.evidence_ids),
            "tags": list(self.tags),
            "created_at": self.created_at,
        }


class CaseRepository:
    """Penyimpanan kasus (persisten, append-only)."""

    def __init__(self, engine: PersistenceEngine) -> None:
        self._engine = engine
        self._index: Dict[str, str] = {}

    def add(self, case: Case) -> None:
        self._engine.append(case.case_id, case.as_dict())
        self._index[case.case_id] = case.case_id

    def get(self, case_id: str) -> Optional[Case]:
        rec = self._engine.get(case_id)
        if rec is None:
            return None
        return self._from_dict(dict(rec.payload))

    def all(self) -> Tuple[Case, ...]:
        return tuple(
            self._from_dict(dict(r.payload)) for r in self._engine.all()
        )

    def count(self) -> int:
        return self._engine.count()

    def search(self, query: str = "") -> Tuple[Case, ...]:
        cases = self.all()
        if not query:
            return cases
        q = query.lower()
        return tuple(
            c
            for c in cases
            if q in c.title.lower() or q in c.description.lower()
        )

    @staticmethod
    def _from_dict(payload: Dict[str, Any]) -> Case:
        return Case(
            case_id=payload["case_id"],
            title=payload.get("title", ""),
            description=payload.get("description", ""),
            features=tuple(tuple(f) for f in payload.get("features") or ()),
            outcome=payload.get("outcome", ""),
            evidence_ids=tuple(payload.get("evidence_ids") or ()),
            tags=tuple(payload.get("tags") or ()),
            created_at=payload.get("created_at", ""),
        )
