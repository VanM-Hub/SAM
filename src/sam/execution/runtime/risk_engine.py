"""Risk Engine — rule-based risk assessment."""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.risk import (
    RiskFactor, RiskAssessment, RiskReport, RiskSummary,
)


class RiskEngine:
    """Engine untuk risk assessment — preview-only."""

    def __init__(self) -> None:
        self._assessments: Dict[str, RiskAssessment] = {}

    def assess(self, candidate: ExecutionCandidate) -> RiskAssessment:
        """Nilai risiko untuk satu kandidat."""
        factors: List[RiskFactor] = []

        # Resource complexity
        effort = candidate.estimated_effort
        if effort > 100:
            factors.append(RiskFactor("high_effort", 0.8, f"Effort {effort} > 100"))
        elif effort > 50:
            factors.append(RiskFactor("high_effort", 0.5, f"Effort {effort} > 50"))
        else:
            factors.append(RiskFactor("low_effort", 0.1, f"Effort {effort}"))

        # Dependency count
        dep_count = len(candidate.dependencies)
        if dep_count > 5:
            factors.append(RiskFactor("many_dependencies", 0.7, f"{dep_count} deps"))
        elif dep_count > 2:
            factors.append(RiskFactor("moderate_deps", 0.4, f"{dep_count} deps"))
        else:
            factors.append(RiskFactor("few_deps", 0.1, f"{dep_count} deps"))

        # Priority based (via metadata)
        priority = candidate.metadata.get("priority", 0.0)
        if priority >= 8:
            factors.append(RiskFactor("high_priority", 0.6, f"Priority {priority}"))
        elif priority >= 5:
            factors.append(RiskFactor("medium_priority", 0.3, f"Priority {priority}"))

        # Overall
        overall = round(sum(f.score for f in factors) / max(len(factors), 1), 2)
        level = self._risk_level(overall)

        assessment = RiskAssessment(
            assessment_id=f"risk_{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            overall_score=overall,
            factors=tuple(factors),
            level=level,
        )
        self._assessments[assessment.assessment_id] = assessment
        return assessment

    def assess_batch(self, candidates: List[ExecutionCandidate]) -> List[RiskAssessment]:
        return [self.assess(c) for c in candidates]

    def _risk_level(self, score: float) -> str:
        if score >= 0.7:
            return "critical"
        if score >= 0.5:
            return "high"
        if score >= 0.3:
            return "medium"
        return "low"

    def generate_report(self, report_id: str, execution_plan_id: str,
                        candidates: List[ExecutionCandidate]) -> RiskReport:
        """Generate risk report."""
        assessments = self.assess_batch(candidates)
        scores = [a.overall_score for a in assessments]
        critical = sum(1 for a in assessments if a.level == "critical")

        return RiskReport(
            report_id=report_id,
            execution_plan_id=execution_plan_id,
            assessments=tuple(assessments),
            total_assessments=len(assessments),
            highest_risk=max(scores) if scores else 0.0,
            avg_risk=round(sum(scores) / len(scores), 2) if scores else 0.0,
            critical_count=critical,
        )

    def get_summary(self) -> RiskSummary:
        """Buat ringkasan risiko."""
        scores = [a.overall_score for a in self._assessments.values()]
        crit = sum(1 for a in self._assessments.values() if a.level == "critical")
        high = sum(1 for a in self._assessments.values() if a.level == "high")
        med = sum(1 for a in self._assessments.values() if a.level == "medium")
        low = sum(1 for a in self._assessments.values() if a.level == "low")

        if crit > 0:
            status = "critical_risk"
        elif high > 0:
            status = "high_risk"
        elif med > 0:
            status = "medium_risk"
        else:
            status = "low_risk"

        return RiskSummary(
            total_assessments=len(self._assessments),
            avg_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
            critical_count=crit,
            high_count=high,
            medium_count=med,
            low_count=low,
            status=status,
        )
