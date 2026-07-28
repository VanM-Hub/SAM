"""
OP-267 — Integration.

Pipeline Sprint 21 — Learning:

  Observation → Analysis → Recommendation → Outcome → Learning → Knowledge → Optimization

Connects Sprint 21 components into one pipeline.
Output: LearningAndOptimizationResult.
"""

from __future__ import annotations

import time as time_module
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.operations.brain.pattern_miner import (
    PatternMiner, PatternDiscoveryResult, OperationalRecord, build_record,
)
from sam.operations.brain.success_estimator import (
    SuccessEstimator, SuccessEstimate, EvidencePiece, HistoricalOutcome,
)
from sam.operations.brain.optimizer import (
    RecommendationOptimizer, OptimizationReport,
)
from sam.operations.brain.feedback_collector import (
    FeedbackCollector, FeedbackSummary, FeedbackEvent,
)
from sam.operations.brain.learning_pipeline import (
    LearningPipeline, KnowledgeSnapshot, LearningPipelineResult,
)
from sam.operations.brain.dashboard_brain import (
    DashboardBrainV2, DashboardStateV2, Insight,
)


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class LearningAndOptimizationResult:
    """Complete output of the Sprint 21 integration pipeline."""
    learning: LearningPipelineResult
    knowledge: KnowledgeSnapshot
    dashboard: DashboardStateV2
    elapsed_ms: float = 0.0
    timestamp: float = 0.0

    def summary(self) -> Dict[str, Any]:
        return {
            "patterns": len(self.learning.patterns.patterns),
            "feedback_events": self.learning.feedback_summary.total_events,
            "optimizations": self.learning.optimizations.total_adjusted,
            "estimates": len(self.learning.estimates),
            "insights": len(self.dashboard.insights),
            "snapshot_version": self.knowledge.version_id,
            "elapsed_ms": round(self.elapsed_ms, 1),
        }


class LearningIntegration:
    """
    End-to-end integration for Sprint 21.

    Connects:
      Feedback → Patterns → Estimates → Optimizations → Knowledge → Dashboard
    """

    def __init__(self):
        self.pipeline = LearningPipeline()
        self.dashboard = DashboardBrainV2()
        self._last_result: Optional[LearningAndOptimizationResult] = None

    @property
    def last_result(self) -> Optional[LearningAndOptimizationResult]:
        return self._last_result

    def run(
        self,
        operational_records: Optional[List[OperationalRecord]] = None,
        existing_confidences: Optional[Dict[str, float]] = None,
        estimate_inputs: Optional[List[Dict[str, Any]]] = None,
        observation_summary: Optional[Dict[str, Any]] = None,
        approval_rate: float = 0.0,
        mission_success_rate: float = 0.0,
    ) -> LearningAndOptimizationResult:
        start = time_module.time()

        # 1. Run learning pipeline
        learning = self.pipeline.run(
            records=operational_records,
            optimizations=existing_confidences,
            estimates=estimate_inputs,
        )

        # 2. Create knowledge snapshot
        knowledge = self.pipeline.snapshot()

        # 3. Compute dashboard with insights
        dashboard = self.dashboard.compute(
            observation_summary=observation_summary,
            health_score=learning.feedback_summary.avg_health_score or 1.0,
            health_state=(
                "healthy" if (learning.feedback_summary.avg_health_score or 1.0) >= 0.8
                else "degraded"
            ),
            patterns_found=len(learning.patterns.patterns),
            feedback_events=learning.feedback_summary.total_events,
            optimizations_applied=learning.optimizations.total_adjusted,
            approval_rate=approval_rate or learning.feedback_summary.approval_rate,
            mission_success_rate=mission_success_rate or learning.feedback_summary.mission_success_rate,
            snapshot_version=knowledge.version_id,
        )

        elapsed = (time_module.time() - start) * 1000
        result = LearningAndOptimizationResult(
            learning=learning,
            knowledge=knowledge,
            dashboard=dashboard,
            elapsed_ms=round(elapsed, 1),
            timestamp=time_module.time(),
        )
        self._last_result = result
        return result


# ── Convenience ────────────────────────────────────────────────────


def run_learning_integration(
    records: Optional[List[OperationalRecord]] = None,
    confidences: Optional[Dict[str, float]] = None,
    approval_rate: float = 0.0,
    mission_rate: float = 0.0,
) -> LearningAndOptimizationResult:
    """One-shot: run full learning integration."""
    integration = LearningIntegration()
    return integration.run(
        operational_records=records,
        existing_confidences=confidences,
        approval_rate=approval_rate,
        mission_success_rate=mission_rate,
    )
