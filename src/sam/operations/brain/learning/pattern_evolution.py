# OP-383 — Pattern Evolution Engine
# Python 3.8 compatible, frozen dataclass, synchronous only
# Detects emerging/obsolete patterns, tracks trend confidence — recommendation only
# Does NOT modify existing patterns

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from .knowledge_base import KnowledgeRecord, KnowledgeBase


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvolutionCandidate:
    """A candidate pattern evolution insight (recommendation only)."""
    candidate_id: str = ""
    pattern_category: str = ""
    pattern_fact: str = ""
    evolution_type: str = ""  # emerging, obsolete, stable, strengthening, weakening
    current_confidence: float = 0.0
    previous_confidence: float = 0.0
    trend_confidence: float = 1.0  # how confident we are about this trend (0.0-1.0)
    evolution_score: float = 0.0  # magnitude of evolution (0.0-1.0)
    evidence_before: int = 0
    evidence_after: int = 0
    recommendation: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)
    related_record_ids: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EvolutionSummary:
    """Summary of pattern evolution findings."""
    candidates: Tuple[EvolutionCandidate, ...] = field(default_factory=tuple)
    total_analyzed: int = 0
    total_emerging: int = 0
    total_obsolete: int = 0
    total_stable: int = 0
    total_strengthening: int = 0
    total_weakening: int = 0
    avg_evolution_score: float = 0.0
    snapshot_time: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# PatternEvolutionEngine
# ---------------------------------------------------------------------------

class PatternEvolutionEngine:
    """Analyzes pattern evolution across snapshots of knowledge base.

    Compares historical patterns to detect emerging, obsolete, strengthening,
    and weakening patterns. Produces recommendations only — never modifies
    existing patterns.
    """

    def __init__(self) -> None:
        self._history: List[Tuple[datetime, Dict[str, float]]] = []  # (timestamp, category->avg_confidence)

    def _extract_category_confidences(self, base: KnowledgeBase) -> Dict[str, float]:
        """Extract per-category average confidence from knowledge base."""
        records = base.get_all_records()
        categories: Dict[str, List[float]] = {}
        for rec in records:
            categories.setdefault(rec.category, []).append(rec.confidence)
        return {cat: sum(confs) / len(confs) for cat, confs in categories.items()}

    def record_snapshot(self, base: KnowledgeBase) -> None:
        """Record current state for future comparison."""
        confs = self._extract_category_confidences(base)
        self._history.append((datetime.utcnow(), confs))

    def analyze(self, base: KnowledgeBase) -> EvolutionSummary:
        """Analyze knowledge base for pattern evolution insights.

        Compares current state with recent historical snapshots.
        Produces recommendation DTOs — does NOT modify any patterns.
        """
        current = self._extract_category_confidences(base)
        candidates: List[EvolutionCandidate] = []
        all_categories = set(current.keys())

        # Gather historical confidences
        for ts, hist in self._history:
            all_categories.update(hist.keys())

        for cat in sorted(all_categories):
            current_conf = current.get(cat, 0.0)
            hist_confidences = [h.get(cat, 0.0) for _, h in self._history if cat in h]

            if not hist_confidences:
                # New category
                if current_conf > 0:
                    records = base.search_by_category(cat)
                    ev_before = 0
                    ev_after = sum(r.evidence_count for r in records)
                    candidates.append(EvolutionCandidate(
                        candidate_id=f"emerge_{cat}",
                        pattern_category=cat,
                        pattern_fact=f"Emerging pattern in category '{cat}'",
                        evolution_type="emerging",
                        current_confidence=current_conf,
                        previous_confidence=0.0,
                        trend_confidence=min(1.0, current_conf + 0.1),
                        evolution_score=min(1.0, current_conf),
                        evidence_before=ev_before,
                        evidence_after=ev_after,
                        recommendation=f"Monitor emerging pattern '{cat}'. Gather more evidence.",
                        related_record_ids=tuple(r.record_id for r in records),
                    ))
                continue

            prev_conf = sum(hist_confidences) / len(hist_confidences)
            delta = current_conf - prev_conf
            threshold = 0.05
            evolution_score = abs(delta)

            records = base.search_by_category(cat)
            ev_before = sum(hist_confidences[-1] for _ in hist_confidences[-1:]) if hist_confidences else 0
            ev_after = sum(r.evidence_count for r in records)

            if evolution_score < threshold:
                # Stable
                candidates.append(EvolutionCandidate(
                    candidate_id=f"stable_{cat}",
                    pattern_category=cat,
                    pattern_fact=f"Pattern '{cat}' is stable",
                    evolution_type="stable",
                    current_confidence=current_conf,
                    previous_confidence=prev_conf,
                    trend_confidence=1.0,
                    evolution_score=0.0,
                    evidence_before=int(ev_before),
                    evidence_after=ev_after,
                    recommendation=f"Pattern '{cat}' is stable. No action needed.",
                    related_record_ids=tuple(r.record_id for r in records),
                ))
            elif delta > 0:
                # Strengthening
                candidate_id = f"strengthen_{cat}"
                candidates.append(EvolutionCandidate(
                    candidate_id=candidate_id,
                    pattern_category=cat,
                    pattern_fact=f"Pattern '{cat}' is strengthening",
                    evolution_type="strengthening",
                    current_confidence=current_conf,
                    previous_confidence=prev_conf,
                    trend_confidence=min(1.0, evolution_score + 0.3),
                    evolution_score=evolution_score,
                    evidence_before=int(ev_before),
                    evidence_after=ev_after,
                    recommendation=f"Pattern '{cat}' strengthening (delta={delta:.3f}). Consider increasing confidence.",
                    related_record_ids=tuple(r.record_id for r in records),
                ))
            else:
                # Weakening
                candidates.append(EvolutionCandidate(
                    candidate_id=f"weaken_{cat}",
                    pattern_category=cat,
                    pattern_fact=f"Pattern '{cat}' is weakening",
                    evolution_type="weakening",
                    current_confidence=current_conf,
                    previous_confidence=prev_conf,
                    trend_confidence=min(1.0, evolution_score + 0.2),
                    evolution_score=evolution_score,
                    evidence_before=int(ev_before),
                    evidence_after=ev_after,
                    recommendation=f"Pattern '{cat}' weakening (delta={delta:.3f}). Review and consider updates.",
                    related_record_ids=tuple(r.record_id for r in records),
                ))

        # Statistik
        t_emerging = sum(1 for c in candidates if c.evolution_type == "emerging")
        t_obsolete = sum(1 for c in candidates if c.evolution_type == "obsolete")
        t_stable = sum(1 for c in candidates if c.evolution_type == "stable")
        t_strengthening = sum(1 for c in candidates if c.evolution_type == "strengthening")
        t_weakening = sum(1 for c in candidates if c.evolution_type == "weakening")
        avg_score = (sum(c.evolution_score for c in candidates) / len(candidates)) if candidates else 0.0

        return EvolutionSummary(
            candidates=tuple(candidates),
            total_analyzed=len(candidates),
            total_emerging=t_emerging,
            total_obsolete=t_obsolete,
            total_stable=t_stable,
            total_strengthening=t_strengthening,
            total_weakening=t_weakening,
            avg_evolution_score=round(avg_score, 4),
        )

    def clear_history(self) -> None:
        self._history.clear()
