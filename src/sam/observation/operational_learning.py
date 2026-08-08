"""Operational Learning - Workstream C10.

Operational Learning (bukan AI, bukan governance, bukan autonomous decision):
- C10.1 OperationalTrendReport (tren observasi operational)
- C10.2 OperationalRecommendationCenter (pemanfaatan Recommendation Engine)
- C10.3 HistoricalObservationSummary (ringkasan observasi historis)
- C10.4 LearningEvidenceReport (evidence yang mendukung learning)

READ-ONLY. Learning HANYA memanfaatkan: Observation, Analytics, Recommendation,
Historical Evidence. TIDAK: execute action, approve action, mutate governance,
invoke runtime. Recommendation Engine (C-Phase 3) = salah satu sumber masukan.
Sesuai constraint AP-2C-001 & Directive EA-C05 (C10): observe, never govern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# C10.1 Operational Trend Report
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class OperationalTrendEntry:
    """Tren satu dimensi operasional (immutable, read-only)."""
    dimension: str = ""       # health | readiness | operational | capability | runtime
    current: float = 0.0
    previous: float = 0.0
    direction: str = "stable"  # improving | degrading | stable | unknown

    def as_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "current": self.current,
            "previous": self.previous,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class OperationalTrendReport:
    """Laporan tren operasional (immutable)."""
    entries: Tuple[OperationalTrendEntry, ...] = field(default_factory=tuple)
    observed_at: str = ""

    def by_dimension(self, dimension: str) -> Optional[OperationalTrendEntry]:
        for e in self.entries:
            if e.dimension == dimension:
                return e
        return None

    def as_dict(self) -> dict:
        return {"observed_at": self.observed_at, "trends": [e.as_dict() for e in self.entries]}


# ═══════════════════════════════════════════════════════════════════════
# C10.2 Operational Recommendation Center
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class OperationalRecommendation:
    """Satu rekomendasi operasional (immutable, bukan keputusan)."""
    category: str = "unknown"
    severity: str = "info"  # info | low | medium | high | critical
    message: str = ""
    source: str = "observation"

    def as_dict(self) -> dict:
        return {"category": self.category, "severity": self.severity,
                "message": self.message, "source": self.source}


@dataclass(frozen=True)
class OperationalRecommendationCenter:
    """Pusat rekomendasi operasional (immutable).

    Merepresentasikan rekomendasi DARI Recommendation Engine (C-Phase 3)
    sebagai informasi operasional - bukan otoritas untuk bertindak.
    """
    recommendations: Tuple[OperationalRecommendation, ...] = field(default_factory=tuple)
    source_engine: str = "observation.recommendation"
    total_recommendations: int = 0
    high_severity_count: int = 0

    def by_severity(self, severity: str) -> Tuple[OperationalRecommendation, ...]:
        return tuple(r for r in self.recommendations if r.severity == severity)

    def as_dict(self) -> dict:
        return {
            "source_engine": self.source_engine,
            "total_recommendations": self.total_recommendations,
            "high_severity_count": self.high_severity_count,
            "recommendations": [r.as_dict() for r in self.recommendations],
        }


# ═══════════════════════════════════════════════════════════════════════
# C10.3 Historical Observation Summary
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class HistoricalObservationSummary:
    """Ringkasan observasi historis (immutable)."""
    total_observations: int = 0
    total_runtimes: int = 0
    healthy_count: int = 0
    degraded_count: int = 0
    critical_count: int = 0
    window_start: str = ""
    window_end: str = ""

    def as_dict(self) -> dict:
        return {
            "total_observations": self.total_observations,
            "total_runtimes": self.total_runtimes,
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "critical_count": self.critical_count,
            "window_start": self.window_start,
            "window_end": self.window_end,
        }


# ═══════════════════════════════════════════════════════════════════════
# C10.4 Learning Evidence Report
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LearningEvidence:
    """Satu evidence yang mendukung learning (immutable)."""
    category: str = "unknown"
    observed: bool = False
    detail: str = ""

    def as_dict(self) -> dict:
        return {"category": self.category, "observed": self.observed, "detail": self.detail}


@dataclass(frozen=True)
class LearningEvidenceReport:
    """Laporan evidence learning (immutable)."""
    evidence: Tuple[LearningEvidence, ...] = field(default_factory=tuple)
    ready_to_learn: bool = False
    summary: str = ""

    def as_dict(self) -> dict:
        return {"ready_to_learn": self.ready_to_learn, "summary": self.summary,
                "evidence": [e.as_dict() for e in self.evidence]}


# ═══════════════════════════════════════════════════════════════════════
# C10 Observer
# ═══════════════════════════════════════════════════════════════════════

class OperationalLearningObserver:
    """Observer Operational Learning - learning berbasis evidence (read-only).

    Learning HANYA dari: observasi (registry), analytics (platform metrics),
    recommendation (Recommendation Engine C-Phase 3), historical evidence.
    TIDAK melakukan aksi apapun; murni observasi untuk pembelajaran operasional.
    """

    def __init__(self, registry=None, recommendation_engine=None) -> None:
        self._registry = registry
        self._recommendation_engine = recommendation_engine

    def _get_recommendation_engine(self):
        if self._recommendation_engine is not None:
            return self._recommendation_engine
        try:
            from sam.runtime_service.api.observation_wiring import get_recommendation_engine
            return get_recommendation_engine()
        except Exception:
            return None

    def _publications(self) -> Tuple:
        if self._registry is None:
            try:
                from sam.runtime_service.api.observation_wiring import get_publication_registry
                reg = get_publication_registry()
                return reg.observe_all().publications
            except Exception:
                return ()
        try:
            return self._registry.observe_all().publications
        except Exception:
            return ()

    # C10.1
    def trend_report(self) -> OperationalTrendReport:
        """Tren operasional dari observasi saat ini (read-only)."""
        pubs = self._publications()
        total = len(pubs)
        if total == 0:
            return OperationalTrendReport()
        healthy = sum(1 for p in pubs if p.health_state == "healthy")
        ready = sum(1 for p in pubs if p.readiness_level == "operational")
        op = sum(1 for p in pubs if p.operational_state in ("running", "ready", "operational"))
        health_ratio = healthy / total
        readiness_ratio = ready / total
        operational_ratio = op / total
        entries = (
            OperationalTrendEntry(dimension="health", current=health_ratio, previous=0.0,
                                  direction="stable" if health_ratio >= 0.5 else "degrading"),
            OperationalTrendEntry(dimension="readiness", current=readiness_ratio, previous=0.0,
                                  direction="improving" if readiness_ratio >= 0.8 else "stable"),
            OperationalTrendEntry(dimension="operational", current=operational_ratio, previous=0.0,
                                  direction="stable" if operational_ratio >= 0.5 else "degrading"),
        )
        return OperationalTrendReport(entries=entries)

    # C10.2
    def recommendation_center(self) -> OperationalRecommendationCenter:
        """Pusat rekomendasi dari Recommendation Engine (C-Phase 3) (read-only)."""
        engine = self._get_recommendation_engine()
        recs: List[OperationalRecommendation] = []
        if engine is not None:
            try:
                report = engine.recommend()
                for r in getattr(report, "recommendations", ()):
                    recs.append(OperationalRecommendation(
                        category=getattr(r, "category", "unknown"),
                        severity=getattr(r, "severity", "info"),
                        message=getattr(r, "title", "") or "",
                        source="observation.recommendation",
                    ))
            except Exception:
                recs = []
        high = sum(1 for r in recs if r.severity in ("high", "critical"))
        return OperationalRecommendationCenter(
            recommendations=tuple(recs),
            total_recommendations=len(recs),
            high_severity_count=high,
        )

    # C10.3
    def historical_summary(self) -> HistoricalObservationSummary:
        """Ringkasan observasi historis (read-only, dari snapshot publikasi)."""
        pubs = self._publications()
        healthy = sum(1 for p in pubs if p.health_state == "healthy")
        degraded = sum(1 for p in pubs if p.health_state == "degraded")
        critical = sum(1 for p in pubs if p.health_state in ("critical", "unhealthy"))
        return HistoricalObservationSummary(
            total_observations=sum(p.health_check_count or 0 for p in pubs),
            total_runtimes=len(pubs),
            healthy_count=healthy,
            degraded_count=degraded,
            critical_count=critical,
        )

    # C10.4
    def learning_evidence(self) -> LearningEvidenceReport:
        """Evidence yang mendukung pembelajaran operasional (read-only)."""
        pubs = self._publications()
        total = len(pubs)
        has_observations = total > 0
        has_analytics = any((p.metric_count or 0) > 0 for p in pubs)
        has_readiness = any((p.readiness_level or "") != "" for p in pubs)
        has_recommendation_source = self._get_recommendation_engine() is not None
        evidence = (
            LearningEvidence(category="observation", observed=has_observations,
                             detail="{0} runtime dipublikasi".format(total)),
            LearningEvidence(category="analytics", observed=has_analytics,
                             detail="metrik operasional tersedia"),
            LearningEvidence(category="readiness", observed=has_readiness,
                             detail="readiness reporting tersedia"),
            LearningEvidence(category="recommendation", observed=has_recommendation_source,
                             detail="recommendation engine tersedia"),
        )
        ready = has_observations and has_readiness and has_recommendation_source
        summary = "Learning siap: observasi + analytics + readiness + recommendation tersedia." if ready \
            else "Learning belum siap: sebagian evidence belum tersedia."
        return LearningEvidenceReport(evidence=evidence, ready_to_learn=ready, summary=summary)

    # ── C10 Observer utama ──
    def observe(self) -> OperationalRecommendationCenter:
        """Agregasi utama: pusat rekomendasi operational (read-only)."""
        return self.recommendation_center()
