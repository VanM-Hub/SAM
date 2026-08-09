"""Knowledge Validation - WP-25 (MISSION-4.3 / IP-4.3-003).

Memvalidasi pengetahuan yang telah dibangun (evidence & confidence).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .operational_knowledge import KnowledgeEntry


@dataclass(frozen=True)
class ValidationResult:
    """Hasil validasi sebuah knowledge."""

    knowledge_id: str
    valid: bool
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "knowledge_id": self.knowledge_id,
            "valid": self.valid,
            "reasons": list(self.reasons),
        }


class KnowledgeValidator:
    """Memvalidasi knowledge (evidence & confidence minimum)."""

    MIN_CONFIDENCE = 0.3

    def validate(self, entry: KnowledgeEntry) -> ValidationResult:
        reasons: List[str] = []
        valid = True
        if not entry.evidence_ids:
            valid = False
            reasons.append("no evidence")
        if entry.confidence < self.MIN_CONFIDENCE:
            valid = False
            reasons.append("low confidence")
        if not entry.content:
            valid = False
            reasons.append("empty content")
        if valid:
            reasons.append("valid")
        return ValidationResult(
            knowledge_id=entry.knowledge_id, valid=valid, reasons=tuple(reasons)
        )

    def validate_many(
        self, entries: Tuple[KnowledgeEntry, ...]
    ) -> Tuple[ValidationResult, ...]:
        return tuple(self.validate(e) for e in entries)
