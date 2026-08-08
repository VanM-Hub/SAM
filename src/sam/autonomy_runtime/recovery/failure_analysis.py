# Failure Analysis Engine - WP-22
# IP-3.2-003 (AO-3.2-001 / ED-3.2-003)
#
# Analisis deterministik terhadap failure dari diagnostics (IP-3.2-001).
# Mengonsumsi FailureClassification + RecoveryContext; TIDAK memodifikasi
# keduanya. Output: FailureAnalysis (immutable) - penjelasan penyebab,
# tingkat keparahan, dan keterkaitan dependency.
# Prinsip: "Recover by strategy, never by authority."

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.recovery.models import RecoveryContext

# Tingkat keparahan kegagalan: lebih tinggi = lebih parah
_SEVERITY_RANK = {
    "dependency_failure": 2,
    "configuration_error": 2,
    "connectivity_failure": 2,
    "resource_exhaustion": 2,
    "unavailable": 3,
    "unknown": 1,
    "none": 0,
}


def _pure_severity(cls: str, status: str) -> int:
    """Menghitung keparahan dari klasifikasi & status, tanpa efek samping."""
    base = _SEVERITY_RANK.get(cls, 1)
    if status in ("error", "unhealthy", "unavailable", "down"):
        base = max(base, 3)
    return base


@dataclass(frozen=True)
class ComponentFailure:
    """Analisis satu komponen yang gagal."""

    component: str
    failure_class: str  # dari taxonomy diagnostics (FailureClass)
    status: str  # unhealthy | degraded | unavailable | unknown
    severity: int
    reason: str  # penjelasan deterministik
    evidence_refs: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "failure_class": self.failure_class,
            "status": self.status,
            "severity": self.severity,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class FailureAnalysis:
    """Hasil analisis kegagalan - immutable, proposal-only, read-only."""

    state_id: str
    analysis_id: str
    overall_severity: int
    failures: Tuple[ComponentFailure, ...] = ()
    affected_components: Tuple[str, ...] = ()
    root_candidates: Tuple[str, ...] = ()
    related_failures: Tuple[Tuple[str, ...], ...] = ()  # group komponen saling terkait
    basis: str = ""  # deskripsi analisis
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "analysis_id": self.analysis_id,
            "overall_severity": self.overall_severity,
            "failures": [f.as_dict() for f in self.failures],
            "affected_components": list(self.affected_components),
            "root_candidates": list(self.root_candidates),
            "related_failures": [list(g) for g in self.related_failures],
            "basis": self.basis,
            "metadata": dict(self.metadata),
        }

    def failure_count(self) -> int:
        return len(self.failures)


class FailureAnalyzer:
    """Menganalisis kegagalan dari klasifikasi diagnostics + recovery context.

    Deterministik: konsumsi FailureClassification (state, komponen->failure
    class) dan RecoveryContext, lalu bangun FailureAnalysis. Tidak mengubah
    input apa pun, tidak mengusulkan aksi - hanya analisis.
    """

    def analyze(
        self,
        failure_classification,
        context: RecoveryContext,
        analysis_id: str = "",
        created_at: str = "",
    ) -> FailureAnalysis:
        """Membangun FailureAnalysis dari klasifikasi & context (read-only)."""
        comp_failures: List[ComponentFailure] = []
        affected: set = set()

        classifications = getattr(failure_classification, "classifications", {}) or {}
        state_id = getattr(failure_classification, "state_id", None) or context.state_id

        status_by_comp: Dict[str, str] = {}
        for comp in context.failed_components:
            status_by_comp[comp] = "unavailable"
        for comp in context.degraded_components:
            status_by_comp[comp] = "degraded"

        for comp, failure_cls in classifications.items():
            if failure_cls in ("none", None):
                continue
            status = status_by_comp.get(comp, "unknown")
            severity = _pure_severity(failure_cls, status)
            reason = self._reason(comp, failure_cls, status, context)
            comp_failures.append(
                ComponentFailure(
                    component=comp,
                    failure_class=failure_cls,
                    status=status,
                    severity=severity,
                    reason=reason,
                    evidence_refs=(failure_cls,),
                )
            )
            affected.add(comp)

        # komponen gagal di context namun tak terklasifikasi -> jadikan unknown
        for comp in context.failed_components:
            if comp in classifications:
                continue
            status = "unavailable"
            comp_failures.append(
                ComponentFailure(
                    component=comp,
                    failure_class="unknown",
                    status=status,
                    severity=_pure_severity("unknown", status),
                    reason="{} failed; cause not classified by diagnostics".format(comp),
                )
            )
            affected.add(comp)

        # stabilkan urutan: severity turun, lalu nama naik
        comp_failures.sort(key=lambda f: (-f.severity, f.component))
        overall = _overall_severity(comp_failures)

        root_candidates, related = self._dependency_insights(context)

        analysis_id = analysis_id or self._stable_id(state_id)
        return FailureAnalysis(
            state_id=state_id,
            analysis_id=analysis_id,
            overall_severity=overall,
            failures=tuple(comp_failures),
            affected_components=tuple(sorted(affected)),
            root_candidates=root_candidates,
            related_failures=related,
            basis="Analyzed {} failure(s) for state {}; proposal only, no action".format(
                len(comp_failures), state_id
            ),
            metadata={"deterministic": True},
        )

    def _reason(
        self, comp: str, failure_cls: str, status: str, context: RecoveryContext
    ) -> str:
        # reason berbasis evidence dari taxonomy diagnostics
        base = "{} classified as {}".format(comp, failure_cls)
        return "{} (status {})".format(base, status)

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "fa-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]

    @staticmethod
    def _dependency_insights(
        context: RecoveryContext,
    ) -> "Tuple[Tuple[str, ...], Tuple[Tuple[str, ...], ...]]":
        """Menemukan kandidat akar kegagalan & grup terkait dari dependency.

        Mempertimbangkan komponen gagal DAN degraded sebagai bagian dari
        afeksi - karena komponen degraded bisa menjadi penyebab hilir kegagalan
        (mis. provider degraded membuat gateway gagal). Murni read-only.
        """
        edges = list(context.dependency_edges)
        children = {}  # komponen -> set komponen yang bergantung padanya
        parents = {}  # komponen -> set prerequisite yang harus siap dulu

        for src, dst in edges:
            # (src, dst): dst butuh src siap dulu -> src prereq dari dst
            parents.setdefault(dst, set()).add(src)
            children.setdefault(src, set()).add(dst)

        affected = set(context.failed_components) | set(context.degraded_components)

        root_candidates: set = set()
        related: List[Tuple[str, ...]] = []
        seen: set = set()

        for comp in sorted(affected):
            if comp in seen:
                continue
            group = set([comp])
            # komponen terkait lain yang memiliki jalur dependency dengannya
            frontier = list(children.get(comp, ()))
            while frontier:
                node = frontier.pop()
                if node in affected and node not in group:
                    group.add(node)
                frontier.extend(children.get(node, ()))
            if len(group) > 1:
                related.append(tuple(sorted(group)))
                seen |= group

        for comp in affected:
            # kandidat akar: yang menjadi prereq komponen bermasalah lain
            if any(comp in parents.get(other, ()) for other in affected if other != comp):
                root_candidates.add(comp)
            # kandidat akar: yang bermasalah dan tidak punya prereq bermasalah
            prereq_bad = parents.get(comp, ()) & affected
            if not prereq_bad:
                root_candidates.add(comp)

        return tuple(sorted(root_candidates)), tuple(dict.fromkeys(related))


def _overall_severity(failures: List[ComponentFailure]) -> int:
    """Keparahan menyeluruh = keparahan tertinggi (bukan rata-rata)."""
    if not failures:
        return 0
    return max(f.severity for f in failures)
