# Dependency Planner - WP-13
# IP-3.2-002 (AO-3.2-001 / ED-3.2-002)
#
# Planning berdasarkan dependency graph TANPA mutasi runtime.
# Menghasilkan urutan kerja yang menghormati dependency (prasyarat dulu),
# deteksi ketergantungan yang tidak bisa dipenuhi, dan analisis urutan
# deterministik. Murni read-only terhadap dependency graph.
#
# Prinsip: plan, never decide. Semua output adalah proposal urutan.

from typing import Dict, List, Optional, Set, Tuple

from sam.autonomy_runtime.planning.models import PlanStep, PlanningContext


class DependencyPlanner:
    """Menyusun urutan kerja berdasarkan dependency graph (read-only)."""

    def __init__(self, context: PlanningContext) -> None:
        self._context = context
        self._edges = list(context.dependency_edges)

    # --- query graph (read-only) ---

    def dependencies_of(self, target: str) -> List[str]:
        """Komponen yang harus siap sebelum target (langsung)."""
        return [src for src, dst in self._edges if dst == target]

    def dependents_of(self, target: str) -> List[str]:
        """Komponen yang bergantung pada target (langsung)."""
        return [dst for src, dst in self._edges if src == target]

    def transitive_dependencies(self, target: str) -> Set[str]:
        """SEMUA komponen yang harus siap sebelum target (transitif)."""
        result: Set[str] = set()
        stack = list(self.dependencies_of(target))
        seen: Set[str] = set()
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            result.add(cur)
            for dep in self.dependencies_of(cur):
                if dep not in seen:
                    stack.append(dep)
        return result

    def has_cycle(self) -> bool:
        """Deteksi siklus pada dependency graph (deterministik)."""
        WHITE: int = 0
        GRAY: int = 1
        BLACK: int = 2
        color: Dict[str, int] = {}
        for src, dst in self._edges:
            color.setdefault(src, WHITE)
            color.setdefault(dst, WHITE)
        order = [n for n in color]

        def visit(node: str, color: Dict[str, int]) -> bool:
            color[node] = GRAY
            for dep in self.dependencies_of(node):
                if color.get(dep, WHITE) == GRAY:
                    return True
                if color.get(dep, WHITE) == WHITE:
                    if visit(dep, color):
                        return True
            color[node] = BLACK
            return False

        for node in order:
            if color[node] == WHITE:
                if visit(node, color):
                    return True
        return False

    # --- planning ---

    def dependency_ordered_steps(self, steps: Tuple[PlanStep, ...]) -> Tuple[PlanStep, ...]:
        """Urutkan langkah agar menghormati dependency: dependensi dulu.

        Langkah yang ber-targat dependency utama diusulkan sebelum dependents.
        Deterministik: topological-ish sort dengan tie-break step_id.
        """
        if self.has_cycle():
            # bila ada siklus, tetap urutkan deterministik (priority, step_id)
            return tuple(sorted(steps, key=lambda s: (-s.priority, s.step_id)))
        step_by_target: Dict[str, PlanStep] = {s.target: s for s in steps}
        placed: List[str] = []
        seen: Set[str] = set()

        def place(target: str) -> None:
            if target in seen:
                return
            seen.add(target)
            for dep in self.dependencies_of(target):
                if dep in step_by_target and dep not in seen:
                    place(dep)
            if target in step_by_target:
                placed.append(target)

        for step in sorted(steps, key=lambda s: s.step_id):
            place(step.target)
        ordered = [step_by_target[t] for t in placed]
        return tuple(ordered)

    def unavailable_dependencies(self) -> List[str]:
        """Komponen yang jadi prasyarat tapi tidak tersedia (blocker)."""
        blockers: List[str] = []
        for src, dst in self._edges:
            if src in self._context.unavailable_components:
                if src not in blockers:
                    blockers.append(src)
        return blockers

    def dependency_gate_summary(self, target: str) -> str:
        """Ringkasan jelas prasyarat target (untuk explainability WP-18)."""
        deps = self.dependencies_of(target)
        if not deps:
            return "{} has no direct dependency".format(target)
        return "{} depends on: {}".format(target, ", ".join(deps))
