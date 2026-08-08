# Runtime Health Analyzer - WP-04
# IP-3.2-001 (AO-3.2-001 / ED-3.2-001)
#
# Menilai kesehatan runtime dari RuntimeState. Murni analisis (read-only):
# TIDAK mengubah health, TIDAK men-trigger recovery, TIDAK restart.
# Output: RuntimeHealthReport (immutable).

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sam.autonomy_runtime.observation.models import RuntimeState

# Peringkat health: nilai lebih tinggi = lebih sehat
_HEALTH_RANK = {"unknown": 0, "error": 1, "degraded": 2, "healthy": 3}


@dataclass(frozen=True)
class ComponentHealth:
    component: str
    status: str  # re-mapped ke health vocabulary
    ready: bool
    issues: tuple = ()  # tuple[str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "component": self.component,
            "status": self.status,
            "ready": self.ready,
            "issues": list(self.issues),
        }


@dataclass(frozen=True)
class RuntimeHealthReport:
    state_id: str
    observed_at: str
    overall: str  # "healthy" | "degraded" | "unhealthy" | "unknown"
    score: int
    components: tuple = ()  # tuple[ComponentHealth]
    issues: tuple = ()  # tuple[str] isu health global

    def as_dict(self) -> Dict[str, object]:
        return {
            "state_id": self.state_id,
            "observed_at": self.observed_at,
            "overall": self.overall,
            "score": self.score,
            "components": [c.as_dict() for c in self.components],
            "issues": list(self.issues),
        }


class HealthAnalyzer:
    """Menilai kesehatan runtime dari satu RuntimeState (deterministik)."""

    def analyze(self, state: RuntimeState) -> RuntimeHealthReport:
        comp_health: List[ComponentHealth] = []
        global_issues: List[str] = []

        for comp in state.components:
            status = self._status_of(comp.status, comp.ready)
            issues = self._issues_of(comp)
            comp_health.append(
                ComponentHealth(
                    component=comp.name,
                    status=status,
                    ready=comp.ready,
                    issues=tuple(issues),
                )
            )
            global_issues.extend(issues)

        overall, score = self._overall(comp_health)
        return RuntimeHealthReport(
            state_id=state.state_id,
            observed_at=state.observed_at,
            overall=overall,
            score=score,
            components=tuple(comp_health),
            issues=tuple(dict.fromkeys(global_issues)),  # dedup, urutan stabil
        )

    @staticmethod
    def _status_of(status: str, ready: bool) -> str:
        if status == "ok":
            return "healthy"
        if status == "degraded":
            return "degraded"
        if status == "error":
            return "unhealthy"
        return "unknown"

    @staticmethod
    def _issues_of(comp) -> List[str]:
        issues: List[str] = []
        if comp.status not in ("ok",):
            issues.append("{} is {}".format(comp.name, comp.status))
        if not comp.ready:
            issues.append("{} is not ready".format(comp.name))
        if comp.detail:
            issues.append("{}: {}".format(comp.name, comp.detail))
        return issues

    @staticmethod
    def _overall(
        comp_health: List[ComponentHealth],
    ) -> "tuple[str, int]":
        if not comp_health:
            return "unknown", 0
        # skor rata-rata (0..3) -> persentase
        total = sum(_HEALTH_RANK.get(c.status, 0) for c in comp_health)
        max_score = 3 * len(comp_health)
        pct = int((total / max_score) * 100) if max_score else 0
        if any(c.status == "unhealthy" for c in comp_health):
            overall = "unhealthy"
        elif any(c.status == "degraded" for c in comp_health):
            overall = "degraded"
        elif all(c.status == "healthy" for c in comp_health):
            overall = "healthy"
        else:
            overall = "unknown"
        return overall, pct
