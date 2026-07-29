# OP-388 — Learning Dashboard
# Python 3.8 compatible, frozen dataclass, synchronous only
# Dashboard DTOs for Learning Runtime — presentation layer only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .knowledge_base import KnowledgeRecord, KnowledgeStatistics
from .experience_repository import ExperienceRecord, ExperienceSummary
from .pattern_evolution import EvolutionCandidate, EvolutionSummary
from .optimizer_v2 import OptimizationCandidate, OptimizationSummary
from .policy import LearningPolicy, PolicyDecision
from .runtime_v2 import LearningRecommendation, LearningPipelineResult


# ---------------------------------------------------------------------------
# Dashboard DTOs (frozen dataclasses)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KnowledgeCard:
    """Dashboard card for knowledge base overview."""
    total_records: int = 0
    total_categories: int = 0
    total_sources: int = 0
    avg_confidence: float = 0.0
    total_evidence: int = 0
    top_categories: Tuple[Tuple[str, int], ...] = field(default_factory=tuple)
    top_sources: Tuple[Tuple[str, int], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExperienceCard:
    """Dashboard card for experience repository overview."""
    total_experiences: int = 0
    by_source_type: Dict[str, int] = field(default_factory=dict)
    by_outcome: Dict[str, int] = field(default_factory=dict)
    recent_experiences: Tuple[ExperienceSummary, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PatternCard:
    """Dashboard card for pattern evolution overview."""
    total_analyzed: int = 0
    total_emerging: int = 0
    total_obsolete: int = 0
    total_stable: int = 0
    total_strengthening: int = 0
    total_weakening: int = 0
    avg_evolution_score: float = 0.0
    top_candidates: Tuple[EvolutionCandidate, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OptimizationCard:
    """Dashboard card for optimization overview."""
    total_candidates: int = 0
    total_duplicates: int = 0
    total_conflicts: int = 0
    avg_improvement: float = 0.0
    avg_confidence_adjustment: float = 0.0
    top_optimizations: Tuple[OptimizationCandidate, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TrendCard:
    """Dashboard card for trend overview."""
    recommendations_total: int = 0
    recommendations_approved: int = 0
    recommendations_rejected: int = 0
    recommendations_pending: int = 0
    recent_changes: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PolicyCard:
    """Dashboard card for policy overview."""
    total_policies: int = 0
    active_policies: int = 0
    inactive_policies: int = 0
    policy_names: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LearningDashboard:
    """Complete dashboard DTO for Learning Runtime."""
    knowledge: KnowledgeCard = field(default_factory=KnowledgeCard)
    experience: ExperienceCard = field(default_factory=ExperienceCard)
    patterns: PatternCard = field(default_factory=PatternCard)
    optimization: OptimizationCard = field(default_factory=OptimizationCard)
    trends: TrendCard = field(default_factory=TrendCard)
    policy: PolicyCard = field(default_factory=PolicyCard)
    pipeline_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Dashboard Builder
# ---------------------------------------------------------------------------

class LearningDashboardBuilder:
    """Builds dashboard DTOs from Learning Runtime components.

    No business logic — pure composition of DTOs for presentation.
    """

    @staticmethod
    def build(runtime, pipeline_result: LearningPipelineResult) -> LearningDashboard:
        """Build a complete dashboard from pipeline result and runtime state."""
        # Ensure pipeline was run
        if pipeline_result.knowledge_stats:
            ks = pipeline_result.knowledge_stats
            knowledge_card = KnowledgeCard(
                total_records=ks.total_records,
                total_categories=ks.total_categories,
                total_sources=ks.total_sources,
                avg_confidence=ks.avg_confidence,
                total_evidence=ks.total_evidence,
                top_categories=ks.top_categories,
                top_sources=ks.top_sources,
            )
        else:
            knowledge_card = KnowledgeCard()

        # Experience card
        repo = runtime.get_experience_repository()
        exp_summaries = repo.get_summaries()
        recent = tuple(sorted(
            exp_summaries,
            key=lambda s: s.timestamp,
            reverse=True,
        )[:10])
        experience_card = ExperienceCard(
            total_experiences=repo.total_count,
            by_source_type=repo.count_by_source_type(),
            by_outcome=repo.count_by_outcome(),
            recent_experiences=recent,
        )

        # Pattern card
        if pipeline_result.evolution_summary:
            evo = pipeline_result.evolution_summary
            top = tuple(sorted(
                evo.candidates,
                key=lambda c: c.evolution_score,
                reverse=True,
            )[:5])
            pattern_card = PatternCard(
                total_analyzed=evo.total_analyzed,
                total_emerging=evo.total_emerging,
                total_obsolete=evo.total_obsolete,
                total_stable=evo.total_stable,
                total_strengthening=evo.total_strengthening,
                total_weakening=evo.total_weakening,
                avg_evolution_score=evo.avg_evolution_score,
                top_candidates=top,
            )
        else:
            pattern_card = PatternCard()

        # Optimization card
        if pipeline_result.optimization_summary:
            opt = pipeline_result.optimization_summary
            top_opt = tuple(sorted(
                opt.candidates,
                key=lambda c: c.estimated_improvement,
                reverse=True,
            )[:5])
            optimization_card = OptimizationCard(
                total_candidates=opt.total_candidates,
                total_duplicates=opt.total_duplicates,
                total_conflicts=opt.total_conflicts,
                avg_improvement=opt.avg_improvement,
                avg_confidence_adjustment=opt.avg_confidence_adjustment,
                top_optimizations=top_opt,
            )
        else:
            optimization_card = OptimizationCard()

        # Trend card from recommendations
        recs = pipeline_result.recommendations
        approved = sum(1 for r in recs if r.approved)
        rejected = sum(1 for r in recs if not r.approved)
        recent_changes = tuple(
            f"{r.category}: {'approved' if r.approved else 'rejected'}"
            for r in recs[:5]
        )
        trend_card = TrendCard(
            recommendations_total=len(recs),
            recommendations_approved=approved,
            recommendations_rejected=rejected,
            recommendations_pending=len(recs) - approved - rejected,
            recent_changes=recent_changes,
        )

        # Policy card
        policy_engine = runtime.get_policy_engine()
        policies = policy_engine.list_policies()
        active = sum(1 for p in policies if p.enabled)
        inactive = len(policies) - active
        policy_card = PolicyCard(
            total_policies=len(policies),
            active_policies=active,
            inactive_policies=inactive,
            policy_names=tuple(p.name for p in policies),
        )

        return LearningDashboard(
            knowledge=knowledge_card,
            experience=experience_card,
            patterns=pattern_card,
            optimization=optimization_card,
            trends=trend_card,
            policy=policy_card,
            pipeline_time_ms=pipeline_result.pipeline_time_ms,
        )
