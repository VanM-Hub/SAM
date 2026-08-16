"""Environment-adaptive: pengukuran confidence berbasis evidence.

SAM tidak mengarang diagnosis. Confidence diturunkan dari jumlah & kualitas
sumber evidence independen. Bila evidence tidak cukup, SAM menyatakan
"evidence tidak cukup" (INSUFFICIENT) - TIDAK menebak.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    INSUFFICIENT = "insufficient"   # evidence tidak cukup -> jangan putuskan


@dataclass(frozen=True)
class Evidence:
    """Satu fakta evidence (jujur, traceable)."""

    source: str           # mekanisme/sumber (mis. process_table, probe_x)
    statement: str        # apa yang diamati
    strength: float = 1.0 # bobot 0..1 (seberapa kuat kesimpulan ini)
    negative: bool = False  # evidence tentang KETIDAKHADIRAN
    causal: bool = False  # evidence ini membawa HUBUNGAN KAUSAL (bukan sekadar anomali)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "statement": self.statement,
            "strength": self.strength,
            "negative": self.negative,
            "causal": self.causal,
        }


class ConfidenceAssessor:
    """Menilai confidence sebuah hipotesis/kesimpulan dari kumpulan evidence.

    Aturan (deterministik):
      - min 2 sumber independen dengan strength >= 0.7 -> HIGH
      - min 1 sumber strength >= 0.7 (atau 2 lemah)     -> MEDIUM
      - ada 1 evidence lemah saja                        -> LOW
      - tidak ada evidence yang mendukung                -> INSUFFICIENT
      - ada counter-evidence kuat -> INSUFFICIENT (jangan dikarang)
    """

    def assess(self, evidence: List[Evidence]) -> ConfidenceLevel:
        supporting = [e for e in evidence if not e.negative]
        counter = [e for e in evidence if e.negative]

        # counter kuat membatalkan kesimpulan (honest)
        strong_counter = [e for e in counter if e.strength >= 0.8]
        if strong_counter:
            return ConfidenceLevel.INSUFFICIENT

        if not supporting:
            return ConfidenceLevel.INSUFFICIENT

        strong = [e for e in supporting if e.strength >= 0.7]
        sources = {e.source for e in strong}

        if len(strong) >= 2 and len(sources) >= 2:
            return ConfidenceLevel.HIGH
        if len(strong) >= 1:
            return ConfidenceLevel.MEDIUM
        if len(supporting) >= 2:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def confidence_score(self, evidence: List[Evidence]) -> float:
        level = self.assess(evidence)
        if level == ConfidenceLevel.HIGH:
            return 0.9
        if level == ConfidenceLevel.MEDIUM:
            return 0.6
        if level == ConfidenceLevel.LOW:
            return 0.3
        return 0.0
