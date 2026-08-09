"""Root Cause Analysis - WP-11 (MISSION-4.2 / IP-4.2-002).

Mengidentifikasi akar penyebab masalah dari evidence operasional.

Berbasis evidence: setiap kandidat penyebab harus didukung evidence yang
dapat ditelusuri (reuse model RCA existing dari operations.rca).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


from .evidence_collection import EvidenceModel


@dataclass(frozen=True)
class RootCauseFinding:
    """Satu hipotesis akar penyebab dengan evidence pendukung."""

    hypothesis: str
    confidence: float = 0.0
    supporting_evidence: Tuple[str, ...] = field(default_factory=tuple)
    missing_evidence: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "hypothesis": self.hypothesis,
            "confidence": self.confidence,
            "supporting_evidence": list(self.supporting_evidence),
            "missing_evidence": list(self.missing_evidence),
        }


@dataclass(frozen=True)
class RootCauseResult:
    """Hasil analisis RCA (evidence-based)."""

    investigation_id: str
    observed_event: str
    findings: Tuple[RootCauseFinding, ...] = field(default_factory=tuple)
    overall_confidence: float = 0.0

    @property
    def top_finding(self) -> Optional[RootCauseFinding]:
        if not self.findings:
            return None
        return max(self.findings, key=lambda f: f.confidence)

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "observed_event": self.observed_event,
            "findings": [f.as_dict() for f in self.findings],
            "overall_confidence": self.overall_confidence,
            "top_finding": (
                self.top_finding.as_dict() if self.top_finding else None
            ),
        }


class RootCauseAnalyzer:
    """Analisis akar penyebab dari evidence (read-only, deterministik)."""

    def analyze(
        self,
        investigation_id: str,
        observed_event: str,
        evidences: Tuple[EvidenceModel, ...],
    ) -> RootCauseResult:
        # Kelompokkan evidence yang mengindikasikan penyimpangan
        abnormal = [
            e for e in evidences if self._is_abnormal(e)
        ]
        findings: List[RootCauseFinding] = []
        if abnormal:
            # Kandidat: sumber dengan evidence abnormal paling banyak
            by_source: Dict[str, List[EvidenceModel]] = {}
            for e in abnormal:
                by_source.setdefault(e.source.source_id, []).append(e)
            total = len(abnormal)
            for source, evs in sorted(
                by_source.items(), key=lambda kv: -len(kv[1])
            ):
                confidence = min(1.0, len(evs) / max(total, 1))
                findings.append(
                    RootCauseFinding(
                        hypothesis=(
                            f"Resource/provider {source} shows "
                            f"{len(evs)} abnormal signal(s)."
                        ),
                        confidence=round(confidence, 3),
                        supporting_evidence=tuple(e.evidence_id for e in evs),
                    )
                )
        overall = (
            max(f.confidence for f in findings) if findings else 0.0
        )
        return RootCauseResult(
            investigation_id=investigation_id,
            observed_event=observed_event,
            findings=tuple(findings),
            overall_confidence=overall,
        )

    @staticmethod
    def _is_abnormal(evidence: EvidenceModel) -> bool:
        for key, value in evidence.data:
            text = str(value).strip().lower()
            if key == "health" and text in ("critical", "degraded"):
                return True
            if key in ("severity", "level") and text in ("critical", "error"):
                return True
        return False
