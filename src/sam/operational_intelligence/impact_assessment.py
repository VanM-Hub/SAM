"""Impact Assessment - WP-14 (MISSION-4.2 / IP-4.2-002).

Menilai dampak dari root cause / failure terhadap dependents.
Read-only, deterministik.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from .dependency_analysis import DependencyAnalysisResult


@dataclass(frozen=True)
class ImpactedComponent:
    """Satu komponen yang terdampak (langsung/tidak langsung)."""

    component: str
    impact_level: str  # direct | indirect
    path: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "component": self.component,
            "impact_level": self.impact_level,
            "path": list(self.path),
        }


@dataclass(frozen=True)
class ImpactAssessmentResult:
    """Hasil penilaian dampak."""

    investigation_id: str
    source_component: str
    impacted: Tuple[ImpactedComponent, ...] = field(default_factory=tuple)

    @property
    def impact_count(self) -> int:
        return len(self.impacted)

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "source_component": self.source_component,
            "impact_count": self.impact_count,
            "impacted": [i.as_dict() for i in self.impacted],
        }


class ImpactAssessor:
    """Menilai dampak kegagalan satu komponen terhadap dependents-nya."""

    def assess(
        self,
        investigation_id: str,
        source_component: str,
        dependency: DependencyAnalysisResult,
    ) -> ImpactAssessmentResult:
        # BFS melalui dependents untuk menemukan semua yang terdampak
        impacted: Dict[str, Tuple[str, ...]] = {}
        visited: Set[str] = set()
        queue: List[Tuple[str, Tuple[str, ...]]] = [
            (dep, (source_component,))
            for dep in self._dependents_of(dependency, source_component)
        ]
        while queue:
            comp, path = queue.pop(0)
            if comp in visited or comp == source_component:
                continue
            visited.add(comp)
            impacted[comp] = path + (comp,)
            for sub in self._dependents_of(dependency, comp):
                if sub not in visited:
                    queue.append((sub, path + (comp,)))

        result = tuple(
            ImpactedComponent(
                component=comp,
                impact_level=(
                    "direct"
                    if len(path) == 2
                    else "indirect"
                ),
                path=path,
            )
            for comp, path in sorted(impacted.items())
        )
        return ImpactAssessmentResult(
            investigation_id=investigation_id,
            source_component=source_component,
            impacted=result,
        )

    @staticmethod
    def _dependents_of(
        dependency: DependencyAnalysisResult, component: str
    ) -> Tuple[str, ...]:
        node = dependency.component(component)
        return node.dependents if node else ()
