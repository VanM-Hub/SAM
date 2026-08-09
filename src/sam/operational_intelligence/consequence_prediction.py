"""Consequence Prediction - WP-21 (MISSION-4.2 / IP-4.2-003).

Menyusun prediksi konsekuensi sebelum execution dilakukan.
Deterministik, berbasis evidence, read-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from .evidence_collection import EvidenceModel


@dataclass(frozen=True)
class PredictedConsequence:
    """Satu konsekuensi yang diprediksi."""

    consequence_id: str
    description: str
    likelihood: float = 0.0  # 0.0 - 1.0
    magnitude: str = "unknown"  # low | medium | high

    def as_dict(self) -> dict:
        return {
            "consequence_id": self.consequence_id,
            "description": self.description,
            "likelihood": self.likelihood,
            "magnitude": self.magnitude,
        }


@dataclass(frozen=True)
class ConsequencePredictionResult:
    """Hasil prediksi konsekuensi."""

    investigation_id: str
    proposed_action: str
    consequences: Tuple[PredictedConsequence, ...] = field(default_factory=tuple)
    predicted_at: str = ""

    @property
    def riskiest(self) -> Optional[PredictedConsequence]:
        if not self.consequences:
            return None
        return max(
            self.consequences,
            key=lambda c: (c.likelihood, self._mag_val(c.magnitude)),
        )

    @staticmethod
    def _mag_val(magnitude: str) -> int:
        return {"low": 1, "medium": 2, "high": 3}.get(magnitude, 0)

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "proposed_action": self.proposed_action,
            "consequences": [c.as_dict() for c in self.consequences],
            "predicted_at": self.predicted_at,
            "riskiest": self.riskiest.as_dict() if self.riskiest else None,
        }


class ConsequencePredictor:
    """Memprediksi konsekuensi tindakan berdasarkan evidence terkait."""

    def __init__(self, consequence_rules) -> None:
        # consequence_rules: Callable[[str, Tuple[EvidenceModel,...]], List[tuple]]
        self._rules = consequence_rules

    def predict(
        self,
        investigation_id: str,
        proposed_action: str,
        evidences: Tuple[EvidenceModel, ...],
    ) -> ConsequencePredictionResult:
        raw = self._rules(proposed_action, evidences) or []
        consequences = tuple(
            PredictedConsequence(
                consequence_id=f"con-{i}",
                description=desc,
                likelihood=min(1.0, max(0.0, float(likelihood))),
                magnitude=magnitude,
            )
            for i, (desc, likelihood, magnitude) in enumerate(raw, start=1)
        )
        from datetime import datetime

        return ConsequencePredictionResult(
            investigation_id=investigation_id,
            proposed_action=proposed_action,
            consequences=consequences,
            predicted_at=datetime.utcnow().isoformat() + "Z",
        )
