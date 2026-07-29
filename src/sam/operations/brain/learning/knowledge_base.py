# OP-381 — Operational Knowledge Base
# Python 3.8 compatible, frozen dataclass, synchronous only
# No persistence, no ML, no LLM, no self-modification
# Recommendation only — read-only by design

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid


# ---------------------------------------------------------------------------
# DTOs — Frozen / Immutable
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KnowledgeRecord:
    """A single piece of learned operational knowledge."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: str = ""
    fact: str = ""
    source: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    tags: Tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

    def with_updated_confidence(self, new_confidence: float) -> "KnowledgeRecord":
        """Return a new KnowledgeRecord with updated confidence (immutable pattern)."""
        return KnowledgeRecord(
            record_id=self.record_id,
            category=self.category,
            fact=self.fact,
            source=self.source,
            confidence=new_confidence,
            evidence_count=self.evidence_count,
            tags=self.tags,
            created_at=self.created_at,
            version=self.version + 1,
        )

    def increment_evidence(self, amount: int = 1) -> "KnowledgeRecord":
        """Return a new record with increased evidence count."""
        return KnowledgeRecord(
            record_id=self.record_id,
            category=self.category,
            fact=self.fact,
            source=self.source,
            confidence=self.confidence,
            evidence_count=self.evidence_count + amount,
            tags=self.tags,
            created_at=self.created_at,
            version=self.version + 1,
        )


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """Immutable snapshot of the entire KnowledgeBase at a point in time."""
    records: Tuple[KnowledgeRecord, ...] = field(default_factory=tuple)
    snapshot_time: datetime = field(default_factory=datetime.utcnow)
    total_records: int = 0
    total_categories: int = 0

    @classmethod
    def from_base(cls, base: "KnowledgeBase") -> "KnowledgeSnapshot":
        records = tuple(base._records.values())
        categories = len(set(r.category for r in records))
        return cls(
            records=records,
            total_records=len(records),
            total_categories=categories,
        )


@dataclass(frozen=True)
class KnowledgeStatistics:
    """Statistical overview of the knowledge base."""
    total_records: int = 0
    total_categories: int = 0
    total_sources: int = 0
    avg_confidence: float = 0.0
    total_evidence: int = 0
    top_categories: Tuple[Tuple[str, int], ...] = field(default_factory=tuple)
    top_sources: Tuple[Tuple[str, int], ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Index (for lookup/search)
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeIndex:
    """In-memory index for lookup operations."""
    by_category: Dict[str, List[str]] = field(default_factory=dict)
    by_tag: Dict[str, List[str]] = field(default_factory=dict)
    by_source: Dict[str, List[str]] = field(default_factory=dict)

    def add(self, record: KnowledgeRecord) -> None:
        rid = record.record_id
        self.by_category.setdefault(record.category, []).append(rid)
        for tag in record.tags:
            self.by_tag.setdefault(tag, []).append(rid)
        self.by_source.setdefault(record.source, []).append(rid)

    def remove(self, record: KnowledgeRecord) -> None:
        rid = record.record_id
        cat_list = self.by_category.get(record.category)
        if cat_list and rid in cat_list:
            cat_list.remove(rid)
        for tag in record.tags:
            tag_list = self.by_tag.get(tag)
            if tag_list and rid in tag_list:
                tag_list.remove(rid)
        src_list = self.by_source.get(record.source)
        if src_list and rid in src_list:
            src_list.remove(rid)

    def find_ids_by_category(self, category: str) -> List[str]:
        return list(self.by_category.get(category, []))

    def find_ids_by_tag(self, tag: str) -> List[str]:
        return list(self.by_tag.get(tag, []))

    def find_ids_by_source(self, source: str) -> List[str]:
        return list(self.by_source.get(source, []))


# ---------------------------------------------------------------------------
# KnowledgeBase
# ---------------------------------------------------------------------------

class KnowledgeBase:
    """Operational Knowledge Base: stores learned patterns and operational facts.

    Pure read/write internal store; NO persistence.
    All external access is via immutable DTOs.
    """

    def __init__(self) -> None:
        self._records: Dict[str, KnowledgeRecord] = {}
        self._index = KnowledgeIndex()

    # --- Write Operations (internal) ---

    def add_record(self, record: KnowledgeRecord) -> KnowledgeRecord:
        """Add a record. Returns it for chaining."""
        self._records[record.record_id] = record
        self._index.add(record)
        return record

    def update_record(self, record_id: str, new_record: KnowledgeRecord) -> bool:
        """Replace existing record with new (immutable) version. Returns True if updated."""
        if record_id not in self._records:
            return False
        old = self._records[record_id]
        self._index.remove(old)
        self._records[record_id] = new_record
        self._index.add(new_record)
        return True

    def remove_record(self, record_id: str) -> bool:
        """Remove a record by ID."""
        rec = self._records.pop(record_id, None)
        if rec is None:
            return False
        self._index.remove(rec)
        return True

    # --- Read Operations ---

    def get_record(self, record_id: str) -> Optional[KnowledgeRecord]:
        return self._records.get(record_id)

    def get_all_records(self) -> Tuple[KnowledgeRecord, ...]:
        return tuple(self._records.values())

    def search_by_category(self, category: str) -> Tuple[KnowledgeRecord, ...]:
        ids = self._index.find_ids_by_category(category)
        return tuple(self._records[rid] for rid in ids if rid in self._records)

    def search_by_tag(self, tag: str) -> Tuple[KnowledgeRecord, ...]:
        ids = self._index.find_ids_by_tag(tag)
        return tuple(self._records[rid] for rid in ids if rid in self._records)

    def search_by_source(self, source: str) -> Tuple[KnowledgeRecord, ...]:
        ids = self._index.find_ids_by_source(source)
        return tuple(self._records[rid] for rid in ids if rid in self._records)

    def search(
        self,
        query: str = "",
        category: Optional[str] = None,
        min_confidence: float = 0.0,
        max_results: int = 50,
    ) -> Tuple[KnowledgeRecord, ...]:
        """Simple text-based search across records."""
        results = []
        q_lower = query.lower() if query else ""
        for rec in self._records.values():
            if category and rec.category != category:
                continue
            if rec.confidence < min_confidence:
                continue
            if q_lower:
                if q_lower not in rec.fact.lower() and q_lower not in rec.source.lower():
                    continue
            results.append(rec)
        # Sort by confidence descending, then evidence_count descending
        results.sort(key=lambda r: (r.confidence, r.evidence_count), reverse=True)
        return tuple(results[:max_results])

    # --- Snapshot & Statistics ---

    def create_snapshot(self) -> KnowledgeSnapshot:
        return KnowledgeSnapshot.from_base(self)

    def get_statistics(self) -> KnowledgeStatistics:
        records = list(self._records.values())
        if not records:
            return KnowledgeStatistics()
        categories = set(r.category for r in records)
        sources = set(r.source for r in records)
        avg_conf = sum(r.confidence for r in records) / len(records)
        total_ev = sum(r.evidence_count for r in records)

        # Top categories
        cat_counts: Dict[str, int] = {}
        for r in records:
            cat_counts[r.category] = cat_counts.get(r.category, 0) + 1
        top_cats = tuple(sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:5])

        # Top sources
        src_counts: Dict[str, int] = {}
        for r in records:
            src_counts[r.source] = src_counts.get(r.source, 0) + 1
        top_srcs = tuple(sorted(src_counts.items(), key=lambda x: x[1], reverse=True)[:5])

        return KnowledgeStatistics(
            total_records=len(records),
            total_categories=len(categories),
            total_sources=len(sources),
            avg_confidence=round(avg_conf, 4),
            total_evidence=total_ev,
            top_categories=top_cats,
            top_sources=top_srcs,
        )

    def clear(self) -> None:
        """Reset the knowledge base (for testing / clean startup)."""
        self._records.clear()
        self._index = KnowledgeIndex()

    @property
    def record_count(self) -> int:
        return len(self._records)
