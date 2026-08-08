# Runtime Dependency Graph - WP-03
# IP-3.2-001 (AO-3.2-001 / ED-3.2-001)
#
# Grafik dependensi komponen runtime (DAG). Murni baca: tidak menyelesaikan
# dependensi, tidak memulai/menghentikan komponen, tidak mengubah lifecycle.
# Berguna untuk menanyakan: siapa dependensi X? apakah X punya dependensi yang
# gagal/degraded? siklus ketergantungan?

from typing import Dict, List, Optional, Set, Tuple

from sam.autonomy_runtime.observation.models import ComponentState, RuntimeState


class DependencyGraph:
    """Representasi dependensi antar komponen (murni deklaratif / read-only)."""

    def __init__(self, components: Optional[Dict[str, Set[str]]] = None):
        # node -> set dependensi (node yang HARUS ready dulu)
        self._edges: Dict[str, Set[str]] = {}
        for node, deps in (components or {}).items():
            self.add(node, deps)

    def add(self, node: str, dependencies: Set[str]) -> None:
        if node not in self._edges:
            self._edges[node] = set()
        self._edges[node].update(dependencies)

    def nodes(self) -> List[str]:
        return sorted(self._edges.keys())

    def dependencies_of(self, node: str) -> List[str]:
        """Dependensi langsung node (prasyarat node)."""
        return sorted(self._edges.get(node, set()))

    def dependents_of(self, node: str) -> List[str]:
        """Node yang bergantung (mengconsum) node."""
        return sorted(
            n for n, deps in self._edges.items() if node in deps
        )

    def transitive_dependencies(self, node: str) -> Set[str]:
        """Seluruh dependensi (langsung + tidak langsung)."""
        seen: Set[str] = set()
        stack = list(self._edges.get(node, set()))
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(self._edges.get(cur, set()))
        return seen

    def has_cycle(self) -> bool:
        """Deteksi siklus dependensi (harusnya tidak ada utk DAG runtime)."""

        state: Dict[str, int] = {}  # 0=unvisited,1=in-progress,2=done

        def visit(node: str) -> bool:
            st = state.get(node, 0)
            if st == 1:
                return True  # cycle
            if st == 2:
                return False
            state[node] = 1
            for dep in self._edges.get(node, set()):
                if visit(dep):
                    return True
            state[node] = 2
            return False

        for node in self._edges:
            if visit(node):
                return True
        return False

    # --- Konsolidasi dengan state observasi (agar health-aware) ---

    def unresolved_dependencies(
        self, state: RuntimeState, node: str
    ) -> List[str]:
        """Dependensi node yang tidak ready atau berstatus error/degraded."""
        by_name = {c.name: c for c in state.components}
        result: List[str] = []
        for dep in self._edges.get(node, set()):
            comp = by_name.get(dep)
            if comp is None:
                result.append(dep)
                continue
            if not comp.ready or comp.status in ("error", "degraded"):
                result.append(dep)
        return sorted(result)

    def root_failures(self, state: RuntimeState) -> List[str]:
        """Komponen error yang tidak bergantung pada komponen error lain
        (akar penyebab kandidat di level dependensi)."""
        by_name = {c.name: c for c in state.components}
        errored = [c.name for c in state.components if c.status == "error"]
        roots: List[str] = []
        for name in errored:
            deps = self._edges.get(name, set())
            depends_on_error = any(d in errored for d in deps)
            if not depends_on_error:
                roots.append(name)
        return sorted(roots)
