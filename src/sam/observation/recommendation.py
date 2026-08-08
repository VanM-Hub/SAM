"""Observation Recommendation Engine — C-Phase 3.

Konteks: Observation layer (bounded context Observation).

Domain:  Observation -> Analytics -> Recommendation
NOT:     Runtime -> Recommendation

Engine ini mengubah HASIL ANALISIS OBSERVASI menjadi rekomendasi operational.
Ia tidak membaca Runtime internal secara langsung dan tidak pernah mengeksekusi,
menyetujui, mempublikasikan, atau mengubah state apa pun.

Constraints (AP-2C-001 + Engineering Decision 2026-08-08):
1. Read-only  : TIDAK memanggil approve/execute/publish/mutate registry/
                mutate readiness/mutate timeline. Hanya membaca.
2. Source     : Input SATU-SATUNYA adalah PublicationRegistry (read-only).
                TIDAK membaca Runtime internal secara langsung.
3. Output     : HANYA recommendation observasi, contoh:
                - missing publication   (runtime tidak terpublikasi)
                - inconsistent health   (aggregated health tidak konsisten)
                - readiness regression (readiness menurun / belum operational)
                - stale timeline       (tidak ada timeline event)
                - missing metadata     (preview/metadata tidak tersedia)
                - capability degradation (health menurun / degraded)
                BUKAN: execute workflow, rerun runtime, restart provider,
                approve mission.
4. Dependency : Observation -> Recommendation. TIDAK ada Recommendation -> Runtime,
                Recommendation -> Execution, Recommendation -> Workflow.
5. Wiring     : get_recommendation_engine() + recommend() di observation_wiring.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Tuple

from sam.observation.publication import PublicationRegistry, RuntimePublication


# ── Rekomendasi DTO (immutable, read-only) ──

@dataclass(frozen=True)
class ObservationRecommendation:
    """Satu rekomendasi operational hasil analisis observasi (immutable)."""
    category: str          # missing_publication | inconsistent_health | readiness_regression |
                           # stale_timeline | missing_metadata | capability_degradation |
                           # metric_insufficiency
    severity: str          # critical | high | medium | low
    runtime_id: str        # runtime yang direkomendasikan ("" untuk platform-level)
    title: str
    description: str = ""
    evidence: Tuple[str, ...] = field(default_factory=tuple)
    timestamp: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "runtime_id": self.runtime_id,
            "title": self.title,
            "description": self.description,
            "evidence": list(self.evidence),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class OperationalRecommendationReport:
    """Laporan rekomendasi operational (immutable aggregate)."""
    status: str = "ok"
    total_recommendations: int = 0
    by_severity: Dict[str, int] = field(default_factory=lambda: {
        "critical": 0, "high": 0, "medium": 0, "low": 0,
    })
    by_category: Dict[str, int] = field(default_factory=dict)
    recommendations: Tuple[ObservationRecommendation, ...] = field(default_factory=tuple)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "total_recommendations": self.total_recommendations,
            "by_severity": dict(self.by_severity),
            "by_category": dict(self.by_category),
            "recommendations": [r.as_dict() for r in self.recommendations],
        }


# ── Observation Recommendation Engine ──

class ObservationRecommendationEngine:
    """Engine rekomendasi operational berbasis observasi (read-only).

    Menerima PublicationRegistry dan menghasilkan rekomendasi dari hasil
    analisis observasi. Tidak pernah mengeksekusi, menyetujui, mempublikasikan,
    atau mengubah state.

    Hanya membaca melalui registry.observe_all() -> ObservationReport.
    Tidak ada dependency ke Runtime/Execution/Workflow.
    """

    def __init__(self, registry: PublicationRegistry) -> None:
        self._registry = registry

    def recommend(self) -> OperationalRecommendationReport:
        """Generate operational recommendations dari analisis observasi."""
        obs = self._registry.observe_all()
        recommendations: List[ObservationRecommendation] = []

        # Deteksi runtime yang TIDAK terpublikasi (missing publication)
        # ObservationReport hanya berisi publikasi yang ada; kelengkapan yang
        # diharapkan diperiksa oleh ReadinessReporter (GAP-004), di sini kita
        # hanya ambil dari apa yang benar-benar terobservasi.
        # Jika registry kosong -> platform-level recommendation.
        if obs.runtime_count == 0:
            recommendations.append(self._platform_recommendation(
                "missing_publication",
                "critical",
                "Tidak ada runtime terpublikasi",
                "Registry observasi kosong - tidak ada runtime yang terobservasi.",
                ("runtime_count=0",),
            ))

        for pub in obs.publications:
            # Per-runtime recommendation (bukan governance action)
            recommendations.extend(self._recommendations_for(pub, obs.runtime_count))

        # Urutkan: severity critical > high > medium > low, lalu runtime_id
        _SEV = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: (_SEV.get(r.severity, 4), r.runtime_id))

        # Aggregate by severity & category
        by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_cat: Dict[str, int] = {}
        for r in recommendations:
            by_sev[r.severity] = by_sev.get(r.severity, 0) + 1
            by_cat[r.category] = by_cat.get(r.category, 0) + 1

        return OperationalRecommendationReport(
            status="ok",
            total_recommendations=len(recommendations),
            by_severity=by_sev,
            by_category=by_cat,
            recommendations=tuple(recommendations),
        )

    # ── Per-runtime analysis ──

    def _recommendations_for(
        self,
        pub: RuntimePublication,
        runtime_count: int,
    ) -> List[ObservationRecommendation]:
        recs: List[ObservationRecommendation] = []

        # 1. Inconsistent health: runtime unhealthy/degraded vs aggregated
        if pub.health_state in ("unhealthy", "degraded"):
            severity = "critical" if pub.health_state == "unhealthy" else "high"
            recs.append(self._runtime_recommendation(
                "capability_degradation",
                severity,
                pub.runtime_id,
                f"Health {pub.health_state} untuk runtime {pub.runtime_id}",
                f"Runtime {pub.runtime_id} terpublikasi dengan health_state "
                f"{pub.health_state}; perlu investigasi observasi.",
                (f"health_state={pub.health_state}",
                 f"operational_state={pub.operational_state}"),
            ))

        # 2. Readiness regression: belum operational/activated
        if pub.readiness_level not in ("operational", "activated"):
            recs.append(self._runtime_recommendation(
                "readiness_regression",
                "high",
                pub.runtime_id,
                f"Readiness {pub.readiness_level} untuk runtime {pub.runtime_id}",
                f"Runtime {pub.runtime_id} belum berada pada level "
                f"operational/activated (readiness={pub.readiness_level}).",
                (f"readiness_level={pub.readiness_level}",),
            ))

        # 3. Stale timeline: tidak ada timeline event
        if pub.timeline_events == 0:
            recs.append(self._runtime_recommendation(
                "stale_timeline",
                "medium",
                pub.runtime_id,
                f"Timeline kosong untuk runtime {pub.runtime_id}",
                f"Runtime {pub.runtime_id} tidak mempublikasikan timeline event "
                "sama sekali (timeline_events=0).",
                ("timeline_events=0",),
            ))

        # 4. Missing metadata: preview/metadata tidak tersedia
        if not (pub.has_preview and pub.has_metadata):
            recs.append(self._runtime_recommendation(
                "missing_metadata",
                "medium",
                pub.runtime_id,
                f"Metadata tidak lengkap untuk runtime {pub.runtime_id}",
                f"Runtime {pub.runtime_id} tidak mengekspos preview "
                f"(has_preview={pub.has_preview}) dan/atau metadata "
                f"(has_metadata={pub.has_metadata}).",
                (f"has_preview={pub.has_preview}",
                 f"has_metadata={pub.has_metadata}"),
            ))

        # 5. Metric insufficiency: monitoring rendah
        if pub.metric_count < 1:
            recs.append(self._runtime_recommendation(
                "metric_insufficiency",
                "low",
                pub.runtime_id,
                f"Metric density rendah untuk runtime {pub.runtime_id}",
                f"Runtime {pub.runtime_id} belum mengekspos metric "
                f"(metric_count={pub.metric_count}); perluasan monitoring "
                "disarankan.",
                (f"metric_count={pub.metric_count}",),
            ))

        # 6. Inconsistent health (platform): aggregated vs per-runtime mismatch
        #    handled dalam loop ini -> skip; hanya per-runtime di atas.

        return recs

    # ── Helpers ──

    def _runtime_recommendation(
        self,
        category: str,
        severity: str,
        runtime_id: str,
        title: str,
        description: str,
        evidence: Tuple[str, ...],
    ) -> ObservationRecommendation:
        return ObservationRecommendation(
            category=category,
            severity=severity,
            runtime_id=runtime_id,
            title=title,
            description=description,
            evidence=evidence,
            timestamp=datetime.now().isoformat(),
        )

    def _platform_recommendation(
        self,
        category: str,
        severity: str,
        title: str,
        description: str,
        evidence: Tuple[str, ...],
    ) -> ObservationRecommendation:
        return ObservationRecommendation(
            category=category,
            severity=severity,
            runtime_id="",
            title=title,
            description=description,
            evidence=evidence,
            timestamp=datetime.now().isoformat(),
        )
