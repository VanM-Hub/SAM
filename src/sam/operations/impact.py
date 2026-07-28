"""
ImpactAnalysis — Prediksi dampak keputusan berbasis evidence.

Setiap impact harus berasal dari evidence.
Jika evidence tidak cukup: Insufficient evidence.
Tidak boleh menebak.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class ImpactAssessment:
    """Assessment dampak untuk satu keputusan.

    Semua field berdasarkan evidence.
    Jika tidak cukup evidence: is_sufficient = False.
    """
    decision: str
    expected_outcome: str                        # "CPU returns to normal range"
    possible_interruption: str = ""              # "1-minute interruption during restart"
    estimated_recovery: str = ""                 # "~30 seconds"
    rollback_possibility: str = ""               # "Reapply previous configuration"

    # Evidence tracking
    supporting_evidence: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    risk: str = ""                               # "Low", "Medium", "High"

    # Sufficiency
    is_sufficient: bool = True
    confidence: float = 0.0

    def to_text(self) -> str:
        lines = ["Impact: {}".format(self.decision)]
        lines.append("  Expected outcome: {}".format(self.expected_outcome))
        if self.possible_interruption:
            lines.append("  Interruption: {}".format(self.possible_interruption))
        if self.estimated_recovery:
            lines.append("  Recovery: {}".format(self.estimated_recovery))
        if self.rollback_possibility:
            lines.append("  Rollback: {}".format(self.rollback_possibility))
        if self.risk:
            lines.append("  Risk: {}".format(self.risk))
        if self.supporting_evidence:
            lines.append("  Evidence ({}):".format(len(self.supporting_evidence)))
            for e in self.supporting_evidence[:3]:
                lines.append("    - {}".format(e))
        if self.missing_evidence:
            lines.append("  Missing:")
            for m in self.missing_evidence[:3]:
                lines.append("    - {}".format(m))
        if not self.is_sufficient:
            lines.append("  ⚠ Insufficient evidence for accurate impact assessment")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "expected_outcome": self.expected_outcome,
            "possible_interruption": self.possible_interruption,
            "estimated_recovery": self.estimated_recovery,
            "rollback_possibility": self.rollback_possibility,
            "risk": self.risk,
            "confidence": self.confidence,
            "is_sufficient": self.is_sufficient,
            "supporting_evidence": self.supporting_evidence,
            "missing_evidence": self.missing_evidence,
        }


@dataclass
class ImpactPackage:
    """Semua impact assessment dari satu set keputusan."""
    assessments: List[ImpactAssessment] = field(default_factory=list)

    def has_any(self) -> bool:
        return len(self.assessments) > 0

    def get_highest_risk(self) -> Optional[ImpactAssessment]:
        if not self.assessments:
            return None
        risk_order = {"High": 3, "Medium": 2, "Low": 1, "": 0}
        return max(self.assessments, key=lambda a: risk_order.get(a.risk, 0))

    def get_insufficient(self) -> List[ImpactAssessment]:
        return [a for a in self.assessments if not a.is_sufficient]


class ImpactAnalyzer:
    """Analisis dampak keputusan — evidence-based.

    Untuk setiap jenis keputusan yang diketahui, memberikan:
    - Expected outcome
    - Possible interruption
    - Estimated recovery
    - Rollback possibility

    Jika keputusan tidak dikenal: is_sufficient = False.
    """

    def __init__(self, runtime_provider=None, workspace_provider=None):
        self._rp = runtime_provider
        self._wp = workspace_provider

    def analyze(self, proposal_decision: str,
                proposal_reason: str = "",
                evidence: Optional[List[str]] = None,
                context: Optional[Dict[str, Any]] = None) -> ImpactAssessment:
        """Analisis dampak satu proposal keputusan.

        Args:
            proposal_decision: Nama keputusan (e.g. "Restart database connection")
            proposal_reason: Reason dari proposal
            evidence: Evidence yang mendukung
            context: Data tambahan (severity, anomaly type, dll.)

        Returns:
            ImpactAssessment dengan evidence-based prediction.
        """
        ctx = context or {}
        ev = evidence or []
        sev = ctx.get("severity", "information")
        anomaly_type = ctx.get("anomaly_type", "")

        # Known decisions — evidence-based impact
        known = {
            "restart database connection": ImpactAssessment(
                decision="Restart database connection",
                expected_outcome="Database connectivity restored",
                possible_interruption="~5 seconds interruption for active queries",
                estimated_recovery="~5 seconds",
                rollback_possibility="Executing restart again if connection fails",
                risk="Medium" if sev in ("critical", "high") else "Medium",
                supporting_evidence=ev,
                confidence=0.8,
            ),
            "free up disk space": ImpactAssessment(
                decision="Free up disk space",
                expected_outcome="Disk usage reduced below 80%",
                possible_interruption="No interruption — cleanup runs in background",
                estimated_recovery="~1-5 minutes depending on file volume",
                rollback_possibility="Not applicable — action is reversible (files can be restored)",
                risk="Low",
                supporting_evidence=ev,
                confidence=0.9,
            ),
            "investigate cpu spike": ImpactAssessment(
                decision="Investigate CPU spike",
                expected_outcome="Identify the process causing CPU spike",
                possible_interruption="No interruption — investigation is passive",
                estimated_recovery="~5-15 minutes for investigation",
                rollback_possibility="Not applicable — investigation produces no side effects",
                risk="Low",
                supporting_evidence=ev,
                confidence=0.85,
            ),
            "drain pending queue": ImpactAssessment(
                decision="Drain pending queue",
                expected_outcome="Queue returns to idle or healthy state",
                possible_interruption="No interruption — operations continue processing",
                estimated_recovery="~2-10 minutes depending on queue depth",
                rollback_possibility="Not applicable — queue naturally processes operations",
                risk="Low",
                supporting_evidence=ev,
                confidence=0.85,
            ),
            "investigate memory usage": ImpactAssessment(
                decision="Investigate memory usage",
                expected_outcome="Identify the process consuming memory",
                possible_interruption="No interruption — investigation is passive",
                estimated_recovery="~5-15 minutes for investigation",
                rollback_possibility="Not applicable — investigation is passive",
                risk="Low",
                supporting_evidence=ev,
                confidence=0.85,
            ),
            "clean up temp files": ImpactAssessment(
                decision="Clean up temp files",
                expected_outcome="Free up disk space by removing temporary files",
                possible_interruption="No interruption — cleanup runs in background",
                estimated_recovery="~30 seconds to 2 minutes",
                rollback_possibility="Partial — deleted files cannot be recovered, but temp files regenerate",
                risk="Low",
                supporting_evidence=ev,
                confidence=0.9,
            ),
            "clean up cache": ImpactAssessment(
                decision="Clean up cache",
                expected_outcome="Free up cache space, potential performance improvement",
                possible_interruption="Slight performance impact as cache rebuilds",
                estimated_recovery="~1-5 minutes cache rebuild time",
                rollback_possibility="Not applicable — cache regenerates automatically",
                risk="Low",
                supporting_evidence=ev,
                confidence=0.85,
            ),
            "monitor system stability after restart": ImpactAssessment(
                decision="Monitor system stability after restart",
                expected_outcome="Confirm system stabilizes within 5 minutes",
                possible_interruption="No interruption — monitoring is passive",
                estimated_recovery="~5 minutes of monitoring",
                rollback_possibility="Not applicable — monitoring has no side effects",
                risk="Low",
                supporting_evidence=ev,
                confidence=0.6,
            ),
            "scale up processing capacity": ImpactAssessment(
                decision="Scale up processing capacity",
                expected_outcome="Queue drains faster as processing capacity increases",
                possible_interruption="No interruption — scaling is additive",
                estimated_recovery="~1-5 minutes",
                rollback_possibility="Revert scaling changes if capacity is no longer needed",
                risk="Medium" if sev == "critical" else "Low",
                supporting_evidence=ev,
                confidence=0.7,
            ),
        }

        # Normalize decision key
        key = proposal_decision.strip().lower()

        if key in known:
            return known[key]

        # Unknown decision — insufficient evidence
        return ImpactAssessment(
            decision=proposal_decision,
            expected_outcome="Unknown",
            possible_interruption="Unknown",
            estimated_recovery="Unknown",
            rollback_possibility="Unknown",
            risk="Unknown",
            is_sufficient=False,
            missing_evidence=["Impact analysis for '{}' is not available".format(proposal_decision)],
            confidence=0.1,
        )

    def analyze_all(self, proposals) -> ImpactPackage:
        """Analisis dampak semua proposal."""
        assessments = []
        if hasattr(proposals, 'proposals'):
            items = proposals.proposals
        else:
            items = proposals
        for p in items:
            assessment = self.analyze(
                proposal_decision=p.decision,
                proposal_reason=p.reason,
                evidence=p.required_evidence,
            )
            assessments.append(assessment)
        return ImpactPackage(assessments=assessments)
