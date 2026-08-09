"""Diagnosis API - WP-17/18 (MISSION-4.2 / IP-4.2-002).

Menyediakan antarmuka standar & explainability untuk diagnosis operasional.
API read-only, konsisten, dapat diintegrasikan, menghasilkan evidence chain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from .evidence_collection import EvidenceModel
from .operational_diagnosis import OperationalDiagnosis


class DiagnosisNotFoundError(Exception):
    def __init__(self, diagnosis_id: str) -> None:
        super().__init__(f"Diagnosis not found: {diagnosis_id}")
        self.diagnosis_id = diagnosis_id


@dataclass(frozen=True)
class DiagnosisExplanation:
    """Penjelasan diagnosis (evidence chain lengkap)."""

    diagnosis_id: str
    explanation: str
    evidence_chain: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "diagnosis_id": self.diagnosis_id,
            "explanation": self.explanation,
            "evidence_chain": [list(c) for c in self.evidence_chain],
        }


class DiagnosisExplainabilityEngine:
    """Menjelaskan diagnosis dengan evidence chain."""

    def explain(
        self,
        diagnosis: OperationalDiagnosis,
        evidences: Tuple[EvidenceModel, ...],
    ) -> DiagnosisExplanation:
        by_id = {e.evidence_id: e for e in evidences}
        chain = tuple(
            (
                eid,
                by_id[eid].source.source_id if eid in by_id else "unknown",
            )
            for eid in diagnosis.evidence_ids
        )
        return DiagnosisExplanation(
            diagnosis_id=diagnosis.diagnosis_id,
            explanation=(
                f"{diagnosis.root_cause} "
                f"(confidence {diagnosis.confidence.level})."
            ),
            evidence_chain=chain,
        )


class DiagnosisAPI:
    """Public read-only facade untuk diagnosis."""

    def __init__(
        self,
        *,
        engine,
        explainer: Optional[DiagnosisExplainabilityEngine] = None,
    ) -> None:
        self._engine = engine
        self._explainer = explainer or DiagnosisExplainabilityEngine()
        self._diagnoses: Dict[str, OperationalDiagnosis] = {}

    def register_diagnosis(self, diagnosis: OperationalDiagnosis) -> None:
        self._diagnoses[diagnosis.diagnosis_id] = diagnosis

    def get_diagnosis(
        self, diagnosis_id: str
    ) -> Dict[str, Any]:
        diag = self._diagnoses.get(diagnosis_id)
        if diag is None:
            raise DiagnosisNotFoundError(diagnosis_id)
        return diag.as_dict()

    def list_diagnoses(
        self, investigation_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], ...]:
        diags = tuple(self._diagnoses.values())
        if investigation_id:
            diags = tuple(
                d for d in diags if d.investigation_id == investigation_id
            )
        return tuple(d.as_dict() for d in diags)

    def explain_diagnosis(
        self, diagnosis_id: str, evidences: Tuple[EvidenceModel, ...]
    ) -> Dict[str, Any]:
        diag = self._diagnoses.get(diagnosis_id)
        if diag is None:
            raise DiagnosisNotFoundError(diagnosis_id)
        return self._explainer.explain(diag, evidences).as_dict()
