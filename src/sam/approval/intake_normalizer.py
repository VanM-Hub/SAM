"""
Intake Normalizer.

Normalizes ApprovalIntakeRecord into NormalizedApprovalRecord.
"""

from typing import Optional
from dataclasses import dataclass
from .intake_record import ApprovalIntakeRecord


@dataclass(frozen=True)
class NormalizedApprovalRecord:
    normalized_id: str = ""
    original_id: str = ""
    decision_id: str = ""
    source: str = ""
    readiness_score: float = 0.0
    certified: bool = False
    version: str = ""
    category: str = "general"
    label: str = ""
    def to_dict(self) -> dict: return {"normalized_id":self.normalized_id,"original_id":self.original_id,
        "decision_id":self.decision_id,"source":self.source,"readiness_score":self.readiness_score,
        "certified":self.certified,"version":self.version,"category":self.category,"label":self.label}


class IntakeNormalizer:
    def normalize(self, record: ApprovalIntakeRecord) -> NormalizedApprovalRecord:
        source_name = record.metadata.source.name if record.metadata else "MANUAL"
        cat = self._infer_category(source_name)
        return NormalizedApprovalRecord(
            normalized_id=f"norm_{record.record_id}",
            original_id=record.record_id,
            decision_id=record.decision_record_id,
            source=source_name,
            readiness_score=record.readiness_score,
            certified=record.certified,
            version=record.pipeline_version,
            category=cat,
            label=f"intake_{source_name.lower()}",
        )

    @staticmethod
    def _infer_category(source: str) -> str:
        mapping = {"MANUAL": "manual", "DECISION_RUNTIME": "decision", "API": "api", "SYSTEM": "system"}
        return mapping.get(source, "general")
