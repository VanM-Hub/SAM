"""
RootCauseModel — evidence-based RCA model untuk Conversation integration.

Tidak ada asumsi. Setiap kesimpulan harus punya evidence yang bisa ditelusuri.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class RootCauseEvidence:
    """Satu bukti konkret dalam RCA."""
    source: str                 # runtime_provider, workspace_provider, telemetry, queue_monitor
    metric: str                 # cpu_percent, queue_depth, disk_percent, etc.
    value: Any                  # Nilai aktual
    threshold: Any              # Nilai threshold/baseline
    severity: str               # normal, warning, critical
    detail: str = ""            # Deskripsi tambahan


@dataclass
class CandidateCause:
    """Satu kandidat penyebab yang diusulkan."""
    hypothesis: str             # "CPU high because queue processing is active"
    evidence: List[RootCauseEvidence] = field(default_factory=list)
    confidence: float = 0.0     # 0.0 - 1.0
    missing_evidence: List[str] = field(default_factory=list)


@dataclass
class RootCauseModel:
    """Hasil analisis RCA untuk satu pertanyaan 'Why?'."""
    question: str                           # "Why is CPU high?"
    observed_event: str                     # "CPU at 92.5%"
    possible_causes: List[CandidateCause] = field(default_factory=list)
    confidence: float = 0.0                 # Overall confidence
    missing_information: List[str] = field(default_factory=list)
    recommended_next_observation: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "observed_event": self.observed_event,
            "possible_causes": [
                {
                    "hypothesis": c.hypothesis,
                    "evidence": [
                        {
                            "source": e.source,
                            "metric": e.metric,
                            "value": e.value,
                            "threshold": e.threshold,
                            "severity": e.severity,
                            "detail": e.detail,
                        }
                        for e in c.evidence
                    ],
                    "confidence": c.confidence,
                    "missing_evidence": c.missing_evidence,
                }
                for c in self.possible_causes
            ],
            "confidence": self.confidence,
            "missing_information": self.missing_information,
            "recommended_next_observation": self.recommended_next_observation,
            "timestamp": self.timestamp,
        }


@dataclass
class RootCauseReport:
    """Ringkasan RCA untuk dimasukkan ke ConversationObject."""
    summary: str
    root_cause: Optional[str] = None
    confidence: float = 0.0
    supporting_evidence: List[str] = field(default_factory=list)
    missing_observations: List[str] = field(default_factory=list)

    def to_text(self) -> str:
        lines = []
        if self.root_cause:
            lines.append("Root cause: {}".format(self.root_cause))
            lines.append("Confidence: {:.0f}%".format(self.confidence * 100))
            for e in self.supporting_evidence:
                lines.append("  - {}".format(e))
        lines.append("Insufficient evidence." if not self.root_cause else "")
        if self.missing_observations:
            lines.append("Additional observations required:")
            for m in self.missing_observations:
                lines.append("  - {}".format(m))
        return "\n".join(l for l in lines if l)
