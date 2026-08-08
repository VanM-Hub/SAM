# Operational Risk Assessment - WP-44
# IP-3.2-005 (AO-3.2-001 / ED-3.2-005)
#
# Menilai risiko operasional berdasarkan dimensi kesiapan & blocker.
# Mengidentifikasi "risiko terbesar" (highest risk) secara deterministik.
# Prinsip: HANYA menilai & menyusun peringkat risiko - TIDAK memilih tindakan
# mitigasi, TIDAK menjalankan. Output = risk assessment (read-only).
# Deterministic: skor risiko = f(severity, likelihood, dampak).

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.operational_readiness.models import OperationalReadiness


@dataclass(frozen=True)
class OperationalRisk:
    """Satu risiko operasional dengan skor (immutable)."""

    risk_id: str
    name: str
    severity: str  # low | medium | high | critical
    likelihood: str  # low | medium | high
    score: float  # 0.0 - 1.0, deterministik
    basis: str = ""
    affected_dimension: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "name": self.name,
            "severity": self.severity,
            "likelihood": self.likelihood,
            "score": self.score,
            "basis": self.basis,
            "affected_dimension": self.affected_dimension,
        }

    def is_critical(self) -> bool:
        return self.score >= 0.7


@dataclass(frozen=True)
class OperationalRiskReport:
    """Laporan risiko operasional (immutable, read-only)."""

    report_id: str
    readiness_id: str
    overall_risk: str = "low"  # low | medium | high | critical
    risks: Tuple[OperationalRisk, ...] = ()
    top_risks: Tuple[str, ...] = ()
    is_proposal_only: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "readiness_id": self.readiness_id,
            "overall_risk": self.overall_risk,
            "risks": [r.as_dict() for r in self.risks],
            "top_risks": list(self.top_risks),
            "is_proposal_only": self.is_proposal_only,
            "metadata": dict(self.metadata),
        }

    def risk_count(self) -> int:
        return len(self.risks)

    def highest_risk(self) -> Optional[OperationalRisk]:
        if not self.risks:
            return None
        return max(self.risks, key=lambda r: r.score)


class OperationalRiskAssessor:
    """Menilai risiko operasional dari penilaian kesiapan (deterministik)."""

    def assess(
        self,
        readiness: OperationalReadiness,
        report_id: str = "",
    ) -> OperationalRiskReport:
        risks: List[OperationalRisk] = []
        seen: set = set()

        # risiko per dimensi yang tidak siap / di bawah ambang
        for d in readiness.dimensions:
            if not d.ready:
                severity = self._severity_for_dimension(d.name, d.score)
                likelihood = "high" if d.score < 0.3 else "medium"
                score = self._risk_score(severity, likelihood)
                risk_id = self._stable_id("d-{}".format(d.name))
                risks.append(OperationalRisk(
                    risk_id=risk_id, name="{} dimension unready".format(d.name),
                    severity=severity, likelihood=likelihood, score=score,
                    basis=d.detail, affected_dimension=d.name,
                ))
                seen.add(d.name)

        # risiko dari blocker
        for b in readiness.blockers:
            if b in seen:
                continue
            severity = "high" if "missing" in b else "medium"
            score = self._risk_score(severity, "medium")
            risks.append(OperationalRisk(
                risk_id=self._stable_id("b-{}".format(b)), name=b,
                severity=severity, likelihood="medium", score=score,
                basis="blocker from readiness integration",
            ))

        # urutkan deterministik: score desc, lalu name asc
        risks.sort(key=lambda r: (-r.score, r.name))

        if risks:
            overall = risks[0].severity if risks[0].score >= 0.7 else "medium"
            top_risks = tuple(r.name for r in risks[:3])
        else:
            overall = "low"
            top_risks = ()

        return OperationalRiskReport(
            report_id=report_id or self._stable_id(readiness.readiness_id),
            readiness_id=readiness.readiness_id,
            overall_risk=overall,
            risks=tuple(risks),
            top_risks=top_risks,
            is_proposal_only=True,
            metadata={"deterministic": True},
        )

    # --- helpers ---

    @staticmethod
    def _severity_for_dimension(name: str, score: float) -> str:
        if score < 0.3:
            return "critical" if name in ("recover", "coordinate", "lifecycle") else "high"
        return "medium"

    @staticmethod
    def _risk_score(severity: str, likelihood: str) -> float:
        sev = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}.get(severity, 0.5)
        lik = {"low": 0.3, "medium": 0.6, "high": 0.9}.get(likelihood, 0.6)
        return round(sev * 0.6 + lik * 0.4, 4)

    @staticmethod
    def _stable_id(seed: str) -> str:
        return "ar-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
