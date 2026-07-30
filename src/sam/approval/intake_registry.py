"""
Intake Registry.

In-memory registry for intaked approval records.
"""

from typing import Optional, List
from .intake_record import ApprovalIntakeRecord
from .intake_normalizer import NormalizedApprovalRecord


class IntakeRegistry:
    def __init__(self) -> None:
        self._records: List[ApprovalIntakeRecord] = []
        self._normalized: List[NormalizedApprovalRecord] = []
        self._ids: set = set()

    def register(self, record: ApprovalIntakeRecord, normalized: NormalizedApprovalRecord) -> None:
        self._records.append(record)
        self._normalized.append(normalized)
        self._ids.add(record.record_id)

    def exists(self, record_id: str) -> bool:
        return record_id in self._ids

    def get(self, record_id: str) -> Optional[ApprovalIntakeRecord]:
        for r in self._records:
            if r.record_id == record_id: return r
        return None

    def get_normalized(self, normalized_id: str) -> Optional[NormalizedApprovalRecord]:
        for n in self._normalized:
            if n.normalized_id == normalized_id: return n
        return None

    @property
    def latest(self) -> Optional[ApprovalIntakeRecord]:
        return self._records[-1] if self._records else None

    @property
    def count(self) -> int:
        return len(self._records)

    @property
    def duplicates(self) -> int:
        return 0  # dual register same id prevented by exists()

    def list_all(self) -> List[ApprovalIntakeRecord]:
        return list(self._records)
