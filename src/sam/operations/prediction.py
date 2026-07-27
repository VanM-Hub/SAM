"""
Prediction Engine — 'What happens if nothing is done?'

BUKAN rekomendasi.
Prediksi menjawab: apa yang akan terjadi jika operator tidak melakukan apa-apa.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Prediction:
    """Satu prediksi tentang masa depan."""
    event: str                          # "Memory exceeds safe threshold"
    timeframe: str                      # "within two days"
    risk: str                           # "Medium"
    impact: str                         # "Performance may degrade"
    confidence: float = 0.7
    recommendation_hint: str = ""       # "Restart recommended before threshold"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def display(self) -> str:
        return "{} {}. Risk: {}.".format(self.event, self.timeframe, self.risk)


class PredictionEngine:
    """Menjawab: 'What happens if nothing is done?'"""

    def __init__(self, experience_engine=None):
        self._ee = experience_engine

    def get_predictions(self, situation: str = "",
                        limit: int = 3) -> List[Prediction]:
        """Dapatkan prediksi berdasarkan situasi terkini."""
        preds = []

        try:
            # Situasi-based
            if situation == "waiting_approval":
                preds.append(Prediction(
                    event="Deployment will remain pending",
                    timeframe="until approved",
                    risk="Low",
                    impact="No execution will continue until approval is given.",
                    confidence=0.95,
                    recommendation_hint="Approving takes approximately 2 minutes.",
                ))

            if situation in ("needs_attention", "action_required"):
                preds.append(Prediction(
                    event="Ignoring this may delay operations",
                    timeframe="",
                    risk="Low",
                    impact="Review and action are recommended.",
                    confidence=0.8,
                ))

            # Fallback — everything healthy
            if not preds:
                preds.append(Prediction(
                    event="No issues expected",
                    timeframe="",
                    risk="None",
                    impact="Everything is operating normally.",
                    confidence=0.9,
                ))

        except Exception:
            pass

        return preds[:limit]
