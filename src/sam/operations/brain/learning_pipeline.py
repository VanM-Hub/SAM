"""
OP-265 — Learning Pipeline.

Pipeline yang menghubungkan:
  Observation → Analysis → Recommendation → Outcome → Learning → Knowledge → Optimization

Semua komponen diambil dari pattern_miner, success_estimator, optimizer, feedback_collector.

Output berupa:
  - Pattern list
  - Success estimates
  - Adjusted confidences
  - Feedback summary
  - Knowledge snapshot DTO
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.operations.brain.pattern_miner import (
    PatternMiner, OperationalRecord, PatternDiscoveryResult, build_record,
)
from sam.operations.brain.success_estimator import (
    SuccessEstimator, SuccessEstimate, EvidencePiece, HistoricalOutcome,
)
from sam.operations.brain.optimizer import (
    RecommendationOptimizer, OptimizerResult, OptimizationReport,
)
from sam.operations.brain.feedback_collector import (
    FeedbackCollector, FeedbackSummary, FeedbackEvent,
)


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class LearningPipelineConfig:
    """Configuration for learning pipeline."""
    discovery_window_hours: float = 24.0
    history_window_hours: float = 168.0
    auto_optimize: bool = True
    min_records_for_learning: int = 5


@dataclass
class LearningPipelineResult:
    """Complete result of a learning pipeline run."""
    patterns: PatternDiscoveryResult
    feedback_summary: FeedbackSummary
    optimizations: OptimizationReport
    estimates: List[SuccessEstimate]
    pipeline_elapsed_ms: float = 0.0
    generated_at: float = 0.0
    records_processed: int = 0

    def summary(self) -> Dict[str, Any]:
        return {
            "patterns_found": len(self.patterns.patterns),
            "feedback_events": self.feedback_summary.total_events,
            "optimizations_total": self.optimizations.total_adjusted,
            "estimates_count": len(self.estimates),
            "records_processed": self.records_processed,
            "elapsed_ms": round(self.pipeline_elapsed_ms, 1),
        }


@dataclass
class KnowledgeSnapshot:
    """
    Immutable, versioned, replayable snapshot of learned knowledge.

    Fields:
      - patterns discovered
      - optimized confidences
      - feedback summary
      - source records used
    """
    version_id: str
    created_at: float = 0.0
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    feedback_stats: Dict[str, Any] = field(default_factory=dict)
    optimized_confidences: Dict[str, float] = field(default_factory=dict)
    estimate_history: List[Dict[str, Any]] = field(default_factory=list)
    source_record_count: int = 0
    source_record_window_hours: float = 0.0
    previous_snapshot_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "created_at": self.created_at,
            "patterns": self.patterns,
            "feedback_stats": self.feedback_stats,
            "optimized_confidences": self.optimized_confidences,
            "estimate_history": self.estimate_history[-50:],
            "source_record_count": self.source_record_count,
            "source_window_hours": self.source_record_window_hours,
        }


# ── Pipeline ───────────────────────────────────────────────────────


class LearningPipeline:
    """
    Connects feedback → pattern discovery → optimization → knowledge.

    Steps:
      1. Collect feedback (from FeedbackCollector)
      2. Discover patterns (PatternMiner)
      3. Estimate success (SuccessEstimator)
      4. Optimize confidence (RecommendationOptimizer)
      5. Generate knowledge snapshot
    """

    def __init__(self, config: Optional[LearningPipelineConfig] = None):
        self.config = config or LearningPipelineConfig()
        self.miner = PatternMiner()
        self.estimator = SuccessEstimator()
        self.optimizer = RecommendationOptimizer()
        self.collector = FeedbackCollector()
        self._snapshot_version = 0
        self._last_result: Optional[LearningPipelineResult] = None
        self._last_snapshot: Optional[KnowledgeSnapshot] = None
        self._previous_snapshot_version: Optional[str] = None

    # ── Public API ─────────────────────────────────────────────────

    @property
    def last_result(self) -> Optional[LearningPipelineResult]:
        return self._last_result

    @property
    def last_snapshot(self) -> Optional[KnowledgeSnapshot]:
        return self._last_snapshot

    def run(
        self,
        records: Optional[List[OperationalRecord]] = None,
        optimizations: Optional[Dict[str, float]] = None,
        estimates: Optional[List[Dict[str, Any]]] = None,
    ) -> LearningPipelineResult:
        """
        Run the learning pipeline.

        Args:
          records: Operational records for pattern discovery
          optimizations: Dict of {rec_id: current_confidence} to optimize
          estimates: List of dicts with recommendation data for success estimation
        """
        start = time.time()

        # 1. Feedback summary
        feedback = self.collector.summarize(
            window_hours=self.config.discovery_window_hours
        )

        # 2. Pattern discovery
        recs = records or []
        patterns = self.miner.discover(
            recs, time_window_hours=self.config.discovery_window_hours
        )

        # 3. Success estimates
        estimate_results: List[SuccessEstimate] = []
        for est_data in (estimates or []):
            evidence_list = [
                EvidencePiece(
                    source=e.get("source", ""),
                    type=e.get("type", "observation"),
                    value=e.get("value", ""),
                    weight=e.get("weight", 1.0),
                    confidence=e.get("confidence", 1.0),
                )
                for e in (est_data.get("evidence", []) or [])
            ]
            rec_id = est_data.get("recommendation_id", est_data.get("id", "unknown"))
            title = est_data.get("title", "")
            risk = est_data.get("risk_score", 0.5)
            # Feed historical outcomes for estimation
            hist_outcomes = est_data.get("historical_outcomes", [])
            for ho in hist_outcomes:
                if isinstance(ho, dict):
                    self.estimator.add_outcome(HistoricalOutcome(
                        record_id=ho.get("record_id", ""),
                        source_type=ho.get("source_type", "recommendation"),
                        title=ho.get("title", ""),
                        success=ho.get("success", False),
                        similarity_score=ho.get("similarity", 0.0),
                        timestamp=ho.get("timestamp", time.time()),
                    ))
            estimate = self.estimator.estimate(
                recommendation_id=rec_id,
                title=title,
                evidence=evidence_list or None,
                risk_score=risk,
            )
            estimate_results.append(estimate)

        # 4. Optimize
        opt_confidences = optimizations or {}
        for est in estimate_results:
            if est.recommendation_id not in opt_confidences:
                opt_confidences[est.recommendation_id] = est.probability

        if self.config.auto_optimize and opt_confidences:
            for rec_id, conf in opt_confidences.items():
                self.optimizer.record_outcome(
                    rec_id,
                    feedback.execution_success_rate >= 0.5,
                )

        optimizations_report = self.optimizer.optimize_batch(opt_confidences)

        elapsed = (time.time() - start) * 1000

        result = LearningPipelineResult(
            patterns=patterns,
            feedback_summary=feedback,
            optimizations=optimizations_report,
            estimates=estimate_results,
            pipeline_elapsed_ms=round(elapsed, 1),
            generated_at=time.time(),
            records_processed=len(recs) + len(estimate_results),
        )
        self._last_result = result
        return result

    def snapshot(self) -> KnowledgeSnapshot:
        """
        Create an immutable, versioned knowledge snapshot.

        The snapshot captures:
          - Current patterns
          - Feedback stats
          - Optimized confidences
          - Estimate history
        """
        self._snapshot_version += 1
        version_id = f"v{self._snapshot_version}_{int(time.time())}"

        patterns = []
        if self._last_result:
            patterns = self._last_result.patterns.to_dict_list()

        optimized_confidences: Dict[str, float] = {}
        estimates_history: List[Dict[str, Any]] = []
        if self._last_result:
            for opt in self._last_result.optimizations.results:
                optimized_confidences[opt.recommendation_id] = opt.adjusted_confidence
            estimates_history = [e.to_dict() for e in self._last_result.estimates]

        snapshot = KnowledgeSnapshot(
            version_id=version_id,
            created_at=time.time(),
            patterns=patterns,
            feedback_stats={
                "total_events": self._last_result.feedback_summary.total_events
                    if self._last_result else 0,
                "approval_rate": self._last_result.feedback_summary.approval_rate
                    if self._last_result else 0.0,
                "mission_success_rate":
                    self._last_result.feedback_summary.mission_success_rate
                    if self._last_result else 0.0,
            } if self._last_result else {},
            optimized_confidences=optimized_confidences,
            estimate_history=estimates_history,
            source_record_count=self._last_result.records_processed
                if self._last_result else 0,
            source_record_window_hours=self.config.discovery_window_hours,
            previous_snapshot_version=self._previous_snapshot_version,
        )
        self._previous_snapshot_version = version_id
        self._last_snapshot = snapshot
        return snapshot

    def apply_feedback(self, feedback_events: List[FeedbackEvent]) -> None:
        """Inject feedback events for learning."""
        self.collector.add_bulk(feedback_events)

    def add_historical_outcomes(self, outcomes: List[HistoricalOutcome]) -> None:
        """Pre-populate historical outcomes."""
        self.estimator.add_outcomes(outcomes)


# ── Convenience ────────────────────────────────────────────────────


def learn(
    records: Optional[List[OperationalRecord]] = None,
    optimizations: Optional[Dict[str, float]] = None,
) -> LearningPipelineResult:
    """One-shot: run learning pipeline."""
    pipeline = LearningPipeline()
    return pipeline.run(records=records, optimizations=optimizations)


def create_knowledge_snapshot(
    records: Optional[List[OperationalRecord]] = None,
    confidences: Optional[Dict[str, float]] = None,
) -> KnowledgeSnapshot:
    """One-shot: create a knowledge snapshot."""
    pipeline = LearningPipeline()
    pipeline.run(records=records, optimizations=confidences)
    return pipeline.snapshot()
