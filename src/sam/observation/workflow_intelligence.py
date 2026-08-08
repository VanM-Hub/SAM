"""Workflow Operational Intelligence - Workstream C2.

Observability mendalam terhadap Workflow Runtime:
- C2.1 Workflow Visualization (descriptor workflow dari registry)
- C2.3 Runtime Status (status masing-masing workflow)
- C2.4 Dependency Graph (relasi depends_on antar step)
- C2.5 Bottleneck Detection (deteksi step tersibuk / banyak dependensi)

READ-ONLY. Membaca data Workflow yang sudah dipublikasikan runtime.
Tidak mengeksekusi workflow, tidak mengubah state, tidak menyentuh governance.
Sesuai constraint AP-2C-001: observe, never govern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# C2.1 Workflow Descriptor View
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class WorkflowView:
    """Satu workflow yang diamati (immutable)."""
    workflow_id: str = ""
    name: str = ""
    category: str = "workflow"
    description: str = ""
    tags: Tuple[str, ...] = field(default_factory=tuple)
    integrated_runtimes: Tuple[str, ...] = field(default_factory=tuple)
    step_count: int = 0
    status: str = "registered"   # registered | active | completed

    def as_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "tags": list(self.tags),
            "integrated_runtimes": list(self.integrated_runtimes),
            "step_count": self.step_count,
            "status": self.status,
        }


# ═══════════════════════════════════════════════════════════════════════
# C2.4 Dependency Graph
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class WorkflowStepDependency:
    """Satu step + dependensinya (immutable)."""
    workflow_id: str = ""
    step_id: str = ""
    step_order: int = 0
    kind: str = "compose"
    depends_on: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "step_order": self.step_order,
            "kind": self.kind,
            "depends_on": list(self.depends_on),
        }


@dataclass(frozen=True)
class WorkflowDependencyGraph:
    """Graf dependensi workflow (immutable)."""
    workflow_id: str = ""
    steps: Tuple[WorkflowStepDependency, ...] = field(default_factory=tuple)

    @property
    def edge_count(self) -> int:
        return sum(len(s.depends_on) for s in self.steps)

    def as_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "step_count": len(self.steps),
            "edge_count": self.edge_count,
            "steps": [s.as_dict() for s in self.steps],
        }


# ═══════════════════════════════════════════════════════════════════════
# C2.5 Bottleneck Detection
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Bottleneck:
    """Kandidat bottleneck (immutable)."""
    workflow_id: str = ""
    step_id: str = ""
    reason: str = ""
    metric: int = 0

    def as_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "reason": self.reason,
            "metric": self.metric,
        }


@dataclass(frozen=True)
class WorkflowBottleneckView:
    """Hasil deteksi bottleneck (immutable)."""
    bottlenecks: Tuple[Bottleneck, ...] = field(default_factory=tuple)

    @property
    def count(self) -> int:
        return len(self.bottlenecks)

    def as_dict(self) -> dict:
        return {
            "count": self.count,
            "bottlenecks": [b.as_dict() for b in self.bottlenecks],
        }


# ═══════════════════════════════════════════════════════════════════════
# C2 report agregat
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class WorkflowIntelligenceReport:
    """Laporan intelligence workflow (immutable)."""
    total_workflows: int = 0
    workflows: Tuple[WorkflowView, ...] = field(default_factory=tuple)
    dependencies: Tuple[WorkflowDependencyGraph, ...] = field(default_factory=tuple)
    bottlenecks: Optional[WorkflowBottleneckView] = None

    def as_dict(self) -> dict:
        return {
            "total_workflows": self.total_workflows,
            "workflows": [w.as_dict() for w in self.workflows],
            "dependencies": [d.as_dict() for d in self.dependencies],
            "bottlenecks": self.bottlenecks.as_dict() if self.bottlenecks else None,
        }


# ═══════════════════════════════════════════════════════════════════════
# C2 Observer
# ═══════════════════════════════════════════════════════════════════════

class WorkflowIntelligenceObserver:
    """Observer Workflow - membaca publikasi workflow (read-only).

    Menerima WorkflowRegistry opsional (di-inject dari wiring) agar dapat
    membaca descriptor yang SUDAH terdaftar, PLUS PublicationRegistry untuk
    metadata publikasi. Observer TIDAK mengisi/mengubah registry manapun.
    """

    def __init__(self, publication_registry=None, workflow_registry=None) -> None:
        self._pub_registry = publication_registry
        self._workflow_registry = workflow_registry

    def _descriptors(self) -> List:
        """Ambil daftar descriptor workflow (read-only)."""
        if self._workflow_registry is not None:
            try:
                return list(self._workflow_registry.all())
            except Exception:
                pass
        # Fallback: metadata publikasi workflow dari registry observasi
        pub = self._publication_for("workflow")
        if pub and pub.dashboard_count > 0:
            return [
                type("D", (), {"id": "workflow", "name": "Workflow",
                              "category": "workflow", "description": "",
                              "tags": [], "integrated_runtimes": []})()
            ]
        return []

    def workflows(self) -> Tuple[WorkflowView, ...]:
        views: List[WorkflowView] = []
        for d in self._descriptors():
            wid = getattr(d, "id", getattr(d, "workflow_id", "unknown"))
            steps = getattr(d, "steps", None)
            step_count = 0
            if steps is not None:
                try:
                    step_count = len(steps)
                except Exception:
                    step_count = 0
            views.append(WorkflowView(
                workflow_id=wid,
                name=getattr(d, "name", wid),
                category=getattr(d, "category", "workflow"),
                description=getattr(d, "description", ""),
                tags=tuple(getattr(d, "tags", []) or []),
                integrated_runtimes=tuple(getattr(d, "integrated_runtimes", []) or []),
                step_count=step_count,
                status=self._status_for(wid),
            ))
        return tuple(views)

    def dependencies(self) -> Tuple[WorkflowDependencyGraph, ...]:
        graphs: List[WorkflowDependencyGraph] = []
        for d in self._descriptors():
            wid = getattr(d, "id", getattr(d, "workflow_id", "unknown"))
            steps = getattr(d, "steps", None)
            step_defs: List[WorkflowStepDependency] = []
            if steps:
                for idx, s in enumerate(steps):
                    step_defs.append(WorkflowStepDependency(
                        workflow_id=wid,
                        step_id=getattr(s, "step_id", "step{0}".format(idx)),
                        step_order=getattr(s, "order", idx),
                        kind=getattr(s, "kind", "compose"),
                        depends_on=tuple(getattr(s, "depends_on", []) or []),
                    ))
            graphs.append(WorkflowDependencyGraph(workflow_id=wid, steps=tuple(step_defs)))
        return tuple(graphs)

    def bottlenecks(self) -> WorkflowBottleneckView:
        """Deteksi bottleneck: step dengan dependensi terbanyak per workflow."""
        found: List[Bottleneck] = []
        for g in self.dependencies():
            if not g.steps:
                continue
            # step yang paling banyak dijadikan dependency (fan-in terbesar)
            fan_in: dict = {}
            for s in g.steps:
                for dep in s.depends_on:
                    fan_in[dep] = fan_in.get(dep, 0) + 1
            if fan_in:
                bottleneck_step = max(fan_in, key=fan_in.get)
                found.append(Bottleneck(
                    workflow_id=g.workflow_id,
                    step_id=bottleneck_step,
                    reason="most-depended-on step (fan-in)",
                    metric=fan_in[bottleneck_step],
                ))
        return WorkflowBottleneckView(bottlenecks=tuple(found))

    def report(self) -> WorkflowIntelligenceReport:
        return WorkflowIntelligenceReport(
            total_workflows=len(self.workflows()),
            workflows=self.workflows(),
            dependencies=self.dependencies(),
            bottlenecks=self.bottlenecks(),
        )

    # ── helper ──
    def _status_for(self, workflow_id: str) -> str:
        if self._workflow_registry is not None:
            try:
                if self._workflow_registry.exists(workflow_id):
                    return "active"
            except Exception:
                return "registered"
        return "registered"

    def _publication_for(self, runtime_id: str):
        if self._pub_registry is None:
            return None
        try:
            for pub in self._pub_registry.observe_all().publications:
                if pub.runtime_id == runtime_id:
                    return pub
        except Exception:
            return None
        return None
