"""Quality Engine — rule-based quality validation."""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.quality import QualityMetric, QualityAssessment, QualityGate, QualitySummary


class QualityEngine:
    """Engine validasi kualitas — preview-only."""

    def __init__(self) -> None:
        self._assessments: Dict[str, QualityAssessment] = {}
        self._gates: Dict[str, QualityGate] = {}

    def assess(self, assessment_id: str, execution_plan_id: str,
               candidates: List[ExecutionCandidate]) -> QualityAssessment:
        """Nilai kualitas berdasarkan kandidat."""
        metrics: List[QualityMetric] = []
        total_weight = 0.0

        # Metric: effort variability
        if candidates:
            efforts = [c.estimated_effort for c in candidates]
            avg = sum(efforts) / len(efforts)
            variance = sum((e - avg) ** 2 for e in efforts) / len(efforts)
            var_score = max(0.0, 1.0 - variance / 100.0)
            metrics.append(QualityMetric("effort_variance", round(var_score, 2), 1.0,
                                        f"Variance score {var_score:.2f}"))
            total_weight += 1.0

        # Metric: dependency coverage
        deps_count = sum(len(c.dependencies) for c in candidates)
        dep_score = min(1.0, deps_count / max(len(candidates), 1) / 3.0)
        metrics.append(QualityMetric("dependency_coverage", round(dep_score, 2), 0.8,
                                    f"Deps coverage {dep_score:.2f}"))
        total_weight += 0.8

        # Metric: type diversity
        types = set(c.candidate_type for c in candidates)
        type_score = len(types) / 4.0
        metrics.append(QualityMetric("type_diversity", round(min(1.0, type_score), 2), 0.5,
                                    f"Types: {len(types)}"))
        total_weight += 0.5

        overall = sum(m.score * m.weight for m in metrics) / total_weight if total_weight > 0 else 0.0

        assessment = QualityAssessment(
            assessment_id=assessment_id,
            execution_plan_id=execution_plan_id,
            metrics=tuple(metrics),
            overall_score=round(overall, 2),
            total_weight=round(total_weight, 2),
            category="execution",
        )
        self._assessments[assessment_id] = assessment
        return assessment

    def create_gate(self, gate_id: str, name: str, threshold: float = 0.8) -> QualityGate:
        gate = QualityGate(gate_id=gate_id, name=name, threshold=threshold)
        self._gates[gate_id] = gate
        return gate

    def evaluate_gate(self, gate_id: str, score: float) -> QualityGate:
        old = self._gates.get(gate_id)
        if not old:
            return QualityGate(gate_id=gate_id, name="unknown")

        failures: List[str] = []
        if score < old.threshold:
            failures.append(f"Score {score} < threshold {old.threshold}")

        gate = QualityGate(
            gate_id=old.gate_id,
            name=old.name,
            threshold=old.threshold,
            passed=score >= old.threshold,
            score=round(score, 2),
            failures=tuple(failures),
        )
        self._gates[gate_id] = gate
        return gate

    def get_summary(self) -> QualitySummary:
        scores = [a.overall_score for a in self._assessments.values()]
        passed = sum(1 for g in self._gates.values() if g.passed)
        failed = sum(1 for g in self._gates.values() if not g.passed and g.score > 0)

        if failed > 0:
            status = "gates_failed"
        elif passed > 0:
            status = "gates_passed"
        else:
            status = "unknown"

        return QualitySummary(
            total_assessments=len(self._assessments),
            avg_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
            gates_passed=passed,
            gates_failed=failed,
            status=status,
        )
