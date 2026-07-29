# OP-387 — Conversation Learning Bridge
# Python 3.8 compatible, frozen dataclass, synchronous only
# Read-only query interface for Conversation API to access learning runtime

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .runtime_v2 import LearningRuntimeV2, LearningPipelineResult, LearningRecommendation
from .knowledge_base import KnowledgeRecord, KnowledgeStatistics
from .experience_repository import ExperienceRecord, ExperienceSummary
from .optimizer_v2 import OptimizationSummary
from .pattern_evolution import EvolutionSummary
from .policy import LearningPolicyEngine, LearningPolicy, PolicyDecision


# ---------------------------------------------------------------------------
# Query Result DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LearningQueryResult:
    """Standard DTO for conversation learning queries."""
    query_type: str = ""
    data: Any = None
    count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# ConversationLearningBridge
# ---------------------------------------------------------------------------

class ConversationLearningBridge:
    """Read-only query bridge between Conversation API and Learning Runtime.

    Supports queries:
    - learning summary
    - knowledge
    - patterns
    - experience
    - optimization
    - confidence
    - recommendation
    - history
    - trend
    - policy

    All methods return immutable DTOs. No mutation of learning state.
    """

    def __init__(self, runtime: LearningRuntimeV2) -> None:
        self._runtime = runtime

    # --- Query Dispatcher ---

    def query(self, query_type: str, params: Optional[Dict[str, Any]] = None) -> LearningQueryResult:
        """Dispatch a query to the appropriate handler."""
        params = params or {}
        handlers = {
            "learning summary": self._query_summary,
            "knowledge": self._query_knowledge,
            "patterns": self._query_patterns,
            "experience": self._query_experience,
            "optimization": self._query_optimization,
            "confidence": self._query_confidence,
            "recommendation": self._query_recommendation,
            "history": self._query_history,
            "trend": self._query_trend,
            "policy": self._query_policy,
        }
        handler = handlers.get(query_type.lower())
        if handler is None:
            return LearningQueryResult(
                query_type=query_type,
                data={"error": f"Unknown query type: {query_type}"},
                count=0,
            )
        return handler(params)

    # --- Individual Handlers ---

    def _query_summary(self, params: Dict[str, Any]) -> LearningQueryResult:
        """Get overall learning summary."""
        result = self._runtime.run_pipeline()
        data = self._runtime.to_conversation_dto(result)
        return LearningQueryResult(
            query_type="learning summary",
            data=data,
            count=1,
        )

    def _query_knowledge(self, params: Dict[str, Any]) -> LearningQueryResult:
        """Query knowledge base."""
        kb = self._runtime.get_knowledge_base()
        records = kb.get_all_records()
        stats = kb.get_statistics()

        # Filter by category if specified
        category = params.get("category")
        if category:
            records = kb.search_by_category(category)

        data = {
            "total_records": len(records),
            "statistics": {
                "total_categories": stats.total_categories,
                "total_sources": stats.total_sources,
                "avg_confidence": stats.avg_confidence,
                "total_evidence": stats.total_evidence,
            },
            "records": [
                {
                    "id": r.record_id[:8],
                    "category": r.category,
                    "fact": r.fact[:60],
                    "confidence": r.confidence,
                    "evidence": r.evidence_count,
                    "source": r.source,
                }
                for r in sorted(
                    records,
                    key=lambda x: x.confidence,
                    reverse=True,
                )[:50]
            ],
        }
        return LearningQueryResult(
            query_type="knowledge",
            data=data,
            count=len(records),
        )

    def _query_patterns(self, params: Dict[str, Any]) -> LearningQueryResult:
        """Query pattern evolution analysis."""
        pattern_engine = self._runtime.get_pattern_engine()
        kb = self._runtime.get_knowledge_base()
        evo = pattern_engine.analyze(kb)

        data = {
            "total_analyzed": evo.total_analyzed,
            "emerging": evo.total_emerging,
            "obsolete": evo.total_obsolete,
            "stable": evo.total_stable,
            "strengthening": evo.total_strengthening,
            "weakening": evo.total_weakening,
            "avg_evolution_score": evo.avg_evolution_score,
            "candidates": [
                {
                    "type": c.evolution_type,
                    "category": c.pattern_category,
                    "score": c.evolution_score,
                    "recommendation": c.recommendation,
                }
                for c in evo.candidates[:20]
            ],
        }
        return LearningQueryResult(
            query_type="patterns",
            data=data,
            count=len(evo.candidates),
        )

    def _query_experience(self, params: Dict[str, Any]) -> LearningQueryResult:
        """Query experience repository."""
        repo = self._runtime.get_experience_repository()
        source_type = params.get("source_type")
        outcome = params.get("outcome")

        records: Tuple[ExperienceRecord, ...]
        if source_type:
            records = repo.get_by_source_type(source_type)
        elif outcome:
            records = repo.get_by_outcome(outcome)
        else:
            records = repo.get_all()

        data = {
            "total": len(records),
            "by_source_type": repo.count_by_source_type(),
            "by_outcome": repo.count_by_outcome(),
            "records": [
                {
                    "id": r.experience_id[:8],
                    "source_type": r.source_type,
                    "outcome": r.outcome,
                    "summary": r.summary[:60],
                    "timestamp": str(r.timestamp),
                }
                for r in sorted(
                    records,
                    key=lambda x: x.timestamp,
                    reverse=True,
                )[:30]
            ],
        }
        return LearningQueryResult(
            query_type="experience",
            data=data,
            count=len(records),
        )

    def _query_optimization(self, params: Dict[str, Any]) -> LearningQueryResult:
        """Query recommendation optimization results."""
        optimizer = self._runtime.get_optimizer()
        kb = self._runtime.get_knowledge_base()
        repo = self._runtime.get_experience_repository()
        opt = optimizer.optimize(knowledge_base=kb, experience_repo=repo)

        data = {
            "total_candidates": opt.total_candidates,
            "duplicates": opt.total_duplicates,
            "conflicts": opt.total_conflicts,
            "avg_improvement": opt.avg_improvement,
            "avg_confidence_adjustment": opt.avg_confidence_adjustment,
            "candidates": [
                {
                    "recommendation": c.recommendation[:60],
                    "is_duplicate": c.is_duplicate,
                    "has_conflict": c.has_conflict,
                    "improvement": c.estimated_improvement,
                    "confidence_adjustment": c.confidence_adjustment,
                    "rank": c.rank,
                }
                for c in opt.candidates[:20]
            ],
        }
        return LearningQueryResult(
            query_type="optimization",
            data=data,
            count=len(opt.candidates),
        )

    def _query_confidence(self, params: Dict[str, Any]) -> LearningQueryResult:
        """Query confidence trends across knowledge."""
        kb = self._runtime.get_knowledge_base()
        stats = kb.get_statistics()
        records = kb.get_all_records()

        # Group by category
        by_category: Dict[str, List[float]] = {}
        for rec in records:
            by_category.setdefault(rec.category, []).append(rec.confidence)

        data = {
            "overall_avg_confidence": stats.avg_confidence,
            "total_evidence": stats.total_evidence,
            "by_category": {
                cat: {
                    "avg": round(sum(confs) / len(confs), 4),
                    "count": len(confs),
                }
                for cat, confs in sorted(by_category.items())
            },
        }
        return LearningQueryResult(
            query_type="confidence",
            data=data,
            count=len(by_category),
        )

    def _query_recommendation(self, params: Dict[str, Any]) -> LearningQueryResult:
        """Query learning recommendations."""
        pipeline = self._runtime.run_pipeline()
        data = {
            "total_recommendations": len(pipeline.recommendations),
            "approved": sum(1 for r in pipeline.recommendations if r.approved),
            "rejected": sum(1 for r in pipeline.recommendations if not r.approved),
            "recommendations": [
                {
                    "id": r.recommendation_id,
                    "category": r.category,
                    "confidence": r.confidence,
                    "evidence": r.evidence_count,
                    "approved": r.approved,
                    "source": r.source,
                    "details": r.details,
                }
                for r in pipeline.recommendations[:20]
            ],
        }
        return LearningQueryResult(
            query_type="recommendation",
            data=data,
            count=len(pipeline.recommendations),
        )

    def _query_history(self, params: Dict[str, Any]) -> LearningQueryResult:
        """Query recent experience history."""
        repo = self._runtime.get_experience_repository()
        summaries = repo.get_summaries()

        data = {
            "total": len(summaries),
            "recent": [
                {
                    "id": s.experience_id[:8],
                    "type": s.source_type,
                    "outcome": s.outcome,
                    "summary": s.summary[:50],
                    "timestamp": str(s.timestamp),
                }
                for s in sorted(
                    summaries,
                    key=lambda x: x.timestamp,
                    reverse=True,
                )[:20]
            ],
        }
        return LearningQueryResult(
            query_type="history",
            data=data,
            count=len(summaries),
        )

    def _query_trend(self, params: Dict[str, Any]) -> LearningQueryResult:
        """Query learning trends (pattern evolution + optimization)."""
        pattern_engine = self._runtime.get_pattern_engine()
        optimizer = self._runtime.get_optimizer()
        kb = self._runtime.get_knowledge_base()
        repo = self._runtime.get_experience_repository()

        evo = pattern_engine.analyze(kb)
        opt = optimizer.optimize(knowledge_base=kb, experience_repo=repo)

        data = {
            "pattern_trends": {
                "emerging": evo.total_emerging,
                "strengthening": evo.total_strengthening,
                "weakening": evo.total_weakening,
                "stable": evo.total_stable,
                "obsolete": evo.total_obsolete,
            },
            "optimization_trends": {
                "duplicates": opt.total_duplicates,
                "conflicts": opt.total_conflicts,
                "avg_improvement": opt.avg_improvement,
            },
            "top_recommendations": [
                c.recommendation for c in opt.candidates[:5]
            ],
        }
        return LearningQueryResult(
            query_type="trend",
            data=data,
            count=1,
        )

    def _query_policy(self, params: Dict[str, Any]) -> LearningQueryResult:
        """Query learning policy status."""
        policy_engine = self._runtime.get_policy_engine()
        policies = policy_engine.list_policies()

        data = {
            "policies": [
                {
                    "name": p.name,
                    "enabled": p.enabled,
                    "params": p.params,
                }
                for p in policies
            ],
            "policy_count": len(policies),
        }
        return LearningQueryResult(
            query_type="policy",
            data=data,
            count=len(policies),
        )
