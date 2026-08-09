"""Experience Repository - WP-01 (MISSION-4.3 / IP-4.3-001).

Repositori utama untuk seluruh pengalaman operasional. Mampu menyimpan
seluruh Experience, Experience memiliki identitas unik, dapat ditelusuri,
dan mendukung penyimpanan jangka panjang (persisten).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from .experience_model import Experience
from .persistent_storage import PersistenceEngine


@dataclass(frozen=True)
class RepositoryMetadata:
    """Metadata repository."""

    name: str = "experience_repository"
    version: int = 1
    storage_type: str = "json_persistent"

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "storage_type": self.storage_type,
        }


@dataclass(frozen=True)
class RepositoryStatistics:
    """Statistik repository."""

    total_experiences: int = 0
    by_classification: Dict[str, int] = field(default_factory=dict)
    by_status: Dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "total_experiences": self.total_experiences,
            "by_classification": self.by_classification,
            "by_status": self.by_status,
        }


class ExperienceRepository:
    """Repositori experience persisten (append-only, immutable)."""

    def __init__(self, engine: PersistenceEngine) -> None:
        self._engine = engine
        self._index: Dict[str, str] = {}  # experience_id -> record_id

    # --- Manager ---
    def add(self, experience: Experience) -> None:
        payload = experience.as_dict()
        self._engine.append(experience.experience_id, payload)
        self._index[experience.experience_id] = experience.experience_id

    def get(self, experience_id: str) -> Optional[Experience]:
        record = self._engine.get(experience_id)
        if record is None:
            return None
        payload = dict(record.payload)
        return self._from_dict(payload)

    def all(self) -> Tuple[Experience, ...]:
        return tuple(
            self._from_dict(dict(r.payload))
            for r in self._engine.all()
        )

    def count(self) -> int:
        return self._engine.count()

    # --- Catalog / Index ---
    def catalog(self) -> Tuple[str, ...]:
        return tuple(sorted(self._index.keys()))

    def search(self, *, classification: Optional[str] = None) -> Tuple[Experience, ...]:
        result = []
        for exp in self.all():
            if classification and exp.classification != classification:
                continue
            result.append(exp)
        return tuple(result)

    # --- Statistics ---
    def statistics(self) -> RepositoryStatistics:
        experiences = self.all()
        by_class: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for exp in experiences:
            by_class[exp.classification] = by_class.get(exp.classification, 0) + 1
            by_status[exp.status] = by_status.get(exp.status, 0) + 1
        return RepositoryStatistics(
            total_experiences=len(experiences),
            by_classification=by_class,
            by_status=by_status,
        )

    def metadata(self) -> RepositoryMetadata:
        return RepositoryMetadata()

    def audit_report(self) -> Dict[str, Any]:
        return self._engine.audit_report()

    @staticmethod
    def _from_dict(payload: Dict[str, Any]) -> Experience:
        evidence = tuple(
            (payload.get("evidence") or [])
        )
        from .experience_model import (
            Experience,
            ExperienceContext,
            ExperienceEvidenceRef,
        )

        ev_refs = tuple(
            ExperienceEvidenceRef(
                evidence_id=e.get("evidence_id", ""),
                source_type=e.get("source_type", ""),
                source_id=e.get("source_id", ""),
            )
            for e in evidence
        )
        ctx_data = payload.get("context") or {}
        ctx = ExperienceContext(
            environment=ctx_data.get("environment", ""),
            operator=ctx_data.get("operator", ""),
            target_ids=tuple(ctx_data.get("target_ids") or ()),
            start_time=ctx_data.get("start_time", ""),
            end_time=ctx_data.get("end_time", ""),
        )
        return Experience(
            experience_id=payload["experience_id"],
            summary=payload.get("summary", ""),
            details=tuple(payload.get("details") or ()),
            status=payload.get("status", "recorded"),
            classification=payload.get("classification", ""),
            evidence=ev_refs,
            context=ctx,
            outcome=payload.get("outcome", ""),
            tags=tuple(payload.get("tags") or ()),
            created_at=payload.get("created_at", ""),
        )
