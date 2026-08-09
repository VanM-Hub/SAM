"""Dependency Analysis - WP-13 (MISSION-4.2 / IP-4.2-002).

Menganalisis dependensi antar komponen/provider (read-only).
Read-only, deterministik; output = grafik dependensi + jalur kritis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DependencyEdge:
    """Satu dependensi: component a bergantung pada b."""

    dependency: str  # a -> b
    component: str
    depends_on: str

    def as_dict(self) -> dict:
        return {
            "dependency": self.dependency,
            "component": self.component,
            "depends_on": self.depends_on,
        }


@dataclass(frozen=True)
class DependencyNode:
    """Satu node dalam grafik dependensi."""

    component: str
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    dependents: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "component": self.component,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
        }


@dataclass(frozen=True)
class DependencyAnalysisResult:
    """Hasil analisis dependensi."""

    investigation_id: str
    nodes: Tuple[DependencyNode, ...] = field(default_factory=tuple)
    edges: Tuple[DependencyEdge, ...] = field(default_factory=tuple)
    critical_components: Tuple[str, ...] = field(default_factory=tuple)

    def component(self, name: str) -> Optional[DependencyNode]:
        for n in self.nodes:
            if n.component == name:
                return n
        return None

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "nodes": [n.as_dict() for n in self.nodes],
            "edges": [e.as_dict() for e in self.edges],
            "critical_components": list(self.critical_components),
        }


class DependencyAnalyzer:
    """Menganalisis grafik dependensi antar komponen."""

    def analyze(
        self,
        investigation_id: str,
        *,
        components: Dict[str, Tuple[str, ...]],
    ) -> DependencyAnalysisResult:
        # index reverse (dependents)
        dependents: Dict[str, List[str]] = {}
        for comp, deps in components.items():
            for dep in deps:
                dependents.setdefault(dep, []).append(comp)

        nodes = tuple(
            DependencyNode(
                component=comp,
                dependencies=tuple(deps),
                dependents=tuple(dependents.get(comp, ())),
            )
            for comp, deps in sorted(components.items())
        )
        edges = tuple(
            DependencyEdge(
                dependency=f"{comp}->{dep}",
                component=comp,
                depends_on=dep,
            )
            for comp, deps in sorted(components.items())
            for dep in sorted(deps)
        )
        # Komponen kritis = yang paling banyak dependents (paling berdampak)
        critical = tuple(
            comp
            for comp, deps in sorted(
                components.items(), key=lambda kv: -len(dependents.get(kv[0], ()))
            )
            if len(dependents.get(comp, ())) >= 2
        )
        return DependencyAnalysisResult(
            investigation_id=investigation_id,
            nodes=nodes,
            edges=edges,
            critical_components=critical,
        )
