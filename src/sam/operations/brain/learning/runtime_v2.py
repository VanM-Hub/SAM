# OP-386 — Learning Runtime V2
# Python 3.8 compatible, frozen dataclass, synchronous only
# Pipeline: Experience → Knowledge Base → Pattern Evolution → Optimizer → Policy → Recommendation → Dashboard DTO → Conversation DTO

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .knowledge_base import (
    KnowledgeBase,
    KnowledgeRecord,
    KnowledgeSnapshot,
    KnowledgeStatistics,
)
from .experience_repository import (
    ExperienceRepository,
    ExperienceRecord,
    ExperienceSummary,
)
from .pattern_evolution import PatternEvolutionEngine, EvolutionSummary
from .optimizer_v2 import RecommendationOptimizerV2, OptimizationSummary
from .policy import LearningPolicyEngine, PolicyDecision


# ---------------------------------------------------------------------------
# Pipeline DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LearningRecommendation:
    """Final recommendation DTO produced by the Learning Pipeline."""
    recommendation_id: str = ""
    category: str = ""
    fact: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    policy_decisions: Tuple[PolicyDecision, ...] = field(default_factory=tuple)
    approved: bool = True
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: str = ""


@dataclass(frozen=True)
class LearningPipelineResult:
    """Complete result of a Learning Pipeline run."""
    experience_count: int = 0
    knowledge_count: int = 0
    knowledge_stats: Optional[KnowledgeStatistics] = None
    evolution_summary: Optional[EvolutionSummary] = None
    optimization_summary: Optional[OptimizationSummary] = None
    recommendations: Tuple[LearningRecommendation, ...] = field(default_factory=tuple)
    pipeline_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# LearningRuntimeV2
# ---------------------------------------------------------------------------

class LearningRuntimeV2:
    """Synchronous Learning Pipeline.

    Pipeline:
    Experience → Knowledge Base → Pattern Evolution → Optimizer → Policy → Recommendation → Dashboard DTO → Conversation DTO

    All steps are deterministic, read-only (except in-memory state), and
    produce immutable DTOs.
    """

    def __init__(
        self,
        knowledge_base: Optional[KnowledgeBase] = None,
        experience_repository: Optional[ExperienceRepository] = None,
        pattern_engine: Optional[PatternEvolutionEngine] = None,
        optimizer: Optional[RecommendationOptimizerV2] = None,
        policy_engine: Optional[LearningPolicyEngine] = None,
    ) -> None:
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.experience_repository = experience_repository or ExperienceRepository()
        self.pattern_engine = pattern_engine or PatternEvolutionEngine()
        self.optimizer = optimizer or RecommendationOptimizerV2()
        self.policy_engine = policy_engine or LearningPolicyEngine()

    # --- Pipeline Execution ---

    def run_pipeline(self) -> LearningPipelineResult:
        """Execute the full learning pipeline.

        1. Collect experience stats
        2. Record knowledge snapshot in pattern engine
        3. Run pattern evolution analysis
        4. Run optimization analysis
        5. Apply learning policies
        6. Generate recommendations
        7. Return PipelineResult DTO
        """
        import time
        start = time.time()

        # Step 1: Experience stats
        exp_count = self.experience_repository.total_count

        # Step 2: Knowledge base snapshot
        knowledge_count = self.knowledge_base.record_count
        knowledge_stats = self.knowledge_base.get_statistics()

        # Step 3: Pattern Evolution
        self.pattern_engine.record_snapshot(self.knowledge_base)
        evolution_summary = self.pattern_engine.analyze(self.knowledge_base)

        # Step 4: Optimization
        optimization_summary = self.optimizer.optimize(
            knowledge_base=self.knowledge_base,
            experience_repo=self.experience_repository,
        )

        # Step 5: Generate policy-evaluated recommendations from knowledge
        records = self.knowledge_base.get_all_records()
        recommendations: List[LearningRecommendation] = []

        for i, rec in enumerate(records):
            policy_decisions = self.policy_engine.evaluate_record(rec)
            approved = all(d.approved for d in policy_decisions)

            # Also check against existing records for duplicate/conflict
            all_records = records  # might include self; policy handles filtering
            rec_decisions = self.policy_engine.evaluate_recommendation(
                category=rec.category,
                fact=rec.fact,
                confidence=rec.confidence,
                evidence_count=rec.evidence_count,
                existing_records=all_records,
            )
            combined = list(policy_decisions) + list(rec_decisions)
            approved_final = all(d.approved for d in combined)

            recommendations.append(LearningRecommendation(
                recommendation_id=f"lr_{rec.record_id[:8]}",
                category=rec.category,
                fact=rec.fact,
                confidence=rec.confidence,
                evidence_count=rec.evidence_count,
                policy_decisions=tuple(combined),
                approved=approved_final,
                source=rec.source,
                details=f"Version {rec.version}",
            ))

        # Step 6: Also create recommendations from evolution insights
        if evolution_summary:
            for cand in evolution_summary.candidates:
                decisions = self.policy_engine.evaluate_recommendation(
                    category=cand.pattern_category,
                    fact=cand.pattern_fact,
                    confidence=cand.current_confidence,
                    evidence_count=cand.evidence_after,
                )
                approved = all(d.approved for d in decisions)
                recommendations.append(LearningRecommendation(
                    recommendation_id=f"lr_evo_{cand.candidate_id[:8]}",
                    category=cand.pattern_category,
                    fact=f"{cand.pattern_fact} [{cand.evolution_type}]",
                    confidence=cand.trend_confidence,
                    evidence_count=cand.evidence_after,
                    policy_decisions=decisions,
                    approved=approved,
                    source="pattern_evolution",
                    details=f"Score: {cand.evolution_score:.4f}",
                ))

        # Sort by confidence descending
        recommendations.sort(key=lambda r: r.confidence, reverse=True)

        elapsed = (time.time() - start) * 1000

        return LearningPipelineResult(
            experience_count=exp_count,
            knowledge_count=knowledge_count,
            knowledge_stats=knowledge_stats,
            evolution_summary=evolution_summary,
            optimization_summary=optimization_summary,
            recommendations=tuple(recommendations),
            pipeline_time_ms=round(elapsed, 2),
        )

    # --- Convenience accessors ---

    def get_knowledge_base(self) -> KnowledgeBase:
        return self.knowledge_base

    def get_experience_repository(self) -> ExperienceRepository:
        return self.experience_repository

    def get_pattern_engine(self) -> PatternEvolutionEngine:
        return self.pattern_engine

    def get_optimizer(self) -> RecommendationOptimizerV2:
        return self.optimizer

    def get_policy_engine(self) -> LearningPolicyEngine:
        return self.policy_engine

    def to_dashboard_dto(self, result: LearningPipelineResult) -> Dict[str, Any]:
        """Convert pipeline result to dashboard-friendly DTO."""
        return {
            "knowledge_count": result.knowledge_count,
            "experience_count": result.experience_count,
            "recommendations": len(result.recommendations),
            "approved": sum(1 for r in result.recommendations if r.approved),
            "rejected": sum(1 for r in result.recommendations if not r.approved),
            "pipeline_time_ms": result.pipeline_time_ms,
            "avg_confidence": round(
                sum(r.confidence for r in result.recommendations) / len(result.recommendations), 4
            ) if result.recommendations else 0.0,
        }

    def to_conversation_dto(self, result: LearningPipelineResult) -> Dict[str, Any]:
        """Convert pipeline result to conversation-friendly DTO."""
        return {
            "summary": f"Learning pipeline completed: {result.knowledge_count} patterns, "
                       f"{len(result.recommendations)} recommendations "
                       f"({sum(1 for r in result.recommendations if r.approved)} approved)",
            "recommendations": [
                {
                    "category": r.category,
                    "confidence": r.confidence,
                    "approved": r.approved,
                    "summary": r.fact[:60],
                }
                for r in result.recommendations[:10]
            ],
        }
