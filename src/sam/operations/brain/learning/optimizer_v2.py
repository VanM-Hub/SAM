# OP-384 — Recommendation Optimizer V2
# Python 3.8 compatible, frozen dataclass, synchronous only
# Compares recommendation history, detects duplicates/conflicts, ranks — recommendation only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from .knowledge_base import KnowledgeRecord
from .experience_repository import ExperienceRecord


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OptimizationCandidate:
    """A recommendation optimization insight."""
    candidate_id: str = ""
    recommendation: str = ""
    current_score: float = 0.0
    estimated_improvement: float = 0.0
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    has_conflict: bool = False
    conflict_with: Tuple[str, ...] = field(default_factory=tuple)
    confidence_adjustment: float = 0.0
    rank: int = 0
    details: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class OptimizationSummary:
    """Summary of optimization results."""
    candidates: Tuple[OptimizationCandidate, ...] = field(default_factory=tuple)
    total_candidates: int = 0
    total_duplicates: int = 0
    total_conflicts: int = 0
    avg_improvement: float = 0.0
    avg_confidence_adjustment: float = 0.0
    snapshot_time: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# RecommendationOptimizerV2
# ---------------------------------------------------------------------------

class RecommendationOptimizerV2:
    """Optimizes learning recommendations by detecting duplicates, conflicts,
    and suggesting confidence adjustments.

    All outputs are recommendations — never modifies stored data.
    """

    def __init__(self) -> None:
        self._recommendation_history: List[Dict[str, Any]] = []

    def record_recommendation(self, category: str, fact: str,
                              confidence: float, source: str) -> None:
        """Record a recommendation for future comparison."""
        self._recommendation_history.append({
            "category": category,
            "fact": fact,
            "confidence": confidence,
            "source": source,
            "timestamp": datetime.utcnow(),
        })

    def optimize(
        self,
        knowledge_base=None,
        experience_repo=None,
    ) -> OptimizationSummary:
        """Analyze recommendation history and knowledge base for optimization.

        Detects duplicates, conflicts, and estimates improvements.
        Produces recommendations only — no data mutation.
        """
        candidates: List[OptimizationCandidate] = []

        # Normalize histories
        recent = self._recommendation_history[-100:] if len(self._recommendation_history) > 100 else self._recommendation_history

        # Find duplicates (by fact similarity)
        seen_facts: Dict[str, List[int]] = {}
        for idx, rec in enumerate(recent):
            fact_lower = rec["fact"].lower().strip()
            seen_facts.setdefault(fact_lower, []).append(idx)

        duplicate_tracker: Dict[int, bool] = {}
        for fact, indices in seen_facts.items():
            if len(indices) > 1:
                for idx in indices[1:]:
                    duplicate_tracker[idx] = True

        # Detect conflicts (same category, conflicting fact)
        category_facts: Dict[str, List[Tuple[int, str]]] = {}
        for idx, rec in enumerate(recent):
            category_facts.setdefault(rec["category"], []).append((idx, rec["fact"].lower().strip()))

        conflict_tracker: Dict[int, List[str]] = {}
        for cat, pairs in category_facts.items():
            for i in range(len(pairs)):
                for j in range(i + 1, len(pairs)):
                    idx_i, fact_i = pairs[i]
                    idx_j, fact_j = pairs[j]
                    # Heuristic: different facts in same category = potential conflict
                    if fact_i != fact_j:
                        conflict_tracker.setdefault(idx_i, []).append(str(idx_j))
                        conflict_tracker.setdefault(idx_j, []).append(str(idx_i))

        # Build candidates from knowledge base records
        if knowledge_base:
            records = knowledge_base.get_all_records()
            for idx, rec in enumerate(records):
                hist_idx = idx if idx < len(recent) else -1

                is_dup = hist_idx in duplicate_tracker and hist_idx >= 0
                dup_of = None
                if is_dup:
                    for fact, indices in seen_facts.items():
                        if hist_idx in indices and len(indices) > 1:
                            dup_of = str(indices[0])
                            break

                conflicts = conflict_tracker.get(hist_idx, []) if hist_idx >= 0 else []

                estimated_improvement = 0.0
                confidence_adjustment = 0.0

                if is_dup:
                    # Duplicate: reduce confidence
                    confidence_adjustment = -0.05
                    estimated_improvement = 0.02  # small improvement from dedup
                elif conflicts:
                    # Conflict: flag for review
                    confidence_adjustment = 0.0
                    estimated_improvement = 0.1
                else:
                    # Unique and no conflict: slight positive adjustment
                    confidence_adjustment = min(0.02, (1.0 - rec.confidence) * 0.1)
                    estimated_improvement = rec.confidence * 0.05

                candidates.append(OptimizationCandidate(
                    candidate_id=f"opt_{rec.record_id[:8]}",
                    recommendation=f"Optimize knowledge record '{rec.fact[:50]}'",
                    current_score=rec.confidence,
                    estimated_improvement=round(estimated_improvement, 4),
                    is_duplicate=is_dup,
                    duplicate_of=dup_of,
                    has_conflict=len(conflicts) > 0,
                    conflict_with=tuple(conflicts),
                    confidence_adjustment=round(confidence_adjustment, 4),
                    rank=idx + 1,
                    details=self._build_detail(rec, is_dup, conflicts),
                ))

        # Also process experience repo for optimization
        if experience_repo:
            experiences = experience_repo.get_all()
            for xp in experiences[:50]:  # limit
                if xp.confidence_impact != 0:
                    candidates.append(OptimizationCandidate(
                        candidate_id=f"opt_xp_{xp.experience_id[:8]}",
                        recommendation=f"Review experience '{xp.summary[:50]}' (confidence impact {xp.confidence_impact})",
                        current_score=xp.confidence_impact,
                        estimated_improvement=round(abs(xp.confidence_impact) * 0.1, 4),
                        is_duplicate=False,
                        has_conflict=False,
                        confidence_adjustment=round(xp.confidence_impact * 0.05, 4),
                        rank=len(candidates) + 1,
                        details=f"Experience from {xp.source_type}: {xp.outcome}",
                    ))

        # Rank by estimated improvement descending
        candidates.sort(key=lambda c: c.estimated_improvement, reverse=True)
        for i, c in enumerate(candidates):
            candidates[i] = OptimizationCandidate(
                candidate_id=c.candidate_id,
                recommendation=c.recommendation,
                current_score=c.current_score,
                estimated_improvement=c.estimated_improvement,
                is_duplicate=c.is_duplicate,
                duplicate_of=c.duplicate_of,
                has_conflict=c.has_conflict,
                conflict_with=c.conflict_with,
                confidence_adjustment=c.confidence_adjustment,
                rank=i + 1,
                details=c.details,
            )

        if candidates:
            avg_imp = sum(c.estimated_improvement for c in candidates) / len(candidates)
            avg_conf_adj = sum(c.confidence_adjustment for c in candidates) / len(candidates)
        else:
            avg_imp = 0.0
            avg_conf_adj = 0.0

        return OptimizationSummary(
            candidates=tuple(candidates),
            total_candidates=len(candidates),
            total_duplicates=sum(1 for c in candidates if c.is_duplicate),
            total_conflicts=sum(1 for c in candidates if c.has_conflict),
            avg_improvement=round(avg_imp, 4),
            avg_confidence_adjustment=round(avg_conf_adj, 4),
        )

    @staticmethod
    def _build_detail(rec: KnowledgeRecord, is_dup: bool,
                      conflicts: List[str]) -> str:
        parts = [f"Category: {rec.category}", f"Confidence: {rec.confidence}"]
        if is_dup:
            parts.append("DUPLICATE")
        if conflicts:
            parts.append(f"CONFLICTS with {len(conflicts)} other(s)")
        return " | ".join(parts)

    def clear_history(self) -> None:
        self._recommendation_history.clear()
