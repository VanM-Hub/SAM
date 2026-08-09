"""Evidence Collection - WP-03 (MISSION-4.2 / IP-4.2-001).

Mengumpulkan evidence operasional dari berbagai sumber secara terstruktur.

Evidence memiliki sumber yang jelas, tervalidasi, dapat ditelusuri, dan tidak
ada evidence tanpa metadata.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class EvidenceSource:
    """Sumber evidence (jelas & dapat ditelusuri)."""

    source_type: str  # runtime | provider | api | file | telemetry
    source_id: str
    name: str = ""
    location: str = ""

    def as_dict(self) -> dict:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "name": self.name,
            "location": self.location,
        }


@dataclass(frozen=True)
class EvidenceModel:
    """Model evidence operasional (tidak ada evidence tanpa metadata)."""

    evidence_id: str
    investigation_id: str
    source: EvidenceSource
    category: str
    data: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)
    collected_at: str = field(default_factory=_now_utc)
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    validated: bool = False

    def as_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "investigation_id": self.investigation_id,
            "source": self.source.as_dict(),
            "category": self.category,
            "data": [list(d) for d in self.data],
            "collected_at": self.collected_at,
            "metadata": [list(m) for m in self.metadata],
            "validated": self.validated,
        }


@dataclass(frozen=True)
class EvidenceValidationResult:
    """Hasil validasi evidence."""

    evidence_id: str
    valid: bool
    reason: str = ""

    def as_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "valid": self.valid,
            "reason": self.reason,
        }


class EvidenceValidation:
    """Validasi evidence (harus punya sumber, id, metadata dasarnya)."""

    MIN_FIELDS = ("source", "category")

    @classmethod
    def validate(cls, evidence: EvidenceModel) -> EvidenceValidationResult:
        if not evidence.evidence_id:
            return EvidenceValidationResult(
                evidence.evidence_id, False, "missing evidence_id"
            )
        if not evidence.source.source_id:
            return EvidenceValidationResult(
                evidence.evidence_id, False, "missing source_id"
            )
        if not evidence.category:
            return EvidenceValidationResult(
                evidence.evidence_id, False, "missing category"
            )
        if not evidence.metadata:
            return EvidenceValidationResult(
                evidence.evidence_id, False, "no metadata"
            )
        return EvidenceValidationResult(evidence.evidence_id, True)


class EvidenceCollector:
    """Mengumpulkan evidence dari sumber terdaftar (read-only)."""

    def __init__(self) -> None:
        self._sources: Dict[str, Callable[..., List[EvidenceModel]]] = {}

    def register_source(
        self, source_id: str, fn: Callable[..., List[EvidenceModel]]
    ) -> None:
        self._sources[source_id] = fn

    def collect(
        self,
        investigation_id: str,
        *,
        source_ids: Optional[Tuple[str, ...]] = None,
    ) -> Tuple[EvidenceModel, ...]:
        collected: List[EvidenceModel] = []
        ids = source_ids or tuple(self._sources.keys())
        for sid in ids:
            fn = self._sources.get(sid)
            if fn is None:
                continue
            try:
                results = fn(investigation_id=investigation_id)
                collected.extend(results or [])
            except Exception:
                # observasi gagal: lewati sumber, jangan gagalkan investigasi
                continue
        return tuple(collected)


class EvidenceAggregation:
    """Agregasi evidence per kategori / sumber."""

    @staticmethod
    def aggregate_by_category(
        evidences: Tuple[EvidenceModel, ...],
    ) -> Dict[str, Tuple[EvidenceModel, ...]]:
        result: Dict[str, List[EvidenceModel]] = {}
        for e in evidences:
            result.setdefault(e.category, []).append(e)
        return {k: tuple(v) for k, v in result.items()}

    @staticmethod
    def aggregate_by_source(
        evidences: Tuple[EvidenceModel, ...],
    ) -> Dict[str, Tuple[EvidenceModel, ...]]:
        result: Dict[str, List[EvidenceModel]] = {}
        for e in evidences:
            result.setdefault(e.source.source_id, []).append(e)
        return {k: tuple(v) for k, v in result.items()}

    @staticmethod
    def counts(evidences: Tuple[EvidenceModel, ...]) -> Dict[str, int]:
        return {
            "total": len(evidences),
            "validated": sum(1 for e in evidences if e.validated),
        }


class EvidenceRepository:
    """Penyimpanan evidence per investigasi (append-only)."""

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[EvidenceModel, ...]] = {}

    def save(
        self, investigation_id: str, evidences: Tuple[EvidenceModel, ...]
    ) -> None:
        existing = self._store.get(investigation_id, ())
        self._store[investigation_id] = existing + evidences

    def get(
        self, investigation_id: str
    ) -> Tuple[EvidenceModel, ...]:
        return self._store.get(investigation_id, ())

    def get_by_id(self, evidence_id: str) -> Optional[EvidenceModel]:
        for group in self._store.values():
            for e in group:
                if e.evidence_id == evidence_id:
                    return e
        return None

    def build(
        self,
        investigation_id: str,
        source: EvidenceSource,
        category: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None,
        evidence_id: Optional[str] = None,
    ) -> EvidenceModel:
        return EvidenceModel(
            evidence_id=evidence_id or uuid.uuid4().hex,
            investigation_id=investigation_id,
            source=source,
            category=category,
            data=tuple(sorted(data.items())),
            metadata=tuple(sorted((metadata or {}).items())),
        )
