# OP-382 — Experience Repository
# Python 3.8 compatible, frozen dataclass, synchronous only
# Collects completed/completed/failed/recovered experiences — read-only store

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExperienceRecord:
    """Complete record of a single operation experience."""
    experience_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    source_type: str = ""  # mission, failure, recovery, approval, guardian, reasoning
    outcome: str = ""  # success, failure, approved, denied, recovered, observed
    summary: str = ""
    details: Tuple[str, ...] = field(default_factory=tuple)
    evidence_keys: Tuple[str, ...] = field(default_factory=tuple)
    confidence_impact: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Tuple[str, ...] = field(default_factory=tuple)

    def to_summary(self) -> "ExperienceSummary":
        return ExperienceSummary(
            experience_id=self.experience_id,
            source=self.source,
            source_type=self.source_type,
            outcome=self.outcome,
            summary=self.summary,
            timestamp=self.timestamp,
        )


@dataclass(frozen=True)
class ExperienceSummary:
    """Lightweight summary DTO for listing."""
    experience_id: str = ""
    source: str = ""
    source_type: str = ""
    outcome: str = ""
    summary: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# ExperienceRepository
# ---------------------------------------------------------------------------

class ExperienceRepository:
    """In-memory repository of operational experiences.

    Collects completed missions, failures, recoveries, approvals, guardian
    findings, and reasoning outcomes.

    Read-only by design — records are stored as immutable DTOs.
    No persistence, no modification of stored records.
    """

    def __init__(self) -> None:
        self._records: Dict[str, ExperienceRecord] = {}
        self._by_source_type: Dict[str, List[str]] = {}  # source_type -> [ids]
        self._by_outcome: Dict[str, List[str]] = {}  # outcome -> [ids]

    def _add_to_index(self, record: ExperienceRecord) -> None:
        rid = record.experience_id
        self._by_source_type.setdefault(record.source_type, []).append(rid)
        self._by_outcome.setdefault(record.outcome, []).append(rid)

    def add(self, record: ExperienceRecord) -> ExperienceRecord:
        """Store an experience record. Returns the record (immutable)."""
        self._records[record.experience_id] = record
        self._add_to_index(record)
        return record

    def get(self, experience_id: str) -> Optional[ExperienceRecord]:
        return self._records.get(experience_id)

    def get_all(self) -> Tuple[ExperienceRecord, ...]:
        return tuple(self._records.values())

    def get_summaries(self) -> Tuple[ExperienceSummary, ...]:
        return tuple(r.to_summary() for r in self._records.values())

    def get_by_source_type(self, source_type: str) -> Tuple[ExperienceRecord, ...]:
        ids = self._by_source_type.get(source_type, [])
        return tuple(self._records[rid] for rid in ids if rid in self._records)

    def get_by_outcome(self, outcome: str) -> Tuple[ExperienceRecord, ...]:
        ids = self._by_outcome.get(outcome, [])
        return tuple(self._records[rid] for rid in ids if rid in self._records)

    def search(
        self,
        query: str = "",
        source_type: Optional[str] = None,
        outcome: Optional[str] = None,
        max_results: int = 50,
    ) -> Tuple[ExperienceRecord, ...]:
        """Search experience records by text, source_type, and outcome."""
        results = []
        q_lower = query.lower() if query else ""
        for rec in self._records.values():
            if source_type and rec.source_type != source_type:
                continue
            if outcome and rec.outcome != outcome:
                continue
            if q_lower:
                if q_lower not in rec.summary.lower() and q_lower not in rec.source.lower():
                    continue
            results.append(rec)
        results.sort(key=lambda r: r.timestamp, reverse=True)
        return tuple(results[:max_results])

    def count_by_source_type(self) -> Dict[str, int]:
        return {k: len(v) for k, v in self._by_source_type.items()}

    def count_by_outcome(self) -> Dict[str, int]:
        return {k: len(v) for k, v in self._by_outcome.items()}

    @property
    def total_count(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records.clear()
        self._by_source_type.clear()
        self._by_outcome.clear()
